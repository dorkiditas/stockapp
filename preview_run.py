# -*- coding: utf-8 -*-
"""Claude Preview 启动器:读 PORT 环境变量起 streamlit,避免与常驻隧道(8501)抢端口。"""
import os
import sys
import subprocess

here = os.path.dirname(os.path.abspath(__file__))
port = os.environ.get("PORT", "8502")
exe = os.path.join(here, ".venv", "Scripts", "streamlit.exe")
sys.exit(subprocess.call([exe, "run", os.path.join(here, "app.py"),
                          "--server.port", port, "--server.headless", "true"]))
