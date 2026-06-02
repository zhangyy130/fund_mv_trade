"""回测页 — 选择基金、策略、时间段，执行回测并展示结果"""

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from controllers.fund_manager import FundManager
from controllers.strategy import StrategyRegistry, Strategy
from controllers.backtester import Backtester
from models.fund_db import FundDB
from config import BACKTEST_INITIAL_CAPITAL


def render(mgr: FundManager):
    st.header("策略回测")

    funds = mgr.list_funds()
    if funds.empty:
        st.info("请先在「基金管理」页添加基金")
        return

    # ── 参数选择 ──
    col1, col2 = st.columns(2)
    with col1:
        fund_code = st.selectbox("选择基金", funds["code"].tolist(), key="bt_fund")
    with col2:
        strategy_mode = st.radio("策略来源", ["内置策略", "自定义策略"], horizontal=True, key="bt_mode")

    if strategy_mode == "内置策略":
        strategy_name = st.selectbox("选择策略", StrategyRegistry.list_names(), key="bt_strategy")
        strategy = StrategyRegistry.get(strategy_name)
    else:
        db = FundDB()
        saved_strategies = db.list_strategies()
        saved_names = [item["name"] for item in saved_strategies]

        if saved_names:
            options = ["当前自定义策略"] + saved_names
            selected_strategy = st.selectbox("选择自定义策略", options, key="bt_custom_choice")
            if selected_strategy != "当前自定义策略":
                saved = next(item for item in saved_strategies if item["name"] == selected_strategy)
                strategy = StrategyRegistry.build_from_params(saved["name"], saved["params"])
                st.write(f"使用已保存策略: **{strategy.name}**")
            else:
                strategy = st.session_state.get("custom_strategy")
                if strategy is None:
                    st.warning("请先在「策略配置」页创建自定义策略")
                    return
                st.write(f"使用最近创建的自定义策略: **{strategy.name}**")
        else:
            strategy = st.session_state.get("custom_strategy")
            if strategy is None:
                st.warning("请先在「策略配置」页创建自定义策略")
                return
            st.write(f"使用自定义策略: **{strategy.name}**")

    # 时间段
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input(
            "起始日期",
            value=datetime.now() - timedelta(days=365),
            key="bt_start",
        )
    with col2:
        end_date = st.date_input(
            "结束日期",
            value=datetime.now(),
            key="bt_end",
        )
    with col3:
        initial_capital = st.number_input(
            "初始资金",
            min_value=10000.0,
            value=float(BACKTEST_INITIAL_CAPITAL),
            step=10000.0,
            key="bt_capital",
        )

    # ── 执行回测 ──
    if st.button("开始回测", use_container_width=True, type="primary"):
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        with st.spinner("正在回测..."):
            df = mgr.get_nav_with_ma(fund_code, start_str, end_str)
            if df.empty:
                st.error("该时间段无数据，请先刷新基金数据")
                return

            bt = Backtester(initial_capital=initial_capital)
            result = bt.run(df, strategy, fund_code)

        _render_result(result, df)


def _render_result(result, df):
    """渲染回测结果"""
    st.success("回测完成")

    # ── 核心指标 ──
    st.subheader("回测统计")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("总收益率", f"{result.total_return_pct:.2f}%")
    c2.metric("年化收益率", f"{result.annual_return_pct:.2f}%")
    c3.metric("最大回撤", f"{result.max_drawdown_pct:.2f}%")
    c4.metric("胜率", f"{result.win_rate_pct:.1f}%")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("初始资金", f"¥{result.initial_capital:,.0f}")
    c2.metric("最终资金", f"¥{result.final_capital:,.0f}")
    c3.metric("交易次数", str(result.total_trades))
    c4.metric("回测区间", result.period)

    # ── 收益曲线图 ──
    st.subheader("收益曲线")
    daily = result.daily_nav
    if not daily.empty:
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.7, 0.3],
            subplot_titles=("净值 & 资产曲线", "持仓状态"),
        )

        # 净值
        fig.add_trace(go.Scatter(
            x=daily["date"], y=daily["nav"],
            name="基金净值", line=dict(color="#1f77b4", width=1.5),
        ), row=1, col=1)

        # 资产曲线（归一化到净值起始点便于对比）
        norm_portfolio = daily["portfolio"] / daily["portfolio"].iloc[0] * daily["nav"].iloc[0]
        fig.add_trace(go.Scatter(
            x=daily["date"], y=norm_portfolio,
            name="策略资产", line=dict(color="#ff7f0e", width=2),
        ), row=1, col=1)

        # 买卖点
        for t in result.trades:
            color = "green" if t.action == "buy" else "red"
            symbol = "triangle-up" if t.action == "buy" else "triangle-down"
            fig.add_trace(go.Scatter(
                x=[t.date], y=[t.price],
                mode="markers",
                marker=dict(color=color, size=12, symbol=symbol),
                name=f"{'买入' if t.action == 'buy' else '卖出'} {t.date}",
                showlegend=False,
            ), row=1, col=1)

        # 持仓状态（底部色条）
        position_map = {"持仓": 1, "空仓": 0}
        pos_values = daily["position"].map(position_map)
        fig.add_trace(go.Scatter(
            x=daily["date"], y=pos_values,
            fill="tozeroy",
            fillcolor="rgba(44,160,44,0.2)",
            line=dict(color="rgba(44,160,44,0)", width=0),
            name="持仓",
            showlegend=False,
        ), row=2, col=1)

        fig.update_layout(height=600, hovermode="x unified", template="plotly_white")
        fig.update_yaxes(title_text="净值", row=1, col=1)
        fig.update_yaxes(title_text="", tickvals=[0, 1], ticktext=["空仓", "持仓"], row=2, col=1)
        st.plotly_chart(fig, use_container_width=True)

    # ── 交易明细 ──
    if result.trades:
        st.subheader("交易明细")
        trade_data = [
            {
                "日期": t.date,
                "操作": "买入" if t.action == "buy" else "卖出",
                "价格": f"{t.price:.4f}",
                "份额": f"{t.shares:.2f}",
                "金额": f"¥{t.amount:,.2f}",
                "手续费": f"¥{t.commission:.2f}",
                "原因": t.reason,
            }
            for t in result.trades
        ]
        st.dataframe(trade_data, use_container_width=True)
