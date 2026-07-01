# -*- coding: utf-8 -*-
"""
ALPHA DESK 视觉主题 —— 极简白·高端简洁(机构路演级)。
统一注入全局CSS(字体/配色/卡片/表格/tab/按钮)+ 品牌头。所有页面共用。
配色:纯白底 + 浅灰卡片 + 深靛蓝主色 #2547E6 + 克制涨绿跌红。字体:Inter。
"""
import streamlit as st

BRAND = "ALPHA DESK"
TAGLINE = "全球AI产业链 · 研究与持仓"

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root{
  --bg:#FFFFFF; --panel:#F6F8FB; --card:#FFFFFF; --ink:#141A2A; --muted:#6B7280;
  --line:#E7EAF1; --brand:#2547E6; --brand-2:#5B7BFF; --brand-soft:#EDF1FF;
  --up:#0E9F6E; --down:#E02424; --gold:#C9A96A;
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

/* 标题 */
h1,h2,h3,h4{ color:var(--ink); font-weight:700; letter-spacing:-0.01em; }
h3{ font-size:1.06rem; margin-top:0.5rem; }
[data-testid="stCaptionContainer"], .stCaption, small{ color:var(--muted) !important; }

/* 品牌头 */
.ad-header{ display:flex; align-items:center; justify-content:space-between;
  padding:2px 2px 14px; border-bottom:1px solid var(--line); margin-bottom:12px; }
.ad-brand{ display:flex; align-items:center; gap:13px; }
.ad-mark{ width:36px; height:36px; border-radius:10px; font-size:16px;
  background:linear-gradient(135deg,var(--brand),var(--brand-2));
  display:flex; align-items:center; justify-content:center; color:#fff; font-weight:800;
  box-shadow:0 6px 16px rgba(37,71,230,.28); }
.ad-name{ font-size:1.34rem; font-weight:800; letter-spacing:0.15em; color:var(--ink); line-height:1; }
.ad-tag{ font-size:0.72rem; color:var(--muted); letter-spacing:0.05em; margin-top:5px; }
.ad-meta{ text-align:right; font-size:0.72rem; color:var(--muted); line-height:1.5; }
.ad-live{ display:inline-flex; align-items:center; gap:6px; color:var(--up); font-weight:700; }
.ad-dot{ width:7px; height:7px; border-radius:50%; background:var(--up);
  box-shadow:0 0 0 3px rgba(14,159,110,.16); }

/* Tabs 分段控件 */
.stTabs [data-baseweb="tab-list"]{ gap:2px; border-bottom:1px solid var(--line); }
.stTabs [data-baseweb="tab"]{ height:42px; padding:0 14px; background:transparent;
  font-weight:600; font-size:0.9rem; color:var(--muted); border-radius:9px 9px 0 0; }
.stTabs [data-baseweb="tab"]:hover{ color:var(--ink); background:var(--panel); }
.stTabs [aria-selected="true"]{ color:var(--brand) !important; }
.stTabs [data-baseweb="tab-highlight"]{ background:var(--brand); height:2.5px; }

/* Metric 卡片 */
[data-testid="stMetric"]{ background:var(--card); border:1px solid var(--line);
  border-radius:14px; padding:14px 16px 12px; box-shadow:0 1px 2px rgba(16,24,40,.04); }
[data-testid="stMetricLabel"]{ color:var(--muted); font-weight:600; }
[data-testid="stMetricValue"]{ font-weight:800; letter-spacing:-0.02em; }

/* 表格 */
[data-testid="stDataFrame"], [data-testid="stTable"]{
  border:1px solid var(--line); border-radius:12px; overflow:hidden; }

/* 按钮 */
.stButton>button{ background:var(--brand); color:#fff; border:0; border-radius:10px;
  font-weight:600; padding:0.45rem 1.1rem; transition:background .15s; }
.stButton>button:hover{ background:#1c39c4; color:#fff; }
.stButton>button:active{ background:#162fa0; }

/* Expander / 输入 / 提示框 */
[data-testid="stExpander"]{ border:1px solid var(--line); border-radius:12px; background:var(--card); }
[data-testid="stAlert"]{ border-radius:12px; border:1px solid var(--line); }
.stTextInput input, .stNumberInput input{ border-radius:10px; }
[data-baseweb="tab-border"]{ background:transparent; }
</style>
"""


def inject():
    """注入全局主题。set_page_config 之后、任何内容之前调用一次。"""
    st.markdown(_CSS, unsafe_allow_html=True)


def header(subtitle=None, meta_right=None):
    """品牌头。subtitle 覆盖默认副标题;meta_right 显示在右侧(如日期)。"""
    tag = subtitle or TAGLINE
    right = ""
    if meta_right:
        right = (f'<div class="ad-meta"><div class="ad-live"><span class="ad-dot"></span>'
                 f'LIVE</div><div>{meta_right}</div></div>')
    st.markdown(
        f'<div class="ad-header"><div class="ad-brand">'
        f'<div class="ad-mark">◆</div>'
        f'<div><div class="ad-name">{BRAND}</div><div class="ad-tag">{tag}</div></div>'
        f'</div>{right}</div>',
        unsafe_allow_html=True)
