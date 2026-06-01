"""Streamlit 入口 — 路由 & 全局状态管理"""

import sys
import os

# 确保项目根目录在 sys.path（兼容本地和 Codespace 环境）
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st
from controllers.fund_manager import FundManager
from models.fund_db import FundDB
from models.fund_data import get_default_source

# ── 全局单例 ──
@st.cache_resource
def get_manager() -> FundManager:
    db = FundDB()
    source = get_default_source()
    return FundManager(db=db, source=source)


def main():
    st.set_page_config(
        page_title="基金均值交易系统",
        page_icon="📈",
        layout="wide",
    )

    st.sidebar.title("基金均值交易系统")
    st.sidebar.divider()

    page = st.sidebar.radio(
        "导航",
        ["基金管理", "净值图表", "策略配置", "策略回测"],
        key="nav",
    )

    mgr = get_manager()

    if page == "基金管理":
        from views.page_fund import render
        render(mgr)
    elif page == "净值图表":
        from views.page_chart import render
        render(mgr)
    elif page == "策略配置":
        from views.page_strategy import render
        render()
    elif page == "策略回测":
        from views.page_backtest import render
        render(mgr)


if __name__ == "__main__":
    main()
