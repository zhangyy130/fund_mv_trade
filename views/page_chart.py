"""图表页 — 净值走势 + 均线图"""

import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from controllers.fund_manager import FundManager
from config import MA_PERIODS, DEFAULT_HISTORY_DAYS


def render(mgr: FundManager):
    st.header("净值走势 & 均线图")

    funds = mgr.list_funds()
    if funds.empty:
        st.info("请先在「基金管理」页添加基金")
        return

    # ── 选择基金 ──
    selected = st.selectbox("选择基金", funds["code"].tolist(), format_func=lambda x: x)
    if not selected:
        return

    # ── 日期范围 ──
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "起始日期",
            value=datetime.now() - timedelta(days=180),
            key="chart_start",
        )
    with col2:
        end_date = st.date_input(
            "结束日期",
            value=datetime.now(),
            key="chart_end",
        )

    # ── 均线选择 ──
    selected_ma = st.multiselect(
        "显示均线",
        MA_PERIODS,
        default=MA_PERIODS,
        format_func=lambda x: f"MA{x}",
    )

    # ── 获取数据 ──
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    with st.spinner("加载数据..."):
        df = mgr.get_nav_with_ma(selected, start_str, end_str)

    if df.empty:
        st.warning("该时间段无数据")
        return

    # ── 绘图 ──
    fig = go.Figure()

    # 净值线
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["nav"],
        mode="lines",
        name="单位净值",
        line=dict(color="#1f77b4", width=2),
    ))

    # 均线 — 高对比度配色，颜色固定对应 MA 周期
    color_map = {
        5: "#FF6B35",   # 橙色
        10: "#00C49A",  # 青绿
        20: "#D50000",  # 深红
        30: "#2962FF",  # 深蓝
        60: "#FFD600",  # 亮黄
        120: "#AA00FF", # 紫色
        250: "#6D4C41", # 棕色
    }
    for p in selected_ma:
        p = int(p)  # 确保是整数
        col = f"ma_{p}"
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df["date"], y=df[col],
                mode="lines",
                name=f"MA{p}",
                line=dict(color=color_map.get(p, "#999999"), width=1.5),
            ))

    fig.update_layout(
        title=f"{selected} 净值走势与均线",
        xaxis_title="日期",
        yaxis_title="净值",
        hovermode="x unified",
        height=500,
        template="plotly_white",
    )

    st.plotly_chart(fig, use_container_width=True)

    # ── 数据表格 ──
    with st.expander("查看原始数据"):
        display_df = df[["date", "nav"] + [f"ma_{p}" for p in selected_ma if f"ma_{p}" in df.columns]]
        display_df = display_df.round(4)
        st.dataframe(display_df, use_container_width=True)
