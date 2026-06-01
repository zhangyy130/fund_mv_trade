"""回测引擎 — 模拟交易执行，生成回测报告"""

from dataclasses import dataclass, field
from controllers.strategy import Strategy, Signal
from models.indicators import calc_all_ma
from config import BACKTEST_INITIAL_CAPITAL, BACKTEST_COMMISSION_RATE
import pandas as pd
import numpy as np


@dataclass
class Trade:
    """单笔交易记录"""
    date: str
    action: str  # "buy" / "sell"
    price: float
    shares: float
    amount: float
    commission: float
    reason: str = ""


@dataclass
class BacktestResult:
    """回测结果"""
    trades: list[Trade] = field(default_factory=list)
    daily_nav: pd.DataFrame = field(default_factory=pd.DataFrame)
    initial_capital: float = 0
    final_capital: float = 0
    total_return_pct: float = 0
    annual_return_pct: float = 0
    max_drawdown_pct: float = 0
    win_rate_pct: float = 0
    total_trades: int = 0
    strategy_name: str = ""
    fund_code: str = ""
    period: str = ""


class Backtester:
    """回测引擎"""

    def __init__(
        self,
        initial_capital: float = BACKTEST_INITIAL_CAPITAL,
        commission_rate: float = BACKTEST_COMMISSION_RATE,
    ):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate

    def run(self, df: pd.DataFrame, strategy: Strategy, fund_code: str = "") -> BacktestResult:
        """执行回测

        Args:
            df: 必须包含 date, nav 列
            strategy: 交易策略
            fund_code: 基金代码（仅用于报告）

        Returns:
            BacktestResult
        """
        if df.empty or len(df) < 5:
            return BacktestResult(strategy_name=strategy.name, fund_code=fund_code)

        # 计算均线
        data = calc_all_ma(df).copy()
        data = data.reset_index(drop=True)

        # 初始化账户状态
        cash = self.initial_capital
        shares = 0.0
        trades: list[Trade] = []
        portfolio_values = []
        buy_price = 0.0

        for i in range(len(data)):
            row = data.iloc[i]
            current_nav = row["nav"]
            signal = strategy.check_signal(row, data)

            if signal == Signal.BUY and shares == 0:
                # 全仓买入
                commission = cash * self.commission_rate
                amount = cash - commission
                shares = amount / current_nav
                buy_price = current_nav
                cash = 0
                trades.append(Trade(
                    date=str(row["date"].date()),
                    action="buy",
                    price=current_nav,
                    shares=shares,
                    amount=amount,
                    commission=commission,
                    reason=strategy.name,
                ))

            elif signal == Signal.SELL and shares > 0:
                # 全仓卖出
                amount = shares * current_nav
                commission = amount * self.commission_rate
                cash = amount - commission
                pnl_pct = (current_nav - buy_price) / buy_price * 100
                trades.append(Trade(
                    date=str(row["date"].date()),
                    action="sell",
                    price=current_nav,
                    shares=shares,
                    amount=amount,
                    commission=commission,
                    reason=f"盈亏{pnl_pct:.2f}%",
                ))
                shares = 0.0
                buy_price = 0.0

            # 记录当日总资产
            total = cash + shares * current_nav
            portfolio_values.append({
                "date": row["date"],
                "nav": current_nav,
                "portfolio": total,
                "position": "持仓" if shares > 0 else "空仓",
            })

        daily_df = pd.DataFrame(portfolio_values)

        # 计算统计指标
        final_capital = daily_df["portfolio"].iloc[-1] if not daily_df.empty else self.initial_capital
        total_return = (final_capital - self.initial_capital) / self.initial_capital * 100

        # 最大回撤
        peak = daily_df["portfolio"].cummax()
        drawdown = (daily_df["portfolio"] - peak) / peak * 100
        max_drawdown = drawdown.min()

        # 年化收益率
        days = (daily_df["date"].iloc[-1] - daily_df["date"].iloc[0]).days if len(daily_df) > 1 else 1
        annual_return = ((final_capital / self.initial_capital) ** (365 / max(days, 1)) - 1) * 100

        # 胜率
        sell_trades = [t for t in trades if t.action == "sell"]
        buy_trades = [t for t in trades if t.action == "buy"]
        wins = 0
        for i, sell in enumerate(sell_trades):
            if i < len(buy_trades) and sell.price > buy_trades[i].price:
                wins += 1
        win_rate = (wins / len(sell_trades) * 100) if sell_trades else 0

        period = f"{data['date'].iloc[0].date()} ~ {data['date'].iloc[-1].date()}"

        return BacktestResult(
            trades=trades,
            daily_nav=daily_df,
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return_pct=total_return,
            annual_return_pct=annual_return,
            max_drawdown_pct=max_drawdown,
            win_rate_pct=win_rate,
            total_trades=len(trades),
            strategy_name=strategy.name,
            fund_code=fund_code,
            period=period,
        )
