"""技术指标计算 — 纯函数，无副作用，可独立测试"""

import pandas as pd
import numpy as np
from config import MA_PERIODS


def calc_ma(series: pd.Series, period: int) -> pd.Series:
    """计算单条移动平均线"""
    return series.rolling(window=period, min_periods=period).mean()


def calc_all_ma(df: pd.DataFrame, periods: list[int] = None) -> pd.DataFrame:
    """为 DataFrame 添加所有均线列

    Args:
        df: 必须包含 'nav' 列
        periods: 均线周期列表，默认使用配置

    Returns:
        原 DataFrame 附加 ma_5, ma_10, ... 列
    """
    if periods is None:
        periods = MA_PERIODS

    result = df.copy()
    for p in periods:
        result[f"ma_{p}"] = calc_ma(result["nav"], p)
    return result


def detect_ma_turn(ma_series: pd.Series) -> pd.Series:
    """检测均线走平或上翘首日

    逻辑：前一日下降（ma[t] < ma[t-1]），当日走平或上升（ma[t] >= ma[t-1]）

    Returns:
        布尔 Series，True 表示该日为走平/上翘首日
    """
    diff = ma_series.diff()
    prev_down = diff.shift(1) < 0
    today_flat_or_up = diff >= 0
    return (prev_down & today_flat_or_up).fillna(False)


def detect_ma_cross(fast_ma: pd.Series, slow_ma: pd.Series) -> pd.Series:
    """检测均线上穿

    逻辑：前一日 fast <= slow，当日 fast > slow

    Returns:
        布尔 Series，True 表示该日发生上穿
    """
    prev_fast = fast_ma.shift(1)
    prev_slow = slow_ma.shift(1)
    crossed = (prev_fast <= prev_slow) & (fast_ma > slow_ma)
    return crossed.fillna(False)


def calc_nav_change_pct(nav_series: pd.Series) -> pd.Series:
    """计算净值涨跌幅（百分比）"""
    return nav_series.pct_change() * 100
