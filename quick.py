#!/usr/bin/env python3
"""专业级快速分析报告 - 按置信度排序，显示数据截止日期"""
import sys
sys.path.insert(0, '/home/fafa6/auto_trading_system')

from datetime import datetime
from config.settings import config
from data_layer.tushare_client import TushareClient
from analysis_layer.kronos_predictor import KronosPredictor

class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def colorize(text, color):
    return f"{color}{text}{Color.END}"

def format_report():
    client = TushareClient()
    kronos = KronosPredictor()
    
    now = datetime.now()
    results_data = []
    buy_signals = []
    strong_buy = []
    sell_signals = []
    hold_signals = []
    latest_cache_date = None

    for stock in config.WATCHLIST:
        ts_code = stock['ts_code']
        name = stock['name']
        df = client.get_kline(ts_code, days=120)
        if len(df) < 50:
            continue
        if latest_cache_date is None or df['timestamp'].max() > latest_cache_date:
            latest_cache_date = df['timestamp'].max()
        signal = kronos.predict(df)
        current_price = signal.get('current_price', df['close'].iloc[-1])
        prev_close = df['close'].iloc[-2] if len(df) >= 2 else current_price
        change_pct = (current_price - prev_close) / prev_close * 100
        action = signal['action']
        conf = signal['confidence']
        if action == 'BUY':
            if conf >= 0.7:
                advice = "强烈关注"
                strong_buy.append((name, conf, current_price))
            elif conf >= 0.5:
                advice = "适当关注"
            else:
                advice = "轻仓试探"
            buy_signals.append((name, conf, current_price))
        elif action == 'SELL':
            advice = "减仓观望"
            sell_signals.append((name, conf, current_price))
        else:
            advice = "持有等待"
            hold_signals.append(name)
        results_data.append((ts_code, name, current_price, change_pct, action, conf, advice))

    results_data.sort(key=lambda x: x[5], reverse=True)

    print("\n" + "█" * 80)
    print(f"█  KRONOS 量化交易信号报告 (按置信度排序)")
    print(f"█  生成时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"█  数据截止日期: {latest_cache_date.strftime('%Y-%m-%d') if latest_cache_date else '未知'}")
    print(f"█  分析范围: 预设精选池 ({len(config.WATCHLIST)}只)")
    print("█" * 80)

    print(f"\n{Color.BOLD}{'代码':<12} {'名称':<10} {'现价':>8} {'涨跌幅':>10} {'信号':>8} {'置信度':>10} {'操作建议':<12}{Color.END}")
    print("-" * 80)

    for ts_code, name, price, change, action, conf, advice in results_data:
        if change > 0:
            price_str = colorize(f"{change:>+6.2f}%", Color.RED)
        elif change < 0:
            price_str = colorize(f"{change:>+6.2f}%", Color.GREEN)
        else:
            price_str = colorize(f"{change:>+6.2f}%", Color.WHITE)
        if action == 'BUY':
            signal_str = colorize("BUY", Color.RED)
        elif action == 'SELL':
            signal_str = colorize("SELL", Color.GREEN)
        else:
            signal_str = colorize("HOLD", Color.WHITE)
        if conf >= 0.7:
            conf_str = colorize(f"{conf:.1%}", Color.RED)
        elif conf >= 0.4:
            conf_str = colorize(f"{conf:.1%}", Color.YELLOW)
        else:
            conf_str = colorize(f"{conf:.1%}", Color.WHITE)
        if '关注' in advice:
            advice_str = colorize(advice, Color.RED)
        elif '减仓' in advice:
            advice_str = colorize(advice, Color.GREEN)
        else:
            advice_str = colorize(advice, Color.WHITE)
        print(f"{ts_code:<12} {name:<10} {price:>8.2f} {price_str:>12} {signal_str:>8} {conf_str:>10} {advice_str:<12}")

    print("-" * 80)
    print("\n" + "█" * 80)
    print("█  信号汇总分析")
    print("█" * 80)
    total = len(results_data)
    up_count = len([r for r in results_data if r[3] > 0])
    down_count = len([r for r in results_data if r[3] < 0])
    print(f"\n📊 今日扫描结果:")
    print(f"   总分析: {total} 只")
    print(f"   {colorize(f'🔴 上涨: {up_count} 只', Color.RED)}")
    print(f"   {colorize(f'🟢 下跌: {down_count} 只', Color.GREEN)}")
    print(f"   {colorize(f'📈 买入信号: {len(buy_signals)} 只', Color.RED)}")
    print(f"   {colorize(f'📉 卖出信号: {len(sell_signals)} 只', Color.GREEN)}")
    print(f"   ⚪ 持有信号: {len(hold_signals)} 只")
    if strong_buy:
        print(f"\n{colorize('🔥 强烈买入信号 (置信度≥70%):', Color.RED)}")
        for name, conf, price in strong_buy:
            print(f"   → {name}: {conf:.1%} @ {price:.2f}")
    if sell_signals:
        print(f"\n{colorize('📉 卖出建议:', Color.GREEN)}")
        for name, conf, price in sell_signals[:5]:
            print(f"   → {name}: {conf:.1%} @ {price:.2f}")
    print("\n" + "█" * 80)
    print("█  风险提示")
    print("█" * 80)
    print("   1. 本报告基于历史数据，不构成投资建议")
    print("   2. 置信度低于30%的信号可靠性较低，请谨慎")
    print("   3. 红色代表上涨/买入，绿色代表下跌/卖出")
    print("   4. 市场有风险，投资需谨慎")
    print("█" * 80)
    print(f"\n报告生成时间: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")

if __name__ == "__main__":
    format_report()
