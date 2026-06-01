"""策略配置页 — 选择/自定义交易策略"""

import streamlit as st
from controllers.strategy import StrategyRegistry, Strategy
from config import MA_PERIODS


def render():
    st.header("交易策略配置")

    tab1, tab2 = st.tabs(["内置策略", "自定义策略"])

    with tab1:
        _render_builtin()
    with tab2:
        _render_custom()


def _render_builtin():
    st.subheader("内置策略")

    names = StrategyRegistry.list_names()
    for name in names:
        strategy = StrategyRegistry.get(name)
        with st.expander(f"📋 {name}"):
            st.write("**买入规则：**")
            for r in strategy.buy_rules:
                st.write(f"  - {r.name}: {r.description}")
            st.write("**卖出规则：**")
            for r in strategy.sell_rules:
                st.write(f"  - {r.name}: {r.description}")

    st.info("内置策略可在「回测」页直接使用")


def _render_custom():
    st.subheader("自定义策略")

    name = st.text_input("策略名称", value="我的策略", key="custom_strategy_name")

    st.markdown("##### 买入规则")
    buy_type = st.radio(
        "买入触发方式",
        ["均线走平上翘", "均线上穿", "多组均线上穿"],
        key="buy_type",
        horizontal=True,
    )

    buy_ma_turn = []
    buy_ma_cross = []

    if buy_type == "均线走平上翘":
        period = st.selectbox("均线周期", MA_PERIODS, key="turn_period")
        buy_ma_turn = [period]
    elif buy_type == "均线上穿":
        col1, col2 = st.columns(2)
        with col1:
            fast = st.selectbox("快线", MA_PERIODS, key="cross_fast")
        with col2:
            slow = st.selectbox("慢线", MA_PERIODS, key="cross_slow")
        buy_ma_cross = [(fast, slow)]
    elif buy_type == "多组均线上穿":
        st.write("至少选择两组上穿条件（同一天全部满足才触发）")
        c1, c2 = st.columns(2)
        with c1:
            fast1 = st.selectbox("快线1", MA_PERIODS, key="mcf1")
            slow1 = st.selectbox("慢线1", MA_PERIODS, key="mcs1")
        with c2:
            fast2 = st.selectbox("快线2", MA_PERIODS, key="mcf2")
            slow2 = st.selectbox("慢线2", MA_PERIODS, key="mcs2")
        buy_ma_cross = [(fast1, slow1), (fast2, slow2)]

    st.markdown("##### 卖出规则")

    col1, col2 = st.columns(2)
    with col1:
        enable_profit = st.checkbox("启用盈利卖出", value=True, key="enable_profit")
        if enable_profit:
            profit_pct = st.number_input("盈利目标 (%)", 1.0, 100.0, 10.0, key="profit_pct")
            profit_ratio = st.slider("卖出仓位比例", 0.1, 1.0, 0.5, key="profit_ratio")
    with col2:
        enable_stop = st.checkbox("启用止损", value=False, key="enable_stop")
        if enable_stop:
            stop_pct = st.number_input("止损线 (%)", 1.0, 50.0, 10.0, key="stop_pct")

    enable_ma_break = st.checkbox("启用均线止损（跌破均线清仓）", value=False, key="enable_ma_break")
    if enable_ma_break:
        break_period = st.selectbox("止损均线", MA_PERIODS, key="break_period")

    # 构建策略
    sell_profit = profit_pct if enable_profit else None
    sell_ratio = profit_ratio if enable_profit else 0.5
    sell_stop = stop_pct if enable_stop else None
    sell_break = break_period if enable_ma_break else None

    strategy = StrategyRegistry.build_custom(
        name=name,
        buy_ma_turn=buy_ma_turn or None,
        buy_ma_cross=buy_ma_cross or None,
        sell_profit=sell_profit,
        sell_profit_ratio=sell_ratio,
        sell_stop_loss=sell_stop,
        sell_ma_break=sell_break,
    )

    if st.button("保存策略", key="save_custom"):
        st.session_state["custom_strategy"] = strategy
        st.success(f"策略「{name}」已保存，可在回测页使用")

    # 预览
    with st.expander("策略预览"):
        st.write("**买入规则：**")
        for r in strategy.buy_rules:
            st.write(f"  - {r.name}: {r.description}")
        st.write("**卖出规则：**")
        for r in strategy.sell_rules:
            st.write(f"  - {r.name}: {r.description}")
