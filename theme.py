# -*- coding: utf-8 -*-
"""
ALPHA DESK 视觉主题 —— 墨绿×金 高级私人财富风(她的专属identity)。
配色:柔软象牙底 + 深祖母绿主色 + 克制金点缀。字体:Newsreader衬线标题 + Inter正文。
Logo:手绘SVG α 字标(alpha=超额收益,基金灵魂;非套用任何现成符号)。
克制、留白、圆角、柔阴影;涨绿跌红保持清晰。所有页面共用。
"""
import streamlit as st

BRAND = "Alpha Desk"
TAGLINE = "全球AI产业链 · 研究与持仓"

# 手绘 α 字标(深绿渐变瓷砖 + 金色内框 + 象牙 α),纯SVG,可无限缩放不失真
LOGO_SVG = """
<svg width="40" height="40" viewBox="0 0 40 40" fill="none" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="adg" x1="2" y1="2" x2="38" y2="38" gradientUnits="userSpaceOnUse">
      <stop stop-color="#1E7A56"/><stop offset="1" stop-color="#0E3A29"/>
    </linearGradient>
  </defs>
  <rect x="0.5" y="0.5" width="39" height="39" rx="11" fill="url(#adg)"/>
  <rect x="3.2" y="3.2" width="33.6" height="33.6" rx="8.6" fill="none"
        stroke="#C2A46A" stroke-opacity="0.55" stroke-width="1"/>
  <text x="20" y="28.5" text-anchor="middle" font-family="Georgia,'Newsreader',serif"
        font-style="italic" font-weight="500" font-size="23" fill="#F4F1E7">&#945;</text>
</svg>
"""

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600;6..72,700&family=Inter:wght@400;500;600;700&display=swap');
:root{
  --bg:#F3F5EF;          /* 柔软象牙(微绿) */
  --panel:#EAEEE4;       /* 浅绿灰面板 */
  --card:#FBFCF8;        /* 卡片(近白) */
  --ink:#14201A;         /* 深绿近黑 */
  --muted:#68706A;       /* 绿灰 */
  --line:#E0E5DB;        /* 描边 */
  --brand:#17513A;       /* 深祖母绿(标题/字标) */
  --brand-2:#1E7A56;     /* 交互祖母绿(按钮/tab/链接) */
  --brand-soft:#E6EFE8;  /* 淡绿底 */
  --gold:#B99150;        /* 克制金 */
  --up:#1E7A56; --down:#BC4B3C;
}
html, body, .stApp, [class*="css"]{
  font-family:'Inter','PingFang SC','Microsoft YaHei',-apple-system,sans-serif;
}
.stApp{ background:var(--bg); color:var(--ink); }

/* 隐藏 Streamlit 自带装饰,路演更干净 */
[data-testid="stToolbar"], [data-testid="stDecoration"], #MainMenu, footer,
[data-testid="stStatusWidget"]{ display:none !important; }
[data-testid="stHeader"]{ background:transparent; height:0; }

/* 版心 */
.block-container{ padding-top:1.1rem !important; padding-bottom:3rem; max-width:1320px; }

/* 标题:衬线,编辑感 */
h1,h2,h3,h4{ font-family:'Newsreader',Georgia,serif !important;
  color:var(--ink); font-weight:600; letter-spacing:-0.005em; }
h2{ font-size:1.5rem; }
h3{ font-size:1.2rem; margin-top:0.5rem; }
[data-testid="stCaptionContainer"], .stCaption, small{ color:var(--muted) !important; }
a, a:visited{ color:var(--brand-2); }

/* 数字用等宽表格数字,更整齐 */
[data-testid="stMetricValue"], [data-testid="stDataFrame"]{ font-variant-numeric:tabular-nums; }

/* 品牌头 */
.ad-header{ display:flex; align-items:center; justify-content:space-between;
  padding:2px 2px 16px; border-bottom:1px solid var(--line); margin-bottom:14px; }
.ad-brand{ display:flex; align-items:center; gap:14px; }
.ad-mark{ width:40px; height:40px; line-height:0;
  filter:drop-shadow(0 6px 16px rgba(23,81,58,.26)); }
.ad-name{ font-family:'Newsreader',Georgia,serif; font-size:1.62rem; font-weight:600;
  letter-spacing:0.01em; color:var(--brand); line-height:1; }
.ad-tag{ font-size:0.74rem; color:var(--muted); letter-spacing:0.03em; margin-top:6px; }
.ad-meta{ text-align:right; font-size:0.72rem; color:var(--muted); line-height:1.6; }
.ad-live{ display:inline-flex; align-items:center; gap:6px; color:var(--up); font-weight:600; }
.ad-dot{ width:7px; height:7px; border-radius:50%; background:var(--up);
  box-shadow:0 0 0 3px rgba(30,122,86,.16); }

/* Tabs 分段控件 */
.stTabs [data-baseweb="tab-list"]{ gap:2px; border-bottom:1px solid var(--line); }
.stTabs [data-baseweb="tab"]{ height:42px; padding:0 14px; background:transparent;
  font-weight:600; font-size:0.9rem; color:var(--muted); border-radius:10px 10px 0 0; }
.stTabs [data-baseweb="tab"]:hover{ color:var(--ink); background:var(--panel); }
.stTabs [aria-selected="true"]{ color:var(--brand-2) !important; }
.stTabs [data-baseweb="tab-highlight"]{ background:var(--brand-2); height:2.5px; }

/* Metric 卡片 */
[data-testid="stMetric"]{ background:var(--card); border:1px solid var(--line);
  border-radius:16px; padding:15px 17px 13px; box-shadow:0 1px 2px rgba(20,32,26,.04); }
[data-testid="stMetricLabel"]{ color:var(--muted); font-weight:600; }
[data-testid="stMetricValue"]{ font-weight:700; letter-spacing:-0.02em; }

/* 表格 */
[data-testid="stDataFrame"], [data-testid="stTable"]{
  border:1px solid var(--line); border-radius:14px; overflow:hidden; }

/* 按钮 */
.stButton>button{ background:var(--brand-2); color:#FBFCF8; border:0; border-radius:11px;
  font-weight:600; padding:0.45rem 1.1rem; transition:background .15s; }
.stButton>button:hover{ background:#186445; color:#FBFCF8; }
.stButton>button:active{ background:#124e36; }

/* Expander / 输入 / 提示框 */
[data-testid="stExpander"]{ border:1px solid var(--line); border-radius:14px; background:var(--card); }
[data-testid="stAlert"]{ border-radius:14px; border:1px solid var(--line); }
.stTextInput input, .stNumberInput input{ border-radius:11px; }
[data-baseweb="tab-border"]{ background:transparent; }
</style>
"""


def inject():
    """注入全局主题。set_page_config 之后、任何内容之前调用一次。"""
    st.markdown(_CSS, unsafe_allow_html=True)


def inject_appicon():
    """把自绘的 α 图标注入真实页面 <head> 作 apple-touch-icon/favicon,
    让手机'添加到主屏幕'用高级图标,而不是系统瞎生成的灰底首字母。"""
    import os
    import base64
    try:
        from streamlit.components.v1 import html as _html
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon180.png")
        b64 = base64.b64encode(open(p, "rb").read()).decode()
    except Exception:
        return
    _html(
        "<script>(function(){try{"
        "var h=window.parent.document.head;"
        "var u='data:image/png;base64," + b64 + "';"
        "h.querySelectorAll(\"link[rel~='icon'],link[rel^='apple-touch-icon']\")"
        ".forEach(function(e){e.remove();});"
        "[180,152,167,120].forEach(function(s){var l=window.parent.document.createElement('link');"
        "l.rel='apple-touch-icon';l.setAttribute('sizes',s+'x'+s);l.href=u;h.appendChild(l);});"
        "var f=window.parent.document.createElement('link');f.rel='icon';f.type='image/png';f.href=u;h.appendChild(f);"
        "}catch(e){}})();</script>", height=0)


def header(subtitle=None, meta_right=None):
    """品牌头。subtitle 覆盖默认副标题;meta_right 显示在右侧(如日期)。"""
    tag = subtitle or TAGLINE
    right = ""
    if meta_right:
        right = (f'<div class="ad-meta"><div class="ad-live"><span class="ad-dot"></span>'
                 f'LIVE</div><div>{meta_right}</div></div>')
    st.markdown(
        f'<div class="ad-header"><div class="ad-brand">'
        f'<div class="ad-mark">{LOGO_SVG}</div>'
        f'<div><div class="ad-name">{BRAND}</div><div class="ad-tag">{tag}</div></div>'
        f'</div>{right}</div>',
        unsafe_allow_html=True)
