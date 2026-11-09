#!/usr/bin/env python3
"""Tushare数据客户端 - 干净版"""
import os
import time
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
import tushare as ts
from config.settings import config


class TushareClient:
    def __init__(self):
        ts.set_token(config.TUSHARE_TOKEN)
        self.pro = ts.pro_api()
        self.cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)

    def _fetch_from_api(self, ts_code, start_date=None, end_date=None):
        if start_date is None or end_date is None:
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=200)
            start_date = start_dt.strftime('%Y%m%d')
            end_date = end_dt.strftime('%Y%m%d')

        time.sleep(0.15)
        try:
            df = self.pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
        except Exception as e:
            logger.error(f"API Fetch Error {ts_code}: {e}")
            return None

        if df is None or df.empty:
            return None

        for col in ['open', 'high', 'low', 'close', 'vol', 'amount']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        if 'trade_date' in df.columns:
            df['timestamp'] = pd.to_datetime(df['trade_date']).dt.normalize()
            df = df.sort_values('timestamp', ascending=True).reset_index(drop=True)
        return df

    def get_kline(self, ts_code: str, days: int = 500, use_cache: bool = True):
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=days)
        start_str = start_dt.strftime('%Y%m%d')
        end_str = end_dt.strftime('%Y%m%d')

        cache_file = os.path.join(self.cache_dir, f"{ts_code}_{days}.csv")

        if use_cache and os.path.exists(cache_file):
            mtime = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if mtime.date() == end_dt.date():
                try:
                    df = pd.read_csv(cache_file, index_col=0)
                    if 'timestamp' in df.columns:
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
                    if len(df) > days:
                        df = df.tail(days).reset_index(drop=True)
                    return df
                except Exception as e:
                    logger.warning(f"缓存读取失败 {ts_code}: {e}")

        df = self._fetch_from_api(ts_code, start_date=start_str, end_date=end_str)
        if df is not None and not df.empty and use_cache:
            try:
                df.to_csv(cache_file)
            except Exception as e:
                logger.error(f"保存缓存失败 {ts_code}: {e}")
        return df

    def get_kline_batch(self, ts_codes: list, days: int = 500, use_cache: bool = True):
        if not ts_codes:
            return {}
        all_data = {}
        for ts_code in ts_codes:
            try:
                df = self.get_kline(ts_code, days=days, use_cache=use_cache)
                if df is not None and not df.empty:
                    all_data[ts_code] = df
            except Exception as e:
                logger.error(f"获取 {ts_code} 失败: {e}")
        return all_data

    def get_realtime(self, ts_code: str) -> dict:
        try:
            df = self.pro.daily_basic(ts_code=ts_code)
            if not df.empty:
                return df.iloc[0].to_dict()
        except Exception:
            pass
        return {}
