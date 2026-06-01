"""基金管理控制器 — 协调模型层完成业务操作"""

from models.fund_data import BaseFundDataSource, get_default_source
from models.fund_db import FundDB
from models.indicators import calc_all_ma
import pandas as pd


class FundManager:
    """基金管理业务逻辑"""

    def __init__(self, db: FundDB = None, source: BaseFundDataSource = None):
        self.db = db or FundDB()
        self.source = source or get_default_source()

    def add_fund(self, code: str, name: str = "") -> dict:
        """添加基金，返回基金信息 dict"""
        info = self.source.fetch_fund_info(code)
        self.db.add_fund(
            code=code,
            name=info.get("name", name),
            fund_manager=info.get("fund_manager", ""),
            fund_company=info.get("fund_company", ""),
            establish_date=info.get("establish_date", ""),
        )
        return info

    def remove_fund(self, code: str):
        self.db.remove_fund(code)

    def list_funds(self) -> pd.DataFrame:
        return self.db.list_funds()

    def refresh_nav(self, code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """从数据源拉取净值并存入本地，返回完整数据"""
        df = self.source.fetch_nav(code, start_date, end_date)
        if not df.empty:
            self.db.save_nav(code, df)
        return df

    def get_nav_with_ma(self, code: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """获取净值 + 均线数据"""
        if start_date and end_date:
            df = self.db.get_nav_range(code, start_date, end_date)
        else:
            df = self.db.get_nav(code)

        if df.empty:
            return df

        return calc_all_ma(df)
