#!/usr/bin/env python3
"""资金流二次排序：对 V4C 结果按近5日主力净流入重排"""
import time
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
from data_layer.tushare_client import TushareClient
from filter_manager import is_on


def rank_by_moneyflow(df, weight_flow=0.5, weight_momentum=0.5, max_n=200):
    """
    输入：包含 ts_code、momentum 的 DataFrame（V4C 结果）
    输出：加上 net_inflow_5d、flow_score、final_score，按 final_score 降序
    """
    if df is None or df.empty:
        return df
    if not is_on("moneyflow_rank"):
        return df

    pro = TushareClient().pro
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=15)
    start_str = start_dt.strftime('%Y%m%d')
    end_str = end_dt.strftime('%Y%m%d')

    # 只对前 max_n 只做资金流排序，其余保留原顺序附加在后
    head = df.head(max_n).copy()
    tail = df.iloc[max_n:].copy() if len(df) > max_n else None

    inflows = {}
    for code in head['ts_code'].tolist():
        try:
            mf = pro.moneyflow(ts_code=code, start_date=start_str, end_date=end_str)
            if mf is None or mf.empty:
                inflows[code] = 0.0
            else:
                # 取最近5个交易日净流入累计
                mf = mf.sort_values('trade_date', ascending=False).head(5)
                inflows[code] = float(mf['net_mf_amount'].fillna(0).sum())
        except Exception as e:
            logger.debug(f"moneyflow {code} 失败: {e}")
            inflows[code] = 0.0
        time.sleep(0.15)  # 限流

    df = head.copy()
    df['net_inflow_5d'] = df['ts_code'].map(inflows).fillna(0)

    # 归一化：净流入 → 0~1
    vmax, vmin = df['net_inflow_5d'].max(), df['net_inflow_5d'].min()
    if vmax > vmin:
        df['flow_score'] = (df['net_inflow_5d'] - vmin) / (vmax - vmin)
    else:
        df['flow_score'] = 0.5

    # 动量归一化：用 min-max，避免量纲差异
    mmax, mmin = df['momentum'].max(), df['momentum'].min()
    if mmax > mmin:
        df['momentum_score'] = (df['momentum'] - mmin) / (mmax - mmin)
    else:
        df['momentum_score'] = 0.5

    df['final_score'] = weight_flow * df['flow_score'] + weight_momentum * df['momentum_score']
    df = df.sort_values('final_score', ascending=False).reset_index(drop=True)
    if tail is not None and not tail.empty:
        for col in ['net_inflow_5d', 'flow_score', 'momentum_score', 'final_score']:
            tail[col] = 0
        df = pd.concat([df, tail], ignore_index=True)
    return df
