import pathlib

import streamlit as st

st.set_page_config(page_title="周报 · Alpha Desk", page_icon="📋", layout="wide")

st.title("📋 Alpha Desk 周报")
st.caption("每周日晚更新 · 完整版归档 · 微信推送为摘要版")

REPORT_DIR = pathlib.Path(__file__).resolve().parent.parent / "reports"
REPORT_DIR.mkdir(exist_ok=True)

files = sorted(REPORT_DIR.glob("*.md"), reverse=True)

if not files:
    st.info("暂无周报。第一期将于本周日生成。")
else:
    names = [f.stem for f in files]
    sel = st.selectbox("期数", names, index=0)
    path = REPORT_DIR / f"{sel}.md"
    st.divider()
    # escape $ so Streamlit doesn't render dollar amounts as LaTeX math
    st.markdown(path.read_text(encoding="utf-8").replace("$", "\\$"))
    st.divider()
    st.download_button(
        "下载本期 (Markdown)",
        data=path.read_text(encoding="utf-8"),
        file_name=f"{sel}.md",
        mime="text/markdown",
    )
