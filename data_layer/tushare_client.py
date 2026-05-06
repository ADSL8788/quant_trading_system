#!/usr/bin/env python3
"""Tushare数据客户端 - 带缓存"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
from config.settings import config

class TushareClient:
    def __init__(self):
        ts.set_token(config.TUSHARE_TOKEN)
        self.pro = ts.pro_api()
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        print(f"✅ Tushare客户端初始化成功")

    def _get_cache_path(self, ts_code, days):
        return os.path.join(self.cache_dir, f"{ts_code}_{days}.parquet")

    def _load_cache(self, ts_code, days):
        path = self._get_cache_path(ts_code, days)
        if os.path.exists(path):
            try:
                df = pd.read_parquet(path)
                if len(df) >= days - 5:
                    print(f"✅ 缓存命中 {ts_code}")
                    return df
            except:
                pass
        return None

    def _save_cache(self, ts_code, days, df):
        if df is not None and not df.empty:
            path = self._get_cache_path(ts_code, days)
            df.to_parquet(path, index=False)
            print(f"💾 缓存保存 {ts_code}")

    def get_kline(self, ts_code: str, days: int = 120, force_refresh: bool = False) -> pd.DataFrame:
        if not force_refresh:
            cached = self._load_cache(ts_code, days)
            if cached is not None:
                return cached.tail(days)

        print(f"🌐 下载 {ts_code}")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days*2)

        df = self.pro.daily(
            ts_code=ts_code,
            start_date=start_date.strftime('%Y%m%d'),
            end_date=end_date.strftime('%Y%m%d')
        )

        if df.empty:
            return pd.DataFrame()

        df = df.rename(columns={
            'trade_date': 'timestamp',
            'vol': 'volume'
        })
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        self._save_cache(ts_code, days, df)
        return df.tail(days)

    def get_realtime(self, ts_code: str) -> dict:
        try:
            df = self.pro.daily_basic(ts_code=ts_code)
            if not df.empty:
                return df.iloc[0].to_dict()
        except:
            pass
        return {}

if __name__ == "__main__":
    client = TushareClient()
    df = client.get_kline("000001.SZ", days=100)
    print(f"获取到 {len(df)} 条K线数据")
    if not df.empty:
        print(df.tail())
