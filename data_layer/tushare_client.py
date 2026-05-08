#!/usr/bin/env python3
"""Tushare数据客户端 - 自动增量更新缓存（增加延时防限流）"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
import time
from loguru import logger
from config.settings import config

class TushareClient:
    def __init__(self):
        ts.set_token(config.TUSHARE_TOKEN)
        self.pro = ts.pro_api()
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
        print("✅ Tushare客户端初始化成功")

    def _get_cache_path(self, ts_code, days):
        return os.path.join(self.cache_dir, f"{ts_code}_{days}.parquet")

    def _load_cache(self, ts_code, days):
        path = self._get_cache_path(ts_code, days)
        if os.path.exists(path):
            try:
                df = pd.read_parquet(path)
                if not df.empty and 'timestamp' in df.columns:
                    return df
            except:
                pass
        return None

    def _save_cache(self, ts_code, days, df):
        if df is not None and not df.empty:
            path = self._get_cache_path(ts_code, days)
            df.to_parquet(path, index=False)
            print(f"💾 缓存保存 {ts_code} ({len(df)}条)")

    def _fetch_from_api(self, ts_code, start_date=None, end_date=None):
        """从Tushare下载数据，并增加延时避免频率超限"""
        # 延时 0.15 秒，确保频率低于 400 次/分钟（安全阈值）
        time.sleep(0.15)
        if start_date is None:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=200)
        else:
            end_date = datetime.now() if end_date is None else datetime.strptime(end_date, '%Y%m%d')
        df = self.pro.daily(
            ts_code=ts_code,
            start_date=start_date.strftime('%Y%m%d') if isinstance(start_date, datetime) else start_date,
            end_date=end_date.strftime('%Y%m%d') if isinstance(end_date, datetime) else end_date
        )
        if df.empty:
            return None
        df = df.rename(columns={'trade_date': 'timestamp', 'vol': 'volume'})
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        return df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

    def get_kline(self, ts_code: str, days: int = 120, force_refresh: bool = False) -> pd.DataFrame:
        """
        获取K线数据，自动增量更新
        - 如果无缓存，下载全部数据
        - 如果有缓存，检查最后日期，若早于今天，则下载新数据并合并
        """
        cache_df = self._load_cache(ts_code, days) if not force_refresh else None

        if cache_df is not None and not force_refresh:
            # 检查缓存中最后日期
            last_date = pd.to_datetime(cache_df['timestamp'].max()).date()
            today = datetime.now().date()
            if last_date >= today:
                print(f"✅ 缓存命中 {ts_code} (数据已最新)")
                return cache_df.tail(days)
            else:
                # 需要增量更新
                print(f"🔄 增量更新 {ts_code} (缓存至 {last_date})")
                start_date = (last_date + timedelta(days=1)).strftime('%Y%m%d')
                end_date = today.strftime('%Y%m%d')
                new_df = self._fetch_from_api(ts_code, start_date, end_date)
                if new_df is not None and not new_df.empty:
                    # 合并新旧数据
                    combined = pd.concat([cache_df, new_df], ignore_index=True)
                    combined = combined.drop_duplicates(subset=['timestamp'], keep='last')
                    combined = combined.sort_values('timestamp')
                    self._save_cache(ts_code, days, combined)
                    return combined.tail(days)
                else:
                    # 无新数据，返回缓存
                    print(f"✅ 缓存命中 {ts_code} (无新数据)")
                    return cache_df.tail(days)
        else:
            # 无缓存，下载全部
            print(f"🌐 首次下载 {ts_code}")
            df = self._fetch_from_api(ts_code)
            if df is not None and not df.empty:
                self._save_cache(ts_code, days, df)
                return df.tail(days)
            else:
                return pd.DataFrame()

    def get_realtime(self, ts_code: str) -> dict:
        try:
            df = self.pro.daily_basic(ts_code=ts_code)
            if not df.empty:
                return df.iloc[0].to_dict()
        except:
            pass
        return {}
