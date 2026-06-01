"""基金数据采集层 — 可替换数据源的抽象接口"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import pandas as pd


class BaseFundDataSource(ABC):
    """数据源抽象基类 — 替换数据源只需实现这个接口"""

    @abstractmethod
    def fetch_nav(self, fund_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取基金净值数据

        Returns:
            DataFrame, columns: [date, nav, acc_nav]
            - date: 日期
            - nav: 单位净值
            - acc_nav: 累计净值
        """
        pass

    @abstractmethod
    def fetch_fund_info(self, fund_code: str) -> dict:
        """获取基金基本信息

        Returns:
            dict: {code, name, type, ...}
        """
        pass


class AkShareDataSource(BaseFundDataSource):
    """基于 akshare 的数据源实现"""

    def fetch_nav(self, fund_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        import akshare as ak

        df = ak.fund_open_fund_info_em(symbol=fund_code, indicator="单位净值走势")
        if df.empty:
            return pd.DataFrame(columns=["date", "nav", "acc_nav"])

        # akshare 返回三列：净值日期、单位净值、日增长率
        # 用位置索引避免列名编码问题
        df = df.iloc[:, :2].copy()
        df.columns = ["date", "nav"]
        df["date"] = pd.to_datetime(df["date"])
        df["nav"] = df["nav"].astype(float)
        df["acc_nav"] = None  # 该接口无累计净值，填 None
        df = df.sort_values("date").reset_index(drop=True)

        # 过滤日期范围
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        df = df[(df["date"] >= start) & (df["date"] <= end)]

        return df[["date", "nav", "acc_nav"]].reset_index(drop=True)

    def fetch_fund_info(self, fund_code: str) -> dict:
        import akshare as ak

        try:
            df = ak.fund_individual_basic_info_xq(symbol=fund_code)
            if df.empty:
                return {"code": fund_code, "name": "未知基金"}

            # item 列是字段名，value 列是值，转成 dict
            info = dict(zip(df["item"], df["value"]))
            return {
                "code": fund_code,
                "name": info.get("基金名称", fund_code),
                "fund_manager": info.get("基金经理", ""),
                "fund_company": info.get("基金公司", ""),
                "establish_date": info.get("成立时间", ""),
            }
        except Exception:
            return {"code": fund_code, "name": "未知基金"}


def get_default_source() -> BaseFundDataSource:
    """工厂函数 — 切换数据源只需改这里"""
    return AkShareDataSource()
