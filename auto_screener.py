#!/usr/bin/env python3
"""
全市场扫描 - V4C量化策略移植版 (V3.0)
移植自 V4C_V6.7 降波动版策略
核心逻辑：趋势 + 动量(3%-50%) + RSI(35-65) + 回撤(<15%) + 波动率(>2%)
"""
import sys
import os
sys.path.insert(0, '/home/fafa6/auto_trading_system')

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from tqdm import tqdm

from config.settings import config
from filter_manager import prompt_filter_switches
from data_layer.tushare_client import TushareClient

class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def colorize(text, color):
    return f"{color}{text}{Color.END}"

class AutoScreener:
    def __init__(self):
        self.client = TushareClient()
        self.pro = self.client.pro

    def get_all_stocks_with_heat(self):
        """获取全市场股票并基于热度初步筛选"""
        try:
            stocks = self.pro.stock_basic(exchange='', list_status='L')
        except Exception as e:
            print(f"❌ 无法获取股票基础信息: {e}")
            return pd.DataFrame()

        cutoff_date = (datetime.now() - timedelta(days=180)).strftime('%Y%m%d')
        stocks = stocks[
            (stocks['list_date'] < cutoff_date) &
            (~stocks['name'].str.contains('ST|退', case=False, na=False)) &
            (stocks['market'].isin(['主板', '创业板', '科创板']))
        ].copy()

        print(f"✅ 初始股票池: {len(stocks)} 只")

        latest_trade_date = (datetime.now() - timedelta(days=1)).strftime('%Y%m%d')
        try:
            daily_basic = self.pro.daily_basic(trade_date=latest_trade_date,
                                               fields='ts_code,turnover_rate,total_mv')
        except Exception as e:
            daily_basic = pd.DataFrame()

        if daily_basic.empty:
            stocks['heat'] = 0
            return stocks

        stocks = stocks.merge(daily_basic, on='ts_code', how='left')
        stocks['turnover_rate'] = stocks['turnover_rate'].fillna(0)
        stocks['total_mv'] = stocks['total_mv'].fillna(0)

        def normalize(series):
            if series.max() == series.min(): return 0
            return (series - series.min()) / (series.max() - series.min())

        stocks['turn_score'] = normalize(stocks['turnover_rate'])
        stocks['mv_score'] = 1 - normalize(stocks['total_mv'])
        stocks['heat'] = stocks['turn_score'] * 0.7 + stocks['mv_score'] * 0.3
        stocks = stocks.sort_values('heat', ascending=False)
        return stocks

    def _analyze_single_stock(self, ts_code, name, df):
        """
        分析单只股票的数据（df 是已获取的 K 线 DataFrame）
        移植自 V4C_V6.7 的核心买入逻辑
        """
        try:
            if df is None or len(df) < 60:
                return None

            df = df.sort_values(by='timestamp', ascending=True).reset_index(drop=True)
            close = df['close'].values.astype(float)
            high = df['high'].values.astype(float)
            vol_col = 'vol' if 'vol' in df.columns else 'volume'
            volume = df[vol_col].values.astype(float)
            last_date = df['timestamp'].iloc[-1].strftime('%Y-%m-%d')

            # --- 指标计算 ---
            ma20 = np.mean(close[-20:])
            ma60 = np.mean(close[-60:])
            current_price = close[-1]

            momentum = (close[-1] / close[-20]) - 1 if len(close) >= 20 else 0

            # RSI (14日)
            rsi = 50
            if len(close) >= 15:
                delta = np.diff(close[-15:])
                ups = delta[delta > 0].sum() if any(delta > 0) else 0
                downs = abs(delta[delta < 0].sum()) if any(delta < 0) else 0.001
                rs = ups / downs
                rsi = 100 - (100 / (1 + rs))

            # 回撤
            high_20 = np.max(high[-20:])
            pullback = (current_price - high_20) / high_20

            # 波动率
            volatility = np.std(close[-20:]) / np.mean(close[-20:])

            # V4C_V6.7 硬性过滤
            if not (current_price > ma20 and ma20 > ma60):
                return None
            if momentum < 0.03 or momentum > 0.50:
                return None
            if rsi < 35 or rsi > 65:
                return None
            if pullback < -0.15:
                return None
            if volatility < 0.02:
                return None

            # ---- 可插拔过滤规则（Y/N 开关，config/filters.json）----
            from filter_manager import is_on
            vol_ratio_val = np.mean(volume[-5:]) / np.mean(volume[-20:])

            if is_on("yearline_filter") and len(close) >= 250:
                if current_price < np.mean(close[-250:]):
                    return None
            if is_on("rsi_upper_filter") and rsi > 70:
                return None
            if is_on("pullback_filter") and pullback < -0.15:
                return None
            if is_on("volume_filter") and vol_ratio_val < 0.8:
                return None

            score_val = momentum * 100
            if is_on("crowding_filter") and momentum > 0.40:
                score_val *= 0.8
            # ---- 规则结束 ----

            return {
                'scan_date': datetime.now().strftime('%Y-%m-%d'),
                'last_date': last_date,
                'ts_code': ts_code,
                'name': name,
                'close': round(current_price, 2),
                'momentum': round(momentum, 4),
                'ma20': round(ma20, 2),
                'ma60': round(ma60, 2),
                'volume_ratio': round(vol_ratio_val, 2),
                'rsi': round(rsi, 1),
                'volatility': round(volatility, 4),
                'pullback': round(pullback * 100, 2),
                'score': score_val,
                'exp_change': round(momentum * 100, 1)
            }
        except Exception:
            return None

    def quick_technical_filter(self, stocks_df, top_n=2000):
        """批量技术筛选（不再使用多线程，改为批量API请求）"""
        print(f"\n📈 正在执行 V4C 精准量化筛选（分析前 {top_n} 只）")
        target_stocks = stocks_df.head(top_n).copy()
        stock_codes = target_stocks['ts_code'].tolist()
        stock_names = dict(zip(target_stocks['ts_code'], target_stocks['name']))

        # 批量获取 K 线数据（120天改到800天）
        print("⏳ 批量获取K线数据...")
        all_data = self.client.get_kline_batch(stock_codes, days=800)
        print(f"✅ 成功获取 {len(all_data)} 只股票数据")

        results = []
        # 逐个分析
        for ts_code, df in tqdm(all_data.items(), desc="量化过滤中", ncols=80):
            name = stock_names.get(ts_code, '')
            res = self._analyze_single_stock(ts_code, name, df)
            if res:
                results.append(res)

        result_df = pd.DataFrame(results)
        if not result_df.empty:
            result_df = result_df.sort_values(by='momentum', ascending=False)
        print(f"✅ 量化筛选通过: {len(result_df)} 只")
        return result_df

    def scan_and_select(self, top_n=20):
        stocks_with_heat = self.get_all_stocks_with_heat()
        tech_ok = self.quick_technical_filter(stocks_with_heat, top_n=2000)
        if tech_ok.empty:
            return tech_ok
        # 资金流二次排序（可通过 flt 开关 moneyflow_rank 关闭）
        from moneyflow_rank import rank_by_moneyflow
        tech_ok = rank_by_moneyflow(tech_ok, weight_flow=0.5, weight_momentum=0.5)
        return tech_ok.head(top_n)

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--full', action='store_true', help='全量扫描所有股票')
    parser.add_argument('-y', '--yes', action='store_true', help='自动添加Top20到手动池')
    parser.add_argument('--no-filter-prompt', action='store_true', help='跳过开关提示（自动化用）')
    args = parser.parse_args()

    if not args.no_filter_prompt:
        try:
            prompt_filter_switches()
        except (EOFError, KeyboardInterrupt):
            print("→ 跳过开关调整，使用当前状态\n")

    screener = AutoScreener()
    if args.full:
        all_stocks = screener.get_all_stocks_with_heat()
        tech_ok = screener.quick_technical_filter(all_stocks, top_n=len(all_stocks))
        results = tech_ok.head(20)
    else:
        results = screener.scan_and_select(top_n=20)

    if results.empty:
        print(colorize("❌ 没有符合 V4C 严苛条件的股票", Color.RED))
        return

    print("\n🏆 Top 20 精选个股 (V4C 量化排序)")
    print("="*100)
    for i, row in results.reset_index(drop=True).iterrows():
        status = colorize("极强趋势", Color.RED) if row['momentum'] > 0.1 else \
                 colorize("稳定上涨", Color.YELLOW) if row['momentum'] > 0.05 else \
                 colorize("趋势初现", Color.WHITE)
        momentum_str = colorize(f"{row['momentum']:+.1%}", Color.RED)
        print(f"{i+1}. {row['name']} ({row['ts_code']}) 日期:{row['last_date']} "
              f"收盘:{row['close']:.2f} 动量:{momentum_str} RSI:{row['rsi']:.0f} 回撤:{row['pullback']:.1f}% {status}")

    # 保存详细 K 线数据（批量获取1000天数据）
    print("\n💾 正在同步详细 K 线数据到 data 目录 (极限清洗模式)...")
    os.makedirs('data', exist_ok=True)

    stock_codes = results['ts_code'].tolist()
    # 批量获取 1000 天数据
    all_detail_data = screener.client.get_kline_batch(stock_codes, days=1000)

    success_count = 0
    for ts_code, df_detail in all_detail_data.items():
        try:
            if df_detail is None or df_detail.empty:
                continue

            if 'timestamp' in df_detail.columns and 'trade_date' in df_detail.columns:
                df_detail = df_detail.drop(columns=['trade_date'])

            rename_map = {'timestamp': 'date', 'vol': 'volume', 'amount': 'amount'}
            df_detail = df_detail.rename(columns=rename_map)

            if 'date' in df_detail.columns:
                df_detail['date'] = pd.to_datetime(df_detail['date'], errors='coerce')
                df_detail = df_detail.dropna(subset=['date'])
                now = pd.Timestamp(datetime.now())
                df_detail = df_detail[df_detail['date'] <= now]
                df_detail = df_detail.drop_duplicates(subset=['date'], keep='last')
                df_detail = df_detail.sort_values(by='date', ascending=True).reset_index(drop=True)
                df_detail['date'] = df_detail['date'].dt.strftime('%Y-%m-%d')

            required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
            existing_cols = [col for col in required_cols if col in df_detail.columns]
            df_detail = df_detail[existing_cols].copy()
            for col in required_cols:
                if col not in df_detail.columns:
                    df_detail[col] = np.nan
            df_detail = df_detail[required_cols]
            df_detail = df_detail.ffill().bfill().dropna()

            file_path = f'data/{ts_code}.csv'
            df_detail.to_csv(file_path, index=False, encoding='utf-8')
            success_count += 1
        except Exception as e:
            print(f"❌ 保存 {ts_code} 失败: {e}")

    print(f"✅ 已成功导出 {success_count} 只个股标准化 K 线文件")
    results.to_csv('data/auto_screener_results.csv', index=False, encoding='utf-8')

    # 交互式添加到预设池（支持 -y）
    if not args.full:
        if args.yes:
            choice = 'y'
        else:
            print("\n📌 是否将本次选股结果（Top20）添加到预设池？(y/n): ", end='')
            choice = input().strip().lower()
        if choice == 'y':
            import add_stock
            added = 0
            for _, row in results.iterrows():
                if add_stock.add_stock(row['ts_code'], row['name'], sector='自动筛选'):
                    added += 1
            print(f"✅ 已将 {added} 只股票添加到手动池")

    print(f"\n✅ 详细汇总结果已保存到 data/auto_screener_results.csv")

if __name__ == "__main__":
    main()
