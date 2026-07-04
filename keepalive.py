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


def ensure_app():
    if _ok("http://localhost:8501/healthz"):
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
    if old and _ok(old + "/healthz", t=12):
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
    for _ in range(20):
        time.sleep(2)
        try:
            m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com",
                          open(CF_LOG, errors="ignore").read())
            if m:
                url = m.group(0)
                break
        except Exception:
            pass
    if url and _ok(url + "/healthz", t=15):
        open(URL_FILE, "w", encoding="utf-8").write(url)
        return url, True  # 新链接
    return old, False


def main():
    app_up = ensure_app()
    url, changed = ensure_tunnel() if app_up else ("", False)
    if changed:
        lan = _lan_ip() or "10.0.66.237"
        _wechat("📱 选股App新地址(自动更新)",
                f"外网新链接:{url}\n\n"
                f"家里WiFi固定地址:http://{lan}:8501\n\n"
                f"密码不变。旧链接作废,不用管为什么,点开就能用。")


if __name__ == "__main__":
    main()
