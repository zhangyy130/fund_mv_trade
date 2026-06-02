"""基金数据存储层 — SQLite 实现，可替换为其他存储引擎"""

import os
import sqlite3
import pandas as pd
from config import DB_PATH


class FundDB:
    """基金数据库操作封装"""

    def __init__(self, db_path: str = DB_PATH):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_tables()

    def _get_conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_tables(self):
        conn = self._get_conn()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS funds (
                    code TEXT PRIMARY KEY,
                    name TEXT NOT NULL DEFAULT '',
                    fund_manager TEXT DEFAULT '',
                    fund_company TEXT DEFAULT '',
                    establish_date TEXT DEFAULT '',
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS nav_history (
                    fund_code TEXT NOT NULL,
                    date TEXT NOT NULL,
                    nav REAL NOT NULL,
                    acc_nav REAL,
                    PRIMARY KEY (fund_code, date),
                    FOREIGN KEY (fund_code) REFERENCES funds(code)
                );

                CREATE TABLE IF NOT EXISTS strategies (
                    name TEXT PRIMARY KEY,
                    buy_rules TEXT NOT NULL,
                    sell_rules TEXT NOT NULL,
                    params TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
        finally:
            conn.close()

        # 数据库迁移：给已有 funds 表添加新列（如果不存在）
        self._migrate()

    def _migrate(self):
        conn = self._get_conn()
        try:
            cols = {row[1] for row in conn.execute("PRAGMA table_info(funds)").fetchall()}
            for col, typ, default in [
                ("fund_manager", "TEXT", ""),
                ("fund_company", "TEXT", ""),
                ("establish_date", "TEXT", ""),
            ]:
                if col not in cols:
                    conn.execute(f"ALTER TABLE funds ADD COLUMN {col} {typ} DEFAULT '{default}'")
            conn.commit()
        finally:
            conn.close()

    # ── 基金管理 ──

    def add_fund(self, code: str, name: str = "", fund_manager: str = "",
                 fund_company: str = "", establish_date: str = ""):
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT OR IGNORE INTO funds (code, name, fund_manager, fund_company, establish_date) "
                "VALUES (?, ?, ?, ?, ?)",
                (code, name, fund_manager, fund_company, establish_date),
            )
            conn.commit()
        finally:
            conn.close()

    def update_fund(self, code: str, name: str = "", fund_manager: str = "",
                    fund_company: str = "", establish_date: str = ""):
        conn = self._get_conn()
        try:
            conn.execute(
                "UPDATE funds SET name=?, fund_manager=?, fund_company=?, establish_date=? WHERE code=?",
                (name, fund_manager, fund_company, establish_date, code),
            )
            conn.commit()
        finally:
            conn.close()

    def remove_fund(self, code: str):
        conn = self._get_conn()
        try:
            conn.execute("DELETE FROM nav_history WHERE fund_code = ?", (code,))
            conn.execute("DELETE FROM funds WHERE code = ?", (code,))
            conn.commit()
        finally:
            conn.close()

    def list_funds(self) -> pd.DataFrame:
        conn = self._get_conn()
        try:
            return pd.read_sql(
                "SELECT code, name, fund_manager, fund_company, establish_date, added_at "
                "FROM funds ORDER BY added_at", conn
            )
        finally:
            conn.close()

    # ── 净值数据 ──

    def save_nav(self, fund_code: str, df: pd.DataFrame):
        """保存净值数据（增量更新，已有日期跳过）"""
        if df.empty:
            return
        conn = self._get_conn()
        try:
            for _, row in df.iterrows():
                conn.execute(
                    "INSERT OR IGNORE INTO nav_history (fund_code, date, nav, acc_nav) VALUES (?, ?, ?, ?)",
                    (fund_code, row["date"].strftime("%Y-%m-%d"), row["nav"], row.get("acc_nav")),
                )
            conn.commit()
        finally:
            conn.close()

    def get_nav(self, fund_code: str) -> pd.DataFrame:
        """获取指定基金的全部净值历史"""
        conn = self._get_conn()
        try:
            df = pd.read_sql(
                "SELECT date, nav, acc_nav FROM nav_history WHERE fund_code = ? ORDER BY date",
                conn,
                params=(fund_code,),
            )
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
            return df
        finally:
            conn.close()

    def get_nav_range(self, fund_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取指定日期范围的净值数据"""
        conn = self._get_conn()
        try:
            df = pd.read_sql(
                "SELECT date, nav, acc_nav FROM nav_history "
                "WHERE fund_code = ? AND date >= ? AND date <= ? ORDER BY date",
                conn,
                params=(fund_code, start_date, end_date),
            )
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
            return df
        finally:
            conn.close()

    def get_latest_nav_date(self, fund_code: str) -> str | None:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT MAX(date) FROM nav_history WHERE fund_code = ?", (fund_code,)
            ).fetchone()
            return row[0] if row and row[0] else None
        finally:
            conn.close()

    # ── 策略存储 ──

    def save_strategy(self, name: str, buy_rules: list, sell_rules: list, params: dict = None):
        import json
        conn = self._get_conn()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO strategies (name, buy_rules, sell_rules, params) VALUES (?, ?, ?, ?)",
                (name, json.dumps(buy_rules, ensure_ascii=False),
                 json.dumps(sell_rules, ensure_ascii=False),
                 json.dumps(params or {}, ensure_ascii=False)),
            )
            conn.commit()
        finally:
            conn.close()

    def list_strategies(self) -> list[dict]:
        import json
        conn = self._get_conn()
        try:
            rows = conn.execute("SELECT name, buy_rules, sell_rules, params FROM strategies").fetchall()
            return [
                {
                    "name": r[0],
                    "buy_rules": json.loads(r[1]),
                    "sell_rules": json.loads(r[2]),
                    "params": json.loads(r[3]),
                }
                for r in rows
            ]
        finally:
            conn.close()

    def delete_strategy(self, name: str):
        conn = self._get_conn()
        try:
            conn.execute("DELETE FROM strategies WHERE name = ?", (name,))
            conn.commit()
        finally:
            conn.close()
