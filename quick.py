#!/usr/bin/env python3
"""专业级快速分析报告 - 联动 V4C 扫描结果版
修复点：彻底解决缩进错误，实现 pool_manager 联动，修复 volume 列缺失崩溃
"""
import sys
import os
import pandas as pd
sys.path.insert(0, '/home/fafa6/auto_trading_system')

from datetime import datetime
from config.settings import config
from data_layer.pool_manager import sync_to_config

# 1. 启动即联动：优先加载扫描结果
has_dynamic_data = sync_to_config()
if not has_dynamic_data:
    # 注意：这里我们不打印太多信息，避免干扰报告头部
    pass

# 2. 导入预测类
try:
    from analysis_layer.kronos_predictor import KronosPredictor
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    sys.exit(1)

class Color:
    RED = '\033[91m'; GREEN = '\033[92m'; YELLOW = '\033[93m'
    WHITE = '\033[97m'; BOLD = '\033[1m'; END = '\033[0m'

def colorize(text, color):
    return f"{color}{text}{Color.END}"

def format_report():
    from data_layer.tushare_client import TushareClient
    client = TushareClient()
    kronos = KronosPredictor()
    now = datetime.now()
    results_data, buy_signals, strong_buy, sell_signals, hold_signals = [], [], [], [], []
    latest_cache_date = None

    # 遍历联动后的股票池
    for stock in config.WATCHLIST:
        ts_code, name = stock['ts_code'], stock['name']
        df = client.get_kline(ts_code, days=120)
        if df is None or len(df) < 50: continue
        
        # 修复 volume 列名问题
        if 'vol' in df.columns and 'volume' not in df.columns:
            df = df.rename(columns={'vol': 'volume'})

        if latest_cache_date is None or df['timestamp'].max() > latest_cache_date:
            latest_cache_date = df['timestamp'].max()
        
        try:
            signal = kronos.predict(df)
            current_price = signal.get('current_price', df['close'].iloc[-1])
            prev_close = df['close'].iloc[-2] if len(df) >= 2 else current_price
            change_pct = (current_price - prev_close) / prev_close * 100
            action, conf = signal['action'], signal['confidence']
            
            if action == 'BUY':
                advice = "强烈关注" if conf >= 0.7 else "适当关注" if conf >= 0.5 else "轻仓试探"
                if conf >= 0.7: strong_buy.append((name, conf, current_price))
                buy_signals.append((name, conf, current_price))
            elif action == 'SELL':
                advice = "减仓观望"
                sell_signals.append((name, conf, current_price))
            else:
                advice = "持有等待"
                hold_signals.append(name)
            results_data.append((ts_code, name, current_price, change_pct, action, conf, advice))
        except Exception as e:
            print(f"❌ 预测 {ts_code} 失败: {e}")

    results_data.sort(key=lambda x: x[5], reverse=True)
    source_name = "动态扫描池" if len(config.WATCHLIST) > 0 and any(s.get('sector') == '动态扫描' for s in config.WATCHLIST) else "预设精选池"
    
    print("\n" + "█" * 80)
    print(f"█  KRONOS 量化交易信号报告 (按置信度排序)")
    print(f"█  生成时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"█  数据截止日期: {latest_cache_date.strftime('%Y-%m-%d') if latest_cache_date else '未知'}")
    print(f"█  分析范围: {source_name} ({len(config.WATCHLIST)}只)")
    print("█" * 80)
    print(f"\n{Color.BOLD}{'代码':<12} {'名称':<10} {'现价':>8} {'涨跌幅':>10} {'信号':>8} {'置信度':>10} {'操作建议':<12}{Color.END}")
    print("-" * 80)
    for ts_code, name, price, change, action, conf, advice in results_data:
        p_col = colorize(f"{change:>+6.2f}%", Color.RED if change > 0 else Color.GREEN if change < 0 else Color.WHITE)
        s_col = colorize("BUY", Color.RED) if action == 'BUY' else colorize("SELL", Color.GREEN) if action == 'SELL' else colorize("HOLD", Color.WHITE)
        c_col = colorize(f"{conf:.1%}", Color.RED if conf >= 0.7 else Color.YELLOW if conf >= 0.4 else Color.WHITE)
        a_col = colorize(advice, Color.RED if '关注' in advice else Color.GREEN if '减仓' in advice else Color.WHITE)
        print(f"{ts_code:<12} {name:<10} {price:>8.2f} {p_col:>12} {s_col:>8} {c_col:>10} {a_col:<12}")
    
    print("-" * 80)
    print(f"\n📊 今日汇总: 总分析 {len(results_data)} 只 | 买入 {len(buy_signals)} | 卖出 {len(sell_signals)}")
    if strong_buy:
        print(f"{colorize('🔥 强烈买入信号 (置信度≥70%):', Color.RED)}")
        for name, conf, price in strong_buy: print(f"   → {name}: {conf:.1%} @ {price:.2f}")
    print("\n" + "█" * 80 + "\n报告生成时间: " + now.strftime('%Y-%m-%d %H:%M:%S') + "\n")

if __name__ == "__main__":
    format_report()
