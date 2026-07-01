# -*- coding: utf-8 -*-
"""
ALPHA DESK 视觉主题 —— Claude/Anthropic 暖色编辑风(高级有温度)。
米白纸感底 + 珊瑚陶土主色 + 衬线标题(Newsreader) + 无衬线正文(Inter)。
克制、留白、圆角、柔阴影;涨绿跌红保持清晰。所有页面共用。
"""
import streamlit as st

BRAND = "Alpha Desk"
TAGLINE = "全球AI产业链 · 研究与持仓"

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600;6..72,700&family=Inter:wght@400;500;600;700&display=swap');
:root{
  --bg:#F4F3EE;          /* 米白纸感底 */
  --panel:#EEEBE2;       /* 暖浅灰面板 */
  --card:#FBFAF6;        /* 卡片(近白暖) */
  --ink:#1F1E1B;         /* 暖近黑 */
  --muted:#6E6A5F;       /* 暖灰 */
  --line:#E4E0D4;        /* 暖描边 */
  --brand:#C96442;       /* 珊瑚陶土(Claude clay) */
  --brand-2:#D97757;     /* 亮一档 */
  --brand-soft:#F3E6DE;  /* 淡陶土底 */
  --up:#3F7D57; --down:#BC4B3C; --gold:#C9A96A;
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
a, a:visited{ color:var(--brand); }

/* 数字用等宽表格数字,更整齐 */
[data-testid="stMetricValue"], [data-testid="stDataFrame"]{ font-variant-numeric:tabular-nums; }

/* 品牌头 */
.ad-header{ display:flex; align-items:center; justify-content:space-between;
  padding:2px 2px 16px; border-bottom:1px solid var(--line); margin-bottom:14px; }
.ad-brand{ display:flex; align-items:center; gap:14px; }
.ad-mark{ width:38px; height:38px; border-radius:11px; font-size:18px;
  background:linear-gradient(135deg,var(--brand),var(--brand-2));
  display:flex; align-items:center; justify-content:center; color:#FBFAF6; font-weight:700;
  box-shadow:0 6px 18px rgba(201,100,66,.26); }
.ad-name{ font-family:'Newsreader',Georgia,serif; font-size:1.6rem; font-weight:600;
  letter-spacing:0.01em; color:var(--ink); line-height:1; }
.ad-tag{ font-size:0.74rem; color:var(--muted); letter-spacing:0.03em; margin-top:6px; }
.ad-meta{ text-align:right; font-size:0.72rem; color:var(--muted); line-height:1.6; }
.ad-live{ display:inline-flex; align-items:center; gap:6px; color:var(--up); font-weight:600; }
.ad-dot{ width:7px; height:7px; border-radius:50%; background:var(--up);
  box-shadow:0 0 0 3px rgba(63,125,87,.16); }

/* Tabs 分段控件 */
.stTabs [data-baseweb="tab-list"]{ gap:2px; border-bottom:1px solid var(--line); }
.stTabs [data-baseweb="tab"]{ height:42px; padding:0 14px; background:transparent;
  font-weight:600; font-size:0.9rem; color:var(--muted); border-radius:10px 10px 0 0; }
.stTabs [data-baseweb="tab"]:hover{ color:var(--ink); background:var(--panel); }
.stTabs [aria-selected="true"]{ color:var(--brand) !important; }
.stTabs [data-baseweb="tab-highlight"]{ background:var(--brand); height:2.5px; }

/* Metric 卡片 */
[data-testid="stMetric"]{ background:var(--card); border:1px solid var(--line);
  border-radius:16px; padding:15px 17px 13px; box-shadow:0 1px 2px rgba(31,30,27,.04); }
[data-testid="stMetricLabel"]{ color:var(--muted); font-weight:600; }
[data-testid="stMetricValue"]{ font-weight:700; letter-spacing:-0.02em; }

/* 表格 */
[data-testid="stDataFrame"], [data-testid="stTable"]{
  border:1px solid var(--line); border-radius:14px; overflow:hidden; }

/* 按钮 */
.stButton>button{ background:var(--brand); color:#FBFAF6; border:0; border-radius:11px;
  font-weight:600; padding:0.45rem 1.1rem; transition:background .15s; }
.stButton>button:hover{ background:#b5583a; color:#FBFAF6; }
.stButton>button:active{ background:#9c4a30; }

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


def header(subtitle=None, meta_right=None):
    """品牌头。subtitle 覆盖默认副标题;meta_right 显示在右侧(如日期)。"""
    tag = subtitle or TAGLINE
    right = ""
    if meta_right:
        right = (f'<div class="ad-meta"><div class="ad-live"><span class="ad-dot"></span>'
                 f'LIVE</div><div>{meta_right}</div></div>')
    st.markdown(
        f'<div class="ad-header"><div class="ad-brand">'
        f'<div class="ad-mark">✳</div>'
        f'<div><div class="ad-name">{BRAND}</div><div class="ad-tag">{tag}</div></div>'
        f'</div>{right}</div>',
        unsafe_allow_html=True)
