#!/usr/bin/env python3
"""手工全市场技术扫描 - 多线程加速版（线程数20，默认成分股）"""
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append('/home/fafa6/auto_trading_system')
from data_layer.tushare_client import TushareClient
from config.settings import config
import add_stock

# ========== 配置开关 ==========
USE_FULL_MARKET = True   # False=成分股(快)，True=全市场(慢)
MAX_WORKERS = 20          # 并发线程数（若遇限流请降低至5-8）

SHORT_MA = 20
LONG_MA = 60
MOMENTUM_MIN = 0.03
MOMENTUM_MAX = 0.50
RSI_MIN = 35
RSI_MAX = 65
PULLBACK_MAX = -0.15
VOLATILITY_MIN = 0.02

def calculate_rsi(close, period=14):
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - 100 / (1 + rs)
    return rsi

def analyze_one_stock(ts_code, name):
    try:
        client = TushareClient()
        df = client.get_kline(ts_code, days=250)
        if df is None or len(df) < LONG_MA + 10:
            return None
        close = df['close'].values
        high = df['high'].values
        current_price = close[-1]

        short_ma = np.mean(close[-SHORT_MA:]) if len(close) >= SHORT_MA else 0
        long_ma = np.mean(close[-LONG_MA:]) if len(close) >= LONG_MA else 0
        if short_ma <= long_ma or current_price <= short_ma:
            return None

        if len(close) >= 22:
            momentum = (close[-1] / close[-22]) - 1
        else:
            return None
        if not (MOMENTUM_MIN <= momentum <= MOMENTUM_MAX):
            return None

        if len(close) >= 15:
            rsi = calculate_rsi(pd.Series(close), 14).iloc[-1]
        else:
            return None
        if not (RSI_MIN <= rsi <= RSI_MAX):
            return None

        high_20 = np.max(high[-20:]) if len(high) >= 20 else current_price
        pullback = (current_price - high_20) / high_20
        if pullback <= PULLBACK_MAX:
            return None

        if len(close) >= 20:
            vol = np.std(close[-20:]) / np.mean(close[-20:])
        else:
            return None
        if vol < VOLATILITY_MIN:
            return None

        return {
            'ts_code': ts_code,
            'name': name,
            'momentum': momentum,
            'current_price': current_price,
            'rsi': rsi,
            'pullback': pullback,
            'volatility': vol
        }
    except Exception:
        return None

def get_stock_pool():
    client = TushareClient()
    pro = client.pro

    # ---- 获取最近一个交易日 ----
    today = datetime.now().strftime('%Y%m%d')
    # 从过去30天内找最近的开盘日
    start = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
    trade_cal = pro.trade_cal(exchange='SSE', start_date=start, end_date=today)
    if trade_cal is not None and not trade_cal.empty:
        trade_cal = trade_cal[trade_cal['is_open'] == 1]
        if not trade_cal.empty:
            latest_trade_date = trade_cal['cal_date'].max()
        else:
            latest_trade_date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    else:
        latest_trade_date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
    # ---------------------------------

    if USE_FULL_MARKET:
        stocks = pro.stock_basic(exchange='', list_status='L')
        stocks = stocks[
            (pd.to_datetime(stocks['list_date']) < (datetime.now() - timedelta(days=180))) &
            (~stocks['name'].str.contains('ST|退', case=False, na=False))
        ]
        print(f"📊 全市场股票池: {len(stocks)} 只")
        return [(row['ts_code'], row['name']) for _, row in stocks.iterrows()]
    else:
        # 使用计算出的最近交易日
        hs300 = pro.index_weight(index_code='000300.SH', trade_date=latest_trade_date)
        zz500 = pro.index_weight(index_code='000905.SH', trade_date=latest_trade_date)
        codes = list(set(hs300['con_code'].tolist() + zz500['con_code'].tolist()))
        name_map = {}
        for code in codes:
            basic = pro.stock_basic(ts_code=code, fields='name')
            name_map[code] = basic.iloc[0]['name'] if not basic.empty else code
        print(f"📊 成分股股票池: {len(codes)} 只 (沪深300+中证500, 交易日{latest_trade_date})")
        return [(code, name_map[code]) for code in codes]

def main():
    stock_list = get_stock_pool()
    print(f"🔍 使用 {MAX_WORKERS} 个线程并发扫描...")
    results = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_stock = {executor.submit(analyze_one_stock, code, name): (code, name)
                           for code, name in stock_list}
        with tqdm(total=len(stock_list), desc="扫描进度") as pbar:
            for future in as_completed(future_to_stock):
                res = future.result()
                if res:
                    results.append(res)
                pbar.update(1)

    if not results:
        print("⚠️ 未找到符合条件的股票")
        return

    results_df = pd.DataFrame(results)
    results_df = results_df.sort_values('momentum', ascending=False)
    top_n = 20
    print("\n🏆 Top 20 推荐股票")
    print("=" * 80)
    for i, row in results_df.head(top_n).iterrows():
        print(f"{row['ts_code']:<12} {row['name']:<12} 现价:{row['current_price']:<8.2f} "
              f"动量:{row['momentum']:>6.1%} RSI:{row['rsi']:.0f} "
              f"回撤:{row['pullback']:>6.1%} 波动率:{row['volatility']:.2%}")

    results_df.to_csv('manual_scan_results.csv', index=False, encoding='utf-8-sig')
    print("\n✅ 结果已保存到 manual_scan_results.csv")

    print(f"\n📌 是否将前 {top_n} 只添加到预设池？(y/n): ", end='')
    if input().strip().lower() == 'y':
        added = 0
        for _, row in results_df.head(top_n).iterrows():
            if add_stock.add_stock(row['ts_code'], row['name']):
                added += 1
        print(f"✅ 已添加 {added} 只股票到预设池")

if __name__ == "__main__":
    main()
