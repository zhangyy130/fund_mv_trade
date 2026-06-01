"""全局配置 — 所有可调参数集中管理"""

import os

# 数据存储路径
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "fund.db")

# 均线周期列表
MA_PERIODS = [5, 10, 20, 30, 60, 120, 250]

# 默认起始日期（距今天数）
DEFAULT_HISTORY_DAYS = 365

# 回测默认参数
BACKTEST_INITIAL_CAPITAL = 100000.0
BACKTEST_COMMISSION_RATE = 0.001  # 手续费率 0.1%
