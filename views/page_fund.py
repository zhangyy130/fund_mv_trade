"""基金管理页 — 添加、删除、刷新数据"""

import streamlit as st
from datetime import datetime, timedelta
from controllers.fund_manager import FundManager


def render(mgr: FundManager):
    st.header("基金管理")

    # ── 添加基金 ──
    col1, col2 = st.columns([3, 1])
    with col1:
        code = st.text_input("基金代码", placeholder="例如 110011", key="add_fund_code")
    with col2:
        st.write("")
        if st.button("添加", use_container_width=True):
            if code.strip():
                _add_fund(mgr, code.strip())
            else:
                st.warning("请输入基金代码")

    st.divider()

    # ── 基金列表 ──
    st.subheader("已添加的基金")
    funds = mgr.list_funds()

    if funds.empty:
        st.info("暂无基金，请先添加")
        return

    # 注入 CSS：单元格垂直居中 + 按钮 mini
    st.markdown("""
        <style>
        .fund-header p { text-align: center !important; font-weight: bold; margin: 0; line-height: 2.5; }
        .fund-cell { display: flex !important; align-items: center !important; justify-content: center !important; min-height: 50px; }
        .fund-cell p { text-align: center !important; margin: 0; line-height: 50px; }
        div[data-testid="stHorizontalBlock"] button { min-width: 28px !important; padding: 2px 4px !important; font-size: 12px !important; height: 28px !important; }
        </style>
    """, unsafe_allow_html=True)

    # 表头
    h1, h2, h3, h4, h5, h6 = st.columns([1.5, 3, 2, 2.5, 2, 1.2])
    for col, text in [(h1, "代码"), (h2, "名称"), (h3, "基金经理"), (h4, "基金公司"), (h5, "成立时间"), (h6, "操作")]:
        with col:
            st.markdown(f"<div class='fund-header'><p>{text}</p></div>", unsafe_allow_html=True)

    # 数据行
    for _, row in funds.iterrows():
        c1, c2, c3, c4, c5, c6 = st.columns([1.5, 3, 2, 2.5, 2, 1.2])
        with c1:
            st.markdown(f"<div class='fund-cell'><p>{row['code']}</p></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='fund-cell'><p>{row.get('name', '') or ''}</p></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='fund-cell'><p>{row.get('fund_manager', '') or ''}</p></div>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<div class='fund-cell'><p>{row.get('fund_company', '') or ''}</p></div>", unsafe_allow_html=True)
        with c5:
            st.markdown(f"<div class='fund-cell'><p>{row.get('establish_date', '') or ''}</p></div>", unsafe_allow_html=True)
        with c6:
            bc1, bc2 = st.columns([1, 1])
            with bc1:
                if st.button("采集", key=f"fetch_{row['code']}", use_container_width=True):
                    _collect_fund(mgr, row)
            with bc2:
                if st.button("删除", key=f"del_{row['code']}", use_container_width=True):
                    mgr.remove_fund(row["code"])
                    st.rerun()


def _add_fund(mgr: FundManager, code: str):
    """添加新基金并采集数据"""
    end = datetime.now().strftime("%Y-%m-%d")

    with st.spinner(f"正在获取 {code} 的基金信息..."):
        info = mgr.source.fetch_fund_info(code)
        est_date = info.get("establish_date", "")
        start = est_date if est_date else (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    with st.spinner(f"正在采集净值数据（{start} ~ {end}）..."):
        df = mgr.refresh_nav(code, start, end)
        if df.empty:
            st.error("未找到该基金的净值数据，请检查代码")
            return
        mgr.add_fund(code)
        st.success(f"已添加：{info.get('name', code)}，共 {len(df)} 条净值数据")


def _collect_fund(mgr: FundManager, row):
    """为已有基金采集净值数据"""
    code = row["code"]
    end = datetime.now().strftime("%Y-%m-%d")
    start = row.get("establish_date", "") or (datetime.now() - timedelta(days=365)).strftime("%Y-%m-%d")

    with st.spinner(f"正在采集 {code} 净值数据（{start} ~ {end}）..."):
        df = mgr.refresh_nav(code, start, end)
        if df.empty:
            st.warning("未获取到新数据")
        else:
            st.success(f"采集完成，共 {len(df)} 条净值数据")
