# -*- coding: utf-8 -*-
"""
AlphaDesk 保活守护 —— 让她彻底省心:
1) 本地 App(8501)挂了 → 自动拉起
2) 隧道挂了 → 自动重开;新链接自动发她微信(Server酱)
3) 每天开机/每10分钟由 Windows 计划任务静默执行,无窗口、无打扰
"""
import os
import re
import json
import time
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
ST = os.path.join(BASE, ".venv", "Scripts", "streamlit.exe")
CF = (r"C:\Users\xiaoy\AppData\Local\Microsoft\WinGet\Packages"
      r"\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe")
URL_FILE = os.path.join(BASE, "tunnel_url.txt")
CF_LOG = os.path.join(os.environ.get("TEMP", BASE), "cf_keepalive.log")

import requests

def _ok(url, t=8):
    try:
        return requests.get(url, timeout=t).status_code == 200
    except Exception:
        return False


# Cloudflare anycast边缘IP:trycloudflare按SNI路由,任一边缘IP都可达任一隧道。
# 用固定IP探活=完全绕开DNS(她的VPN DNS对新子域NXDOMAIN、连1.1.1.1都会flap)。
_CF_EDGE_IPS = ("104.16.230.132", "104.16.231.132")


def _tunnel_ok(url, t=12):
    """判隧道死活,对DNS故障完全免疫:直连失败→固定边缘IP+SNI探活。
    隧道真死时边缘返回530(Argo Tunnel error),不是200,不会误判。
    防止"隧道活着但DNS没跟上"被误判成死→反复轮换刷微信。"""
    if _ok(url + "/healthz", t=t):
        return True
    host = url.split("//", 1)[1].strip("/")
    for ip in _CF_EDGE_IPS:
        try:
            out = subprocess.run(["curl", "-s", "-m", str(t), "-o", "NUL",
                                  "-w", "%{http_code}", "--resolve",
                                  "%s:443:%s" % (host, ip), url + "/healthz"],
                                 capture_output=True, text=True, timeout=t + 18)
            if out.stdout.strip() == "200":
                return True
        except Exception:
            pass
    return False


def _lan_ip():
    try:
        import socket
        s = socket.socket(socket.SOCK_DGRAM.__class__ and 2, 2)  # AF_INET, SOCK_DGRAM
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def _wechat(title, desp):
    try:
        key = json.load(open(os.path.join(BASE, "server_chan.json"), encoding="utf-8"))["key"]
        requests.post(f"https://sctapi.ftqq.com/{key}.send",
                      data={"title": title, "desp": desp}, timeout=15)
    except Exception:
        pass


def _pids_8501():
    """列出所有监听8501的PID。双开=手机随机连到旧代码(logo/页面不一致的元凶)。"""
    try:
        out = subprocess.check_output(["netstat", "-ano"], text=True, errors="ignore")
    except Exception:
        return []
    pids = set()
    for ln in out.splitlines():
        if ":8501" in ln and "LISTENING" in ln:
            parts = ln.split()
            if parts and parts[-1].isdigit():
                pids.add(parts[-1])
    return sorted(pids)


def ensure_app():
    pids = _pids_8501()
    if len(pids) > 1:  # 双开:全杀,下面重启一个干净的
        for p in pids:
            subprocess.run(["taskkill", "/F", "/PID", p],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
    elif _ok("http://localhost:8501/healthz"):
        return True
    # 拉起 streamlit(无窗口)
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    subprocess.Popen([ST, "run", os.path.join(BASE, "app.py"),
                      "--server.port", "8501", "--server.headless", "true",
                      "--server.address", "0.0.0.0"],
                     startupinfo=si, cwd=BASE,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(15):
        time.sleep(2)
        if _ok("http://localhost:8501/healthz"):
            return True
    return False


def ensure_tunnel():
    old = ""
    if os.path.exists(URL_FILE):
        old = open(URL_FILE, encoding="utf-8").read().strip()
    if old and _tunnel_ok(old, t=12):
        return old, False  # 还活着,没变
    # 重开隧道
    subprocess.run(["taskkill", "/IM", "cloudflared.exe", "/F"],
                   capture_output=True)
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    with open(CF_LOG, "w") as f:
        subprocess.Popen([CF, "tunnel", "--url", "http://localhost:8501",
                          "--protocol", "http2"],
                         startupinfo=si, stdout=f, stderr=subprocess.STDOUT)
    url = ""
    for _ in range(30):
        time.sleep(2)
        try:
            # 排除 api.trycloudflare.com(cloudflared自家API,2026-07-05曾被误发布成入口)
            m = re.search(r"https://(?!api\.)[a-z0-9-]+\.trycloudflare\.com",
                          open(CF_LOG, errors="ignore").read())
            if m:
                url = m.group(0)
                break
        except Exception:
            pass
    if url:
        # 新trycloudflare域名DNS生效可能要1-2分钟,耐心等;
        # 即便等不到也照样发布——新链接迟早通,死链接永远死(2026-07-05修:上一版15秒就放弃导致固定网址挂死链)
        for _ in range(12):
            if _tunnel_ok(url, t=10):
                break
            time.sleep(5)
        open(URL_FILE, "w", encoding="utf-8").write(url)
        return url, True  # 新链接
    return old, False


def _update_pages(url):
    """改写 docs/index.html 的跳转目标并 git push → 固定网址 dorkiditas.github.io/stockapp 永远指向活入口。"""
    try:
        p = os.path.join(BASE, "docs", "index.html")
        html = open(p, encoding="utf-8").read()
        html = re.sub(r"https://[a-z0-9-]+\.trycloudflare\.com", url, html)
        open(p, "w", encoding="utf-8").write(html)
        for cmd in (["git", "add", "docs/index.html"],
                    ["git", "-c", "user.email=xiaoyi.d.lei@gmail.com",
                     "-c", "user.name=dorkiditas", "commit", "-m", "keepalive: rotate tunnel url"],
                    ["git", "push", "origin", "main"]):
            subprocess.run(cmd, cwd=BASE, capture_output=True, timeout=60)
    except Exception:
        pass


def main():
    app_up = ensure_app()
    url, changed = ensure_tunnel() if app_up else ("", False)
    # 自愈:入口页指向与实际隧道分叉时(如有人手动开过隧道),即使本轮没轮换也纠正
    if url and not changed:
        try:
            html = open(os.path.join(BASE, "docs", "index.html"), encoding="utf-8").read()
            if url not in html:
                changed = True
        except Exception:
            pass
    if changed:
        _update_pages(url)
        lan = _lan_ip() or "10.0.66.237"
        _wechat("📱 选股App地址已自动更新",
                f"固定网址(记这个就够):https://dorkiditas.github.io/stockapp\n\n"
                f"家里WiFi:http://{lan}:8501\n\n"
                f"(外网直达:{url})密码不变,点开就能用。")


if __name__ == "__main__":
    main()
