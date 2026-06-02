"""策略配置页 — 选择/自定义交易策略"""

import streamlit as st
from controllers.strategy import StrategyRegistry, Strategy
from models.fund_db import FundDB
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

    db = FundDB()
    saved_strategies = db.list_strategies()
    saved_names = [item["name"] for item in saved_strategies]
    new_label = "新建策略"

    selected_saved = st.selectbox("已保存策略", [new_label] + saved_names, key="saved_strategy_select")
    st.caption("选择已保存策略后点击加载，可直接编辑并保存为更新版本。")
    if selected_saved != new_label and st.button("加载到表单", key="load_saved"):
        loaded = next((item for item in saved_strategies if item["name"] == selected_saved), None)
        if loaded:
            params = loaded["params"]
            st.session_state["loaded_strategy_name"] = loaded["name"]
            st.session_state["custom_strategy_name"] = loaded["name"]
            st.session_state["buy_ma_turn"] = params.get("buy_ma_turn", [])
            st.session_state["buy_cross_selected"] = [f"MA{f}上穿MA{s}" for f, s in params.get("buy_ma_cross", [])]
            st.session_state["buy_ma_align_groups"] = params.get("buy_ma_align", []) or []
            st.session_state["enable_profit"] = params.get("sell_profit") is not None
            st.session_state["profit_pct"] = params.get("sell_profit", 10.0)
            st.session_state["profit_ratio"] = params.get("sell_profit_ratio", 0.5)
            st.session_state["enable_stop"] = params.get("sell_stop_loss") is not None
            st.session_state["stop_pct"] = params.get("sell_stop_loss", 10.0)
            st.session_state["enable_ma_break"] = params.get("sell_ma_break") is not None
            st.session_state["break_period"] = params.get("sell_ma_break", MA_PERIODS[0])
            st.session_state["sell_ma_bear_align_groups"] = params.get("sell_ma_bear_align", []) or []
            st.rerun()

    if st.button("重置表单", key="reset_custom"):
        for key in [
            "loaded_strategy_name",
            "custom_strategy_name",
            "buy_ma_turn",
            "buy_cross_selected",
            "buy_ma_align_groups",
            "enable_profit",
            "profit_pct",
            "profit_ratio",
            "enable_stop",
            "stop_pct",
            "enable_ma_break",
            "break_period",
            "sell_ma_bear_align_groups",
            "overwrite_existing",
            "custom_strategy",
        ]:
            st.session_state.pop(key, None)
        st.rerun()

    name = st.text_input(
        "策略名称",
        value=st.session_state.get("custom_strategy_name", "我的策略"),
        key="custom_strategy_name",
    )
    loaded_strategy_name = st.session_state.get("loaded_strategy_name")
    if loaded_strategy_name:
        st.info(f"正在编辑已保存策略：{loaded_strategy_name}。修改名称后将保存为新策略。")
    overwrite_existing = st.checkbox(
        "允许覆盖已存在同名策略",
        value=False,
        key="overwrite_existing",
    )

    st.markdown("##### 买入规则")
    buy_ma_turn = st.multiselect(
        "均线走平上翘周期",
        MA_PERIODS,
        default=st.session_state.get("buy_ma_turn", []),
        key="buy_ma_turn",
    )

    cross_options = [f"MA{fast}上穿MA{slow}" for fast in MA_PERIODS for slow in MA_PERIODS if fast < slow]
    buy_cross_selected = st.multiselect(
        "均线上穿组合（可选择多个）",
        cross_options,
        default=st.session_state.get("buy_cross_selected", []),
        key="buy_cross_selected",
    )
    buy_ma_cross = []
    for item in buy_cross_selected:
        fast, slow = item.replace("MA", "").split("上穿MA")
        buy_ma_cross.append((int(fast), int(slow)))

    if "buy_ma_align_groups" not in st.session_state:
        st.session_state["buy_ma_align_groups"] = st.session_state.get("buy_ma_align", []) or []

    st.markdown("##### 多头排列组合")
    if st.session_state["buy_ma_align_groups"]:
        for idx, group in enumerate(st.session_state["buy_ma_align_groups"]):
            col1, col2 = st.columns([4, 1])
            col1.write(f"组 {idx + 1}: MA{','.join(str(p) for p in group)}")
            if col2.button("删除", key=f"del_buy_align_{idx}"):
                st.session_state["buy_ma_align_groups"].pop(idx)
                st.rerun()

    new_buy_ma_align = st.multiselect(
        "新增多头排列组",
        MA_PERIODS,
        default=[],
        key="new_buy_ma_align",
    )
    if st.button("添加多头排列组", key="add_buy_align"):
        if len(new_buy_ma_align) > 1:
            groups = st.session_state["buy_ma_align_groups"]
            if new_buy_ma_align not in groups:
                groups.append(new_buy_ma_align)
                st.session_state["buy_ma_align_groups"] = groups
        else:
            st.warning("多头排列组至少需要选择两个均线周期")
        st.rerun()

    st.markdown("##### 卖出规则")
    profit_pct = st.session_state.get("profit_pct", 10.0)
    profit_ratio = st.session_state.get("profit_ratio", 0.5)
    stop_pct = st.session_state.get("stop_pct", 10.0)
    break_period = st.session_state.get("break_period", MA_PERIODS[0])

    col1, col2 = st.columns(2)
    with col1:
        enable_profit = st.checkbox(
            "启用盈利卖出",
            value=st.session_state.get("enable_profit", True),
            key="enable_profit",
        )
        if enable_profit:
            profit_pct = st.number_input(
                "盈利目标 (%)",
                1.0,
                100.0,
                value=profit_pct,
                key="profit_pct",
            )
            profit_ratio = st.slider(
                "卖出仓位比例",
                0.1,
                1.0,
                value=profit_ratio,
                key="profit_ratio",
            )
    with col2:
        enable_stop = st.checkbox(
            "启用止损",
            value=st.session_state.get("enable_stop", False),
            key="enable_stop",
        )
        if enable_stop:
            stop_pct = st.number_input(
                "止损线 (%)",
                1.0,
                50.0,
                value=st.session_state.get("stop_pct", 10.0),
                key="stop_pct",
            )

    enable_ma_break = st.checkbox(
        "启用均线止损（跌破均线清仓）",
        value=st.session_state.get("enable_ma_break", False),
        key="enable_ma_break",
    )
    if enable_ma_break:
        break_period = st.selectbox(
            "止损均线",
            MA_PERIODS,
            index=MA_PERIODS.index(st.session_state.get("break_period", MA_PERIODS[0])),
            key="break_period",
        )

    if "sell_ma_bear_align_groups" not in st.session_state:
        st.session_state["sell_ma_bear_align_groups"] = st.session_state.get("sell_ma_bear_align", []) or []

    st.markdown("##### 空头排列组合")
    if st.session_state["sell_ma_bear_align_groups"]:
        for idx, group in enumerate(st.session_state["sell_ma_bear_align_groups"]):
            col1, col2 = st.columns([4, 1])
            col1.write(f"组 {idx + 1}: MA{','.join(str(p) for p in group)}")
            if col2.button("删除", key=f"del_sell_align_{idx}"):
                st.session_state["sell_ma_bear_align_groups"].pop(idx)
                st.rerun()

    new_sell_ma_bear_align = st.multiselect(
        "新增空头排列组",
        MA_PERIODS,
        default=[],
        key="new_sell_ma_bear_align",
    )
    if st.button("添加空头排列组", key="add_sell_bear_align"):
        if len(new_sell_ma_bear_align) > 1:
            groups = st.session_state["sell_ma_bear_align_groups"]
            if new_sell_ma_bear_align not in groups:
                groups.append(new_sell_ma_bear_align)
                st.session_state["sell_ma_bear_align_groups"] = groups
        else:
            st.warning("空头排列组至少需要选择两个均线周期")
        st.rerun()

    strategy = StrategyRegistry.build_custom(
        name=name,
        buy_ma_turn=buy_ma_turn or None,
        buy_ma_cross=buy_ma_cross or None,
        buy_ma_align=buy_ma_align_groups or None,
        sell_profit=sell_profit,
        sell_profit_ratio=sell_ratio,
        sell_stop_loss=sell_stop,
        sell_ma_break=sell_break,
        sell_ma_bear_align=sell_ma_bear_align_groups or None,
    )

    if st.button("保存策略", key="save_custom"):
        params = {
            "buy_ma_turn": buy_ma_turn,
            "buy_ma_cross": buy_ma_cross,
            "buy_ma_align": buy_ma_align_groups,
            "sell_profit": sell_profit,
            "sell_profit_ratio": sell_ratio,
            "sell_stop_loss": sell_stop,
            "sell_ma_break": sell_break,
            "sell_ma_bear_align": sell_ma_bear_align_groups,
        }
        if not name.strip():
            st.error("请输入策略名称")
        else:
            existing_names = [item["name"] for item in saved_strategies]
            if name in existing_names and name != st.session_state.get("loaded_strategy_name") and not overwrite_existing:
                st.warning("存在同名策略，请修改名称或勾选【允许覆盖已存在同名策略】")
            else:
                if st.session_state.get("loaded_strategy_name") and st.session_state["loaded_strategy_name"] != name:
                    db.delete_strategy(st.session_state["loaded_strategy_name"])
                db.save_strategy(name, [r.name for r in strategy.buy_rules], [r.name for r in strategy.sell_rules], params)
                st.session_state["loaded_strategy_name"] = name
                st.session_state["custom_strategy_name"] = name
                st.session_state["custom_strategy"] = strategy
                st.success(f"策略「{name}」已保存，可在回测页使用")
                st.rerun()

    with st.expander("策略预览"):
        st.write("**买入规则：**")
        for r in strategy.buy_rules:
            st.write(f"  - {r.name}: {r.description}")
        st.write("**卖出规则：**")
        for r in strategy.sell_rules:
            st.write(f"  - {r.name}: {r.description}")

    if saved_names:
        st.markdown("##### 已保存策略列表")
        for item in saved_strategies:
            cols = st.columns([5, 1])
            cols[0].write(f"- **{item['name']}**：买入 {', '.join(item['buy_rules']) or '无'}；卖出 {', '.join(item['sell_rules']) or '无'}")
            if cols[1].button("删除", key=f"delete_strategy_{item['name']}"):
                db.delete_strategy(item['name'])
                st.success(f"已删除策略：{item['name']}")
                st.rerun()
