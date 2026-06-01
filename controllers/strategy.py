"""策略框架 — 基于规则的买入/卖出策略定义与执行"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable
import pandas as pd
from models.indicators import detect_ma_turn, detect_ma_cross


# ── 信号类型 ──

class Signal(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


# ── 规则定义 ──

@dataclass
class Rule:
    """单条交易规则"""
    name: str
    check: Callable[[pd.Series, pd.DataFrame], bool]
    description: str = ""


# ── 内置买入规则工厂 ──

def rule_ma_turn_up(ma_period: int) -> Rule:
    """N日均线走平或上翘首日"""
    col = f"ma_{ma_period}"

    def check(row, df):
        idx = row.name
        if idx < 1 or col not in df.columns:
            return False
        ma_slice = df[col].iloc[:idx + 1]
        signals = detect_ma_turn(ma_slice)
        return bool(signals.iloc[-1]) if len(signals) > 0 else False

    return Rule(
        name=f"MA{ma_period}走平上翘首日",
        check=check,
        description=f"{ma_period}日均线由下降转为走平或上升",
    )


def rule_ma_cross(fast: int, slow: int) -> Rule:
    """快线上穿慢线"""
    fast_col = f"ma_{fast}"
    slow_col = f"ma_{slow}"

    def check(row, df):
        idx = row.name
        if idx < 1 or fast_col not in df.columns or slow_col not in df.columns:
            return False
        fast_slice = df[fast_col].iloc[:idx + 1]
        slow_slice = df[slow_col].iloc[:idx + 1]
        signals = detect_ma_cross(fast_slice, slow_slice)
        return bool(signals.iloc[-1]) if len(signals) > 0 else False

    return Rule(
        name=f"MA{fast}上穿MA{slow}",
        check=check,
        description=f"{fast}日均线向上穿过{slow}日均线",
    )


def rule_ma_cross_multi(crosses: list[tuple[int, int]]) -> Rule:
    """多组均线同时上穿（同一天全部满足）"""
    rules = [rule_ma_cross(f, s) for f, s in crosses]
    names = " & ".join(f"MA{f}上穿MA{s}" for f, s in crosses)

    def check(row, df):
        return all(r.check(row, df) for r in rules)

    return Rule(name=names, check=check)


# ── 内置卖出规则工厂 ──

def rule_profit_sell(target_pct: float, sell_ratio: float) -> Rule:
    """盈利达到目标百分比时卖出指定仓位"""
    def check(row, df):
        idx = row.name
        if idx < 1:
            return False
        nav_now = row["nav"]
        nav_buy = df["nav"].iloc[:idx].min()  # 简化：取历史最低作为买入参考
        pct = (nav_now - nav_buy) / nav_buy * 100
        return pct >= target_pct

    return Rule(
        name=f"盈利{target_pct}%卖出{int(sell_ratio * 100)}%",
        check=check,
        description=f"浮盈达到{target_pct}%时卖出{int(sell_ratio * 100)}%仓位",
    )


def rule_stop_loss(loss_pct: float) -> Rule:
    """止损规则"""
    def check(row, df):
        idx = row.name
        if idx < 1:
            return False
        nav_now = row["nav"]
        nav_buy = df["nav"].iloc[:idx].min()
        pct = (nav_now - nav_buy) / nav_buy * 100
        return pct <= -loss_pct

    return Rule(
        name=f"止损{loss_pct}%",
        check=check,
        description=f"浮亏达到{loss_pct}%时清仓",
    )


def rule_ma_break_down(ma_period: int) -> Rule:
    """跌破N日均线"""
    col = f"ma_{ma_period}"

    def check(row, df):
        if col not in df.columns:
            return False
        return row["nav"] < row[col]

    return Rule(
        name=f"跌破MA{ma_period}",
        check=check,
        description=f"净值跌破{ma_period}日均线",
    )


# ── 策略类 ──

@dataclass
class Strategy:
    """交易策略：由买入规则列表和卖出规则列表组成"""
    name: str
    buy_rules: list[Rule] = field(default_factory=list)
    sell_rules: list[Rule] = field(default_factory=list)

    def check_signal(self, row: pd.Series, df: pd.DataFrame) -> Signal:
        """检查当前行应该产生什么信号"""
        # 买入信号：任意一条买入规则触发
        for rule in self.buy_rules:
            if rule.check(row, df):
                return Signal.BUY

        # 卖出信号：任意一条卖出规则触发
        for rule in self.sell_rules:
            if rule.check(row, df):
                return Signal.SELL

        return Signal.HOLD


# ── 策略注册表 ──

class StrategyRegistry:
    """内置策略注册表 — 便于在 UI 中选择"""

    BUILTIN_STRATEGIES: dict[str, callable] = {
        "MA5走平上翘": lambda: Strategy(
            name="MA5走平上翘",
            buy_rules=[rule_ma_turn_up(5)],
            sell_rules=[rule_profit_sell(10, 0.5)],
        ),
        "MA20走平上翘": lambda: Strategy(
            name="MA20走平上翘",
            buy_rules=[rule_ma_turn_up(20)],
            sell_rules=[rule_profit_sell(10, 0.5)],
        ),
        "MA5上穿MA10": lambda: Strategy(
            name="MA5上穿MA10",
            buy_rules=[rule_ma_cross(5, 10)],
            sell_rules=[rule_profit_sell(10, 0.5)],
        ),
        "MA5上穿MA10且MA5上穿MA20": lambda: Strategy(
            name="MA5上穿MA10且MA5上穿MA20",
            buy_rules=[rule_ma_cross_multi([(5, 10), (5, 20)])],
            sell_rules=[rule_profit_sell(10, 0.5)],
        ),
    }

    @classmethod
    def get(cls, name: str) -> Strategy:
        return cls.BUILTIN_STRATEGIES[name]()

    @classmethod
    def list_names(cls) -> list[str]:
        return list(cls.BUILTIN_STRATEGIES.keys())

    @classmethod
    def build_custom(
        cls,
        name: str,
        buy_ma_turn: list[int] = None,
        buy_ma_cross: list[tuple[int, int]] = None,
        sell_profit: float = None,
        sell_profit_ratio: float = 0.5,
        sell_stop_loss: float = None,
        sell_ma_break: int = None,
    ) -> Strategy:
        """从 UI 参数构建自定义策略"""
        buy_rules = []
        if buy_ma_turn:
            for p in buy_ma_turn:
                buy_rules.append(rule_ma_turn_up(p))
        if buy_ma_cross:
            if len(buy_ma_cross) == 1:
                buy_rules.append(rule_ma_cross(*buy_ma_cross[0]))
            else:
                buy_rules.append(rule_ma_cross_multi(buy_ma_cross))

        sell_rules = []
        if sell_profit is not None:
            sell_rules.append(rule_profit_sell(sell_profit, sell_profit_ratio))
        if sell_stop_loss is not None:
            sell_rules.append(rule_stop_loss(sell_stop_loss))
        if sell_ma_break is not None:
            sell_rules.append(rule_ma_break_down(sell_ma_break))

        return Strategy(name=name, buy_rules=buy_rules, sell_rules=sell_rules)
