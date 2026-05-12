#!/usr/bin/env python3
import os
import pandas as pd
from config.settings import config

def get_active_pool():
    """
    统一股票池获取逻辑
    优先级：动态扫描结果 (CSV) > 手动预设池 (config.WATCHLIST)
    """
    dynamic_results_path = 'data/auto_screener_results.csv'
    
    # 1. 优先尝试加载 AutoScreener 的动态结果
    if os.path.exists(dynamic_results_path):
        try:
            df_res = pd.read_csv(dynamic_results_path)
            if not df_res.empty and 'ts_code' in df_res.columns:
                dynamic_list = []
                for _, row in df_res.iterrows():
                    dynamic_list.append({
                        'ts_code': row['ts_code'], 
                        'name': row['name'], 
                        'sector': '动态扫描'
                    })
                return dynamic_list
        except Exception as e:
            print(f"⚠️ 读取动态池失败: {e}")

    # 2. 如果没有动态结果，则返回配置文件中的预设池
    return getattr(config, 'WATCHLIST', [])

def sync_to_config():
    """
    将当前最活跃的股票池同步到内存中的 config.WATCHLIST
    """
    pool = get_active_pool()
    config.WATCHLIST = pool
    return pool
