"""全局配置 — 所有可调参数集中管理"""

import os

# 数据存储路径
# 本地运行：项目目录下的 data/fund.db
# Codespaces：/workspaces/<repo>/data/fund.db（持久化）
_DB_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(_DB_DIR, exist_ok=True)
DB_PATH = os.path.join(_DB_DIR, "fund.db")

# 均线周期列表
MA_PERIODS = [5, 10, 20, 30, 60, 120, 250]

# 默认起始日期（距今天数）
DEFAULT_HISTORY_DAYS = 365

# 回测默认参数
BACKTEST_INITIAL_CAPITAL = 100000.0
BACKTEST_COMMISSION_RATE = 0.001  # 手续费率 0.1%
