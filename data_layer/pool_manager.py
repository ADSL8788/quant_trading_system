#!/usr/bin/env python3
import os
import pandas as pd
from config.settings import config

def get_active_pool():
    """
    合并股票池：动态扫描结果 + 手动池，按 ts_code 去重
    手动池优先保留（保留其原始 sector 信息）
    """
    dynamic_results_path = 'data/auto_screener_results.csv'
    dynamic_list = []

    if os.path.exists(dynamic_results_path):
        try:
            df_res = pd.read_csv(dynamic_results_path)
            if not df_res.empty and 'ts_code' in df_res.columns:
                for _, row in df_res.iterrows():
                    dynamic_list.append({
                        'ts_code': row['ts_code'],
                        'name': row['name'],
                        'sector': '动态扫描'
                    })
        except Exception as e:
            print(f"⚠️ 读取动态池失败: {e}")

    # 手动池：优先取 EXTRA_STOCKS；没有则从 WATCHLIST 里排除“动态扫描”
    manual = getattr(config, 'EXTRA_STOCKS', [])
    if not manual:
        manual = [s for s in getattr(config, 'WATCHLIST', []) if s.get('sector') != '动态扫描']

    # 合并去重（手动池在前，动态扫描在后）
    seen = set()
    merged = []
    for s in manual + dynamic_list:
        code = s.get('ts_code')
        if code and code not in seen:
            seen.add(code)
            merged.append(s)
    return merged

def sync_to_config():
    """
    将合并后的股票池同步到 config.WATCHLIST
    """
    pool = get_active_pool()
    config.WATCHLIST = pool
    return bool(pool)
