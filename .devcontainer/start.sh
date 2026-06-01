#!/bin/bash
# Codespace 启动脚本

echo "正在安装依赖..."
pip install -r requirements.txt

echo "启动 Streamlit 应用..."
streamlit run views/app.py --server.headless true --server.port 8501 --server.address 0.0.0.0
