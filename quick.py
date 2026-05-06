#!/usr/bin/env python3
"""专业级快速分析报告 - 支持代码/名称混合"""
import sys
sys.path.insert(0, '/home/fafa6/auto_trading_system')

from datetime import datetime
from config.settings import config
from data_layer.tushare_client import TushareClient
from analysis_layer.kronos_predictor import KronosPredictor

# ANSI颜色代码
class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def colorize(text, color):
    return f"{color}{text}{Color.END}"

def format_stock_code(code):
    """自动补全市场后缀"""
    code = code.upper().strip()
    if '.' in code:
        return code
    if code.startswith(('60', '68')):
        return f"{code}.SH"
    else:
        return f"{code}.SZ"

def build_name_to_code():
    """构建股票名称到代码的映射（从预设池）"""
    mapping = {}
    for stock in config.WATCHLIST:
        mapping[stock['name']] = stock['ts_code']
    return mapping

def resolve_stock(param, name_to_code):
    """解析参数：返回 (ts_code, name)"""
    # 先尝试作为名称匹配
    if param in name_to_code:
        ts_code = name_to_code[param]
        return ts_code, param
    # 否则当作代码处理
    ts_code = format_stock_code(param)
    # 尝试从预设池获取名称，否则用代码作为名称
    name = ts_code
    for stock in config.WATCHLIST:
        if stock['ts_code'] == ts_code:
            name = stock['name']
            break
    return ts_code, name

def get_stocks_to_analyze():
    """根据命令行参数确定要分析的股票列表"""
    args = sys.argv[1:]
    name_to_code = build_name_to_code()
    if not args:
        # 无参数：分析预设池全部
        return config.WATCHLIST
    
    stocks = []
    for arg in args:
        ts_code, name = resolve_stock(arg, name_to_code)
        stocks.append({'ts_code': ts_code, 'name': name, 'sector': '指定'})
    return stocks

def format_report():
    client = TushareClient()
    kronos = KronosPredictor()
    now = datetime.now()
    stocks = get_stocks_to_analyze()

    print("\n" + "█" * 80)
    print(f"█  KRONOS 量化交易信号报告")
    print(f"█  生成时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    if len(sys.argv) == 1:
        print(f"█  分析范围: 预设精选池 ({len(stocks)}只)")
    else:
        print(f"█  分析范围: 指定股票 ({len(stocks)}只)")
    print("█" * 80)

    buy_signals = []
    strong_buy = []
    sell_signals = []
    hold_signals = []
    results_data = []

    header = (f"{Color.BOLD}{'代码':<12} {'名称':<8} {'现价':>8} {'涨跌幅':>10} "
              f"{'信号':>8} {'置信度':>10} {'操作建议':<12}{Color.END}")
    print(header)
    print("-" * 80)

    for stock in stocks:
        ts_code = stock['ts_code']
        name = stock['name']
        df = client.get_kline(ts_code, days=120)
        if len(df) < 50:
            print(f"{ts_code:<12} {name:<8} {'数据不足':>20}")
            continue

        signal = kronos.predict(df)
        current_price = signal.get('current_price', df['close'].iloc[-1])
        prev_close = df['close'].iloc[-2] if len(df) >= 2 else current_price
        change_pct = (current_price - prev_close) / prev_close * 100

        if change_pct > 0:
            price_str = colorize(f"{change_pct:>+6.2f}%", Color.RED)
        elif change_pct < 0:
            price_str = colorize(f"{change_pct:>+6.2f}%", Color.GREEN)
        else:
            price_str = colorize(f"{change_pct:>+6.2f}%", Color.WHITE)

        action = signal['action']
        conf = signal['confidence']
        if action == 'BUY':
            if conf >= 0.7:
                signal_str = colorize("🔴买入", Color.RED)
                advice_str = colorize("强烈关注", Color.RED)
                strong_buy.append((name, conf, current_price))
            elif conf >= 0.5:
                signal_str = colorize("🔴买入", Color.RED)
                advice_str = colorize("适当关注", Color.RED)
            else:
                signal_str = colorize("🟡买入", Color.YELLOW)
                advice_str = colorize("轻仓试探", Color.YELLOW)
            buy_signals.append((name, conf, current_price))
        elif action == 'SELL':
            signal_str = colorize("🟢卖出", Color.GREEN)
            advice_str = colorize("减仓观望", Color.GREEN)
            sell_signals.append((name, conf, current_price))
        else:
            signal_str = colorize("⚪持有", Color.WHITE)
            advice_str = colorize("持有等待", Color.WHITE)
            hold_signals.append(name)

        if conf >= 0.7:
            conf_str = colorize(f"{conf:.1%}", Color.RED)
        elif conf >= 0.4:
            conf_str = colorize(f"{conf:.1%}", Color.YELLOW)
        else:
            conf_str = colorize(f"{conf:.1%}", Color.WHITE)

        line = (f"{ts_code:<12} {name:<8} {current_price:>8.2f} {price_str:>12} "
                f"{signal_str:>8} {conf_str:>10} {advice_str:<12}")
        print(line)
        results_data.append((name, change_pct, action, conf))

    print("-" * 80)
    print("\n" + "█" * 80)
    print("█  信号汇总分析")
    print("█" * 80)

    total = len(buy_signals) + len(sell_signals) + len(hold_signals)
    up_count = len([r for r in results_data if r[1] > 0])
    down_count = len([r for r in results_data if r[1] < 0])

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
    print(f"""   {Color.YELLOW}1. 本报告基于历史数据，不构成投资建议{Color.END}
   {Color.YELLOW}2. 置信度低于30%的信号可靠性较低，请谨慎{Color.END}
   {Color.YELLOW}3. {Color.RED}红色代表上涨/买入{Color.END}，{Color.GREEN}绿色代表下跌/卖出{Color.END}
   {Color.YELLOW}4. 市场有风险，投资需谨慎{Color.END}""")
    print("█" * 80)
    print(f"\n报告生成时间: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")

if __name__ == "__main__":
    format_report()
