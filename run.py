"""项目启动脚本"""
import subprocess
import sys
import os

if __name__ == "__main__":
    app_path = os.path.join(os.path.dirname(__file__), "views", "app.py")
    subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])
