#!/usr/bin/env python3
"""三工具集成系统 - 极简进度条版"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
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

class ThreeToolsTradingSystem:
    def __init__(self):
        self.data_client = TushareClient()
        self.kronos = KronosPredictor()
        self.dexter = DexterWrapper()
        self.agents = TradingAgentsWrapper()
        self.results = []
    
    def analyze_single_stock(self, stock):
        ts_code = stock['ts_code']
        name = stock['name']
        
        # Kronos
        df = self.data_client.get_kline(ts_code, days=200)
        if len(df) < 50:
            return None
        kronos_signal = self.kronos.predict(df)
        current_price = kronos_signal.get('current_price', df['close'].iloc[-1])
        prev_close = df['close'].iloc[-2] if len(df) >= 2 else current_price
        change_pct = (current_price - prev_close) / prev_close * 100
        
        # Dexter
        dexter_result = self.dexter.research_stock(ts_code, name)
        dexter_report = dexter_result.get('analysis', '') if dexter_result else ''
        
        # TradingAgents
        decision = self.agents.decide(ts_code, name, kronos_signal, dexter_report)
        
        # Dexter 简评
        dexter_rating = '中性'
        if '买入' in dexter_report[:200]:
            dexter_rating = '看多'
        elif '卖出' in dexter_report[:200]:
            dexter_rating = '看空'
        elif '持有' in dexter_report[:200]:
            dexter_rating = '中性'
        
        return {
            'ts_code': ts_code, 'name': name, 'price': current_price, 'change': change_pct,
            'kronos_action': kronos_signal['action'], 'kronos_conf': kronos_signal['confidence'],
            'dexter_rating': dexter_rating, 'final_action': decision.get('action', 'HOLD')
        }
    
    def run(self):
        print("\n" + "█" * 80)
        print("█  完整三工具分析报告 (进度条版)")
        print(f"█  生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("█" * 80)
        
        # 进度条
        for stock in tqdm(config.WATCHLIST, desc="分析进度", unit="只", ncols=80):
            res = self.analyze_single_stock(stock)
            if res:
                self.results.append(res)
        
        # 表格输出
        print("\n" + "█" * 80)
        print("█  分析结果汇总")
        print("█" * 80)
        print(f"\n{Color.BOLD}{'代码':<12} {'名称':<10} {'现价':>8} {'涨跌幅':>10} "
              f"{'Kronos':^10} {'置信度':>8} {'Dexter':^6} {'最终':^6}{Color.END}")
        print("-" * 80)
        
        buy = sell = hold = 0
        for r in self.results:
            change_str = colorize(f"{r['change']:>+6.2f}%", 
                                  Color.RED if r['change']>0 else Color.GREEN if r['change']<0 else Color.WHITE)
            kronos_str = colorize(r['kronos_action'], 
                                  Color.RED if r['kronos_action']=='BUY' else Color.GREEN if r['kronos_action']=='SELL' else Color.WHITE)
            conf_str = colorize(f"{r['kronos_conf']:.0%}", 
                                Color.RED if r['kronos_conf']>=0.7 else Color.YELLOW if r['kronos_conf']>=0.4 else Color.WHITE)
            dex_str = colorize(r['dexter_rating'], 
                               Color.RED if '看多' in r['dexter_rating'] else Color.GREEN if '看空' in r['dexter_rating'] else Color.WHITE)
            final_str = colorize(r['final_action'], 
                                 Color.RED if r['final_action']=='BUY' else Color.GREEN if r['final_action']=='SELL' else Color.WHITE)
            if r['final_action'] == 'BUY': buy += 1
            elif r['final_action'] == 'SELL': sell += 1
            else: hold += 1
            
            print(f"{r['ts_code']:<12} {r['name']:<10} {r['price']:>8.2f} {change_str:>12} "
                  f"{kronos_str:^8} {conf_str:>10} {dex_str:^8} {final_str:^8}")
        
        print("-" * 80)
        print(f"\n📊 汇总: 买入 {buy} 只, 卖出 {sell} 只, 持有 {hold} 只")
        print("\n" + "█" * 80 + "\n")

def main():
    system = ThreeToolsTradingSystem()
    system.run()

if __name__ == "__main__":
    main()
