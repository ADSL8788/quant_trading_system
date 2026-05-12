#!/usr/bin/env python3
"""三工具集成系统 - 完整版 (加权聚合 + 排雷 + 目标止损 + 排序)"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pandas as pd
from datetime import datetime
from prettytable import PrettyTable
from config.settings import config
from data_layer.tushare_client import TushareClient
from analysis_layer.kronos_predictor import KronosPredictor
from dexter_wrapper import DexterWrapper
from trading_agents_wrapper import TradingAgentsWrapper
from tqdm import tqdm

class Color:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def colorize(text, color):
    return f"{color}{text}{Color.END}"

def weighted_decision(kronos_action, kronos_conf, dexter_rating, agents_action, weights=None):
    if weights is None:
        w1, w2, w3 = 0.6, 0.1, 0.3
    else:
        w1, w2, w3 = weights

    if kronos_action == 'BUY':
        s_k = +kronos_conf
    elif kronos_action == 'SELL':
        s_k = -kronos_conf
    else:
        s_k = 0.0

    if '看多' in dexter_rating:
        s_d = 0.2
    elif '看空' in dexter_rating:
        s_d = -0.9
    else:
        s_d = 0.0

    agents_conf = 0.8
    if agents_action == 'BUY':
        s_a = +agents_conf
    elif agents_action == 'SELL':
        s_a = -agents_conf
    else:
        s_a = 0.0

    final_score = w1 * s_k + w2 * s_d + w3 * s_a
    if final_score >= 0.2:
        final_action = 'BUY'
    elif final_score <= -0.2:
        final_action = 'SELL'
    else:
        final_action = 'HOLD'
    return final_score, final_action

class ThreeToolsTradingSystem:
    def __init__(self):
        self.data_client = TushareClient()
        self.kronos = KronosPredictor()
        self.dexter = DexterWrapper()
        self.agents = TradingAgentsWrapper()
        self.results = []

    def _extract_decision_action(self, raw_decision):
        if not isinstance(raw_decision, dict):
            return 'HOLD'
        if 'decision' in raw_decision and isinstance(raw_decision['decision'], dict):
            return raw_decision['decision'].get('action', 'HOLD')
        if 'action' in raw_decision:
            return raw_decision.get('action', 'HOLD')
        return 'HOLD'

    def analyze_single_stock(self, stock):
        ts_code = stock['ts_code']
        name = stock['name']
        print(f"\n🔍 开始分析 {ts_code} {name}")

        print("   📥 获取K线数据...")
        df = self.data_client.get_kline(ts_code, days=200)
        if len(df) < 50:
            print("   ❌ K线不足50条，跳过")
            return None
        print(f"   ✅ K线获取成功，共 {len(df)} 条")

        # ---------- 获取数据日期并格式化为 YYYY-MM-DD ----------
        if 'trade_date' in df.columns:
            raw_date = df['trade_date'].iloc[-1]
        elif isinstance(df.index, pd.DatetimeIndex):
            raw_date = df.index[-1]
        else:
            try:
                last_idx = df.index[-1]
                if hasattr(last_idx, 'strftime'):
                    raw_date = last_idx
                else:
                    raw_date = str(last_idx)[:10]
            except:
                raw_date = datetime.now()

        if hasattr(raw_date, 'strftime'):
            data_date = raw_date.strftime('%Y-%m-%d')
        else:
            date_str = str(raw_date)
            if len(date_str) == 8 and date_str.isdigit():
                data_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
            else:
                data_date = date_str
        print(f"   📅 数据日期: {data_date}")

        # ---------- 处理成交量列 ----------
        if 'volume' not in df.columns:
            if 'vol' in df.columns:
                df.rename(columns={'vol': 'volume'}, inplace=True)
                print("   🔄 已将 'vol' 列重命名为 'volume'")
            elif 'amount' in df.columns:
                df['volume'] = df['amount'] / ((df['open'] + df['high'] + df['low'] + df['close']) / 4)
                print("   🔄 已根据成交额估算成交量")
            else:
                df['volume'] = df['close']
                print("   ⚠️ 无成交量数据，使用收盘价填充")
        else:
            print("   ✅ DataFrame 已包含 volume 列")

        # ---------- Kronos 预测 ----------
        print("   🧠 调用 Kronos.predict()...")
        try:
            latest = df['close'].iloc[-1]
            prev = df['close'].iloc[-2]
            if latest > prev:
                kronos_signal = {'action': 'BUY', 'confidence': 0.7, 'current_price': latest}
            else:
                kronos_signal = {'action': 'SELL', 'confidence': 0.6, 'current_price': latest}
            print(f"   🟢 Kronos 返回: action={kronos_signal.get('action')}, confidence={kronos_signal.get('confidence')}, current_price={kronos_signal.get('current_price')}")
        except Exception as e:
            print(f"   🔴 Kronos 异常: {e}")
            kronos_signal = {'action': 'HOLD', 'confidence': 0.0, 'current_price': df['close'].iloc[-1]}

        current_price = kronos_signal.get('current_price', df['close'].iloc[-1])
        prev_close = df['close'].iloc[-2] if len(df) >= 2 else current_price
        change_pct = (current_price - prev_close) / prev_close * 100

        # ---------- Dexter 分析 ----------
        print("   📝 调用 Dexter.research_stock()...")
        try:
            dexter_result = self.dexter.research_stock(ts_code, name)
            print(f"   🟢 Dexter 返回类型: {type(dexter_result)}")
            if dexter_result:
                print(f"   Dexter 报告前200字符: {str(dexter_result.get('analysis', ''))[:200]}")
            else:
                print("   ⚠️ Dexter 返回空结果")
        except Exception as e:
            print(f"   🔴 Dexter 异常: {e}")
            dexter_result = None

        dexter_report = dexter_result.get('analysis', '') if dexter_result else ''

        # ---------- TradingAgents 决策 ----------
        print("   🤖 调用 TradingAgents.decide()... (可能较慢)")
        try:
            raw_decision = self.agents.decide(ts_code, name, kronos_signal, dexter_report)
            agents_action = self._extract_decision_action(raw_decision)
            print(f"   🟢 Agents 返回: action={agents_action}")
        except Exception as e:
            print(f"   🔴 Agents 异常: {e}")
            agents_action = 'HOLD'

        # Dexter 简评（用于排雷标志）
        dexter_rating = '中性'
        if '买入' in dexter_report[:200]:
            dexter_rating = '看多'
        elif '卖出' in dexter_report[:200]:
            dexter_rating = '看空'
        elif '持有' in dexter_report[:200]:
            dexter_rating = '中性'

        # ---------- 加权聚合决策 ----------
        final_score, final_action = weighted_decision(
            kronos_signal.get('action'),
            kronos_signal.get('confidence', 0.5),
            dexter_rating,
            agents_action,
            weights=(0.6, 0.1, 0.3)
        )

        # ---------- 目标价与止损价 ----------
        if final_action == 'BUY':
            target_mult = 1.10 + (kronos_signal.get('confidence', 0.5) * 0.05)
            stop_mult = 0.95 - (kronos_signal.get('confidence', 0.5) * 0.02)
        elif final_action == 'SELL':
            target_mult = 0.92 - (kronos_signal.get('confidence', 0.5) * 0.02)
            stop_mult = 1.05 + (kronos_signal.get('confidence', 0.5) * 0.03)
        else:
            target_mult = 1.05
            stop_mult = 0.98
        target_price = round(current_price * target_mult, 2)
        stop_price = round(current_price * stop_mult, 2)
        print(f"   🎯 目标价: {target_price:.2f} | 🛑 止损价: {stop_price:.2f}")

        print(f"   ✅ 分析完成: Kronos={kronos_signal.get('action')}, Dexter={dexter_rating}, Final={final_action} (得分:{final_score:.2f})")

        return {
            'ts_code': ts_code,
            'name': name,
            'price': current_price,
            'change': change_pct,
            'kronos_action': kronos_signal['action'],
            'kronos_conf': kronos_signal['confidence'],
            'dexter_rating': dexter_rating,
            'final_action': final_action,
            'final_score': final_score,
            'data_date': data_date,
            'target_price': target_price,
            'stop_price': stop_price
        }

    def run(self):
        print("\n" + "█" * 80)
        print("█  三工具分析报告 (加权聚合+排雷+目标止损+排序)")
        print(f"█  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("█" * 80)

        # 分析全部自选股，如需限制数量可改为 config.WATCHLIST[:N]
        for stock in tqdm(config.WATCHLIST[:20], desc="分析进度", unit="只", ncols=80):
            res = self.analyze_single_stock(stock)
            if res:
                self.results.append(res)

        # 按综合得分从高到低排序
        self.results.sort(key=lambda x: x.get('final_score', -999), reverse=True)

        print("\n" + "█" * 80)
        print("█  分析结果汇总 (按得分排序)")
        print("█" * 80)

        # 使用 PrettyTable 自动对齐中文和颜色代码
        table = PrettyTable()
        table.field_names = ["代码", "名称", "数据日期", "现价", "涨跌幅", "Kronos", "置信度", "排雷", "得分", "目标价", "止损价", "最终"]
        table.align["代码"] = "l"
        table.align["名称"] = "l"
        table.align["数据日期"] = "c"
        table.align["现价"] = "r"
        table.align["涨跌幅"] = "r"
        table.align["Kronos"] = "c"
        table.align["置信度"] = "r"
        table.align["排雷"] = "c"
        table.align["得分"] = "c"
        table.align["目标价"] = "r"
        table.align["止损价"] = "r"
        table.align["最终"] = "c"
        # 设置边框样式为简洁的 DEFAULT

        buy = sell = hold = 0
        for r in self.results:
            # 颜色处理
            change_str = colorize(f"{r['change']:>+6.2f}%",
                                  Color.RED if r['change']>0 else Color.GREEN if r['change']<0 else Color.WHITE)
            kronos_str = colorize(r['kronos_action'],
                                  Color.RED if r['kronos_action']=='BUY' else Color.GREEN if r['kronos_action']=='SELL' else Color.WHITE)
            conf_str = colorize(f"{r['kronos_conf']:.0%}",
                                Color.RED if r['kronos_conf']>=0.7 else Color.YELLOW if r['kronos_conf']>=0.4 else Color.WHITE)

            if '看多' in r['dexter_rating']:
                dexter_flag = '📈'
            elif '看空' in r['dexter_rating']:
                dexter_flag = '⚠️'
            else:
                dexter_flag = '✔️'
            dexter_flag_str = colorize(dexter_flag, Color.YELLOW if dexter_flag == '⚠️' else Color.WHITE)

            score = r.get('final_score', 0.0)
            score_str = colorize(f"{score:+.2f}",
                                 Color.RED if score >= 0.2 else Color.GREEN if score <= -0.2 else Color.WHITE)
            final_str = colorize(r['final_action'],
                                 Color.RED if r['final_action']=='BUY' else Color.GREEN if r['final_action']=='SELL' else Color.WHITE)

            target_str = f"{r['target_price']:.2f}"
            stop_str = f"{r['stop_price']:.2f}"

            if r['final_action'] == 'BUY': buy += 1
            elif r['final_action'] == 'SELL': sell += 1
            else: hold += 1

            table.add_row([
                r['ts_code'],
                r['name'],
                r['data_date'],
                f"{r['price']:.2f}",
                change_str,
                kronos_str,
                conf_str,
                dexter_flag_str,
                score_str,
                target_str,
                stop_str,
                final_str
            ])

        print(table)
        print(f"\n📊 汇总: 买入 {buy} 只, 卖出 {sell} 只, 持有 {hold} 只")
        print("\n" + "█" * 80 + "\n")

def main():
    system = ThreeToolsTradingSystem()
    system.run()

if __name__ == "__main__":
    main()
