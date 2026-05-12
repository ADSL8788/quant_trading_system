#!/usr/bin/env python3
"""实盘模拟系统 - 资金管理 + 模拟交易"""
import sys
import os
sys.path.insert(0, '/home/fafa6/auto_trading_system')

import json
import time
from datetime import datetime, timedelta
from loguru import logger
import pandas as pd

from config.settings import config
from data_layer.tushare_client import TushareClient
from analysis_layer.kronos_predictor import KronosPredictor
from dexter_wrapper import DexterWrapper
from trading_agents_wrapper import TradingAgentsWrapper

class PortfolioManager:
    """投资组合管理器"""
    
    def __init__(self, initial_capital=1000000):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}  # {ts_code: {'shares': 100, 'buy_price': 10.5, 'buy_date': '2025-01-01', 'sector': '消费'}}
        self.trade_history = []
        self.daily_values = []
        
    def get_total_value(self, data_client):
        """获取总资产"""
        position_value = 0
        for ts_code, pos in self.positions.items():
            df = data_client.get_kline(ts_code, days=5)
            if not df.empty:
                current = df['close'].iloc[-1]
                position_value += pos['shares'] * current
        return self.cash + position_value
    
    def can_buy(self, ts_code, price, sector, amount):
        """检查是否可以买入"""
        # 1. 资金检查
        if amount > self.cash:
            return False, "资金不足"
        
        # 2. 单只股票仓位限制
        total_value = self.get_total_value(None)  # 需要传入client
        if amount / total_value > config.MAX_SINGLE_POSITION:
            return False, f"超过单票仓位限制({config.MAX_SINGLE_POSITION:.0%})"
        
        # 3. 板块仓位限制
        sector_value = 0
        for p in self.positions.values():
            if p.get('sector') == sector:
                sector_value += p['shares'] * price
        if (sector_value + amount) / total_value > config.MAX_SECTOR_POSITION:
            return False, f"超过板块仓位限制({config.MAX_SECTOR_POSITION:.0%})"
        
        return True, "通过"
    
    def buy(self, ts_code, name, price, sector, shares=None):
        """买入"""
        amount = shares * price if shares else price * 100
        can_buy, reason = self.can_buy(ts_code, price, sector, amount)
        
        if not can_buy:
            logger.warning(f"  买入失败: {reason}")
            return False
        
        if shares is None:
            # 根据资金自动计算股数
            max_amount = self.cash * config.MAX_SINGLE_POSITION
            shares = int(max_amount / price / 100) * 100
        
        if shares < 100:
            logger.warning(f"  买入失败: 股数不足100")
            return False
        
        cost = shares * price * 1.0003  # 加手续费
        self.cash -= cost
        
        self.positions[ts_code] = {
            'name': name,
            'shares': shares,
            'buy_price': price,
            'buy_date': datetime.now().strftime('%Y-%m-%d'),
            'sector': sector,
            'value': cost
        }
        
        self.trade_history.append({
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'action': 'BUY',
            'ts_code': ts_code,
            'name': name,
            'shares': shares,
            'price': price,
            'value': cost
        })
        
        logger.info(f"  ✅ 买入 {name}: {shares}股 @ {price:.2f} (成本:{cost:.0f})")
        return True
    
    def sell(self, ts_code, price, reason):
        """卖出"""
        if ts_code not in self.positions:
            return False
        
        pos = self.positions[ts_code]
        revenue = pos['shares'] * price * 0.9997  # 扣手续费
        pnl = (price - pos['buy_price']) / pos['buy_price']
        
        self.cash += revenue
        
        self.trade_history.append({
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'action': 'SELL',
            'ts_code': ts_code,
            'name': pos['name'],
            'shares': pos['shares'],
            'price': price,
            'value': revenue,
            'pnl': pnl,
            'reason': reason
        })
        
        logger.info(f"  ✅ 卖出 {pos['name']}: {pos['shares']}股 @ {price:.2f} "
                   f"(盈亏:{pnl:+.2%}, 理由:{reason})")
        
        del self.positions[ts_code]
        return True
    
    def check_positions(self, data_client):
        """检查持仓，触发止损止盈"""
        to_sell = []
        
        for ts_code, pos in self.positions.items():
            df = data_client.get_kline(ts_code, days=5)
            if df.empty:
                continue
            
            current = df['close'].iloc[-1]
            pnl = (current - pos['buy_price']) / pos['buy_price']
            
            if pnl <= -config.STOP_LOSS:
                to_sell.append((ts_code, current, f"止损({pnl:.1%})"))
            elif pnl >= config.TAKE_PROFIT:
                to_sell.append((ts_code, current, f"止盈({pnl:.1%})"))
        
        for ts_code, price, reason in to_sell:
            self.sell(ts_code, price, reason)
        
        return len(to_sell)
    
    def get_summary(self, data_client):
        """获取组合摘要"""
        total_value = self.get_total_value(data_client)
        total_return = (total_value - self.initial_capital) / self.initial_capital
        
        return {
            'cash': self.cash,
            'total_value': total_value,
            'total_return': total_return,
            'positions_count': len(self.positions),
            'trade_count': len(self.trade_history)
        }

class FullLiveSimulator:
    """完整实盘模拟器"""
    
    def __init__(self):
        self.data_client = TushareClient()
        self.kronos = KronosPredictor()
        self.dexter = DexterWrapper()
        self.agents = TradingAgentsWrapper()
        self.portfolio = PortfolioManager(config.INITIAL_CAPITAL)
        
        logger.info("=" * 60)
        logger.info("💰 实盘模拟系统启动")
        logger.info(f"初始资金: {config.INITIAL_CAPITAL:,.0f}")
        logger.info(f"股票池: {len(config.WATCHLIST)} 只")
        logger.info("=" * 60)
    
    def analyze_and_trade(self, stock):
        """分析单只股票并执行交易"""
        ts_code = stock['ts_code']
        name = stock['name']
        sector = stock.get('sector', '其他')
        
        # 检查是否已持仓
        if ts_code in self.portfolio.positions:
            return None
        
        # Kronos 分析
        df = self.data_client.get_kline(ts_code, days=200)
        if len(df) < 50:
            return None
        
        signal = self.kronos.predict(df)
        current_price = signal.get('current_price', df['close'].iloc[-1])
        
        # 置信度过低不交易
        if signal['confidence'] < 0.25:
            return None
        
        # Dexter 研究
        dexter_result = self.dexter.research_stock(ts_code, name)
        dexter_report = dexter_result.get('analysis', '') if dexter_result.get('success') else ''
        
        # 多智能体决策
        decision = self.agents.decide(ts_code, name, signal, dexter_report)
        
        if decision.get('action') == 'BUY':
            self.portfolio.buy(ts_code, name, current_price, sector)
            return decision
        
        return None
    
    def run_daily(self):
        """每日运行"""
        today = datetime.now().strftime('%Y-%m-%d')
        logger.info(f"\n{'='*60}")
        logger.info(f"📅 交易日: {today}")
        logger.info(f"{'='*60}")
        
        # 1. 检查现有持仓（止损止盈）
        sold_count = self.portfolio.check_positions(self.data_client)
        if sold_count > 0:
            logger.info(f"🔄 执行了 {sold_count} 笔卖出")
        
        # 2. 分析新机会
        buy_count = 0
        for stock in config.WATCHLIST:
            result = self.analyze_and_trade(stock)
            if result:
                buy_count += 1
        
        if buy_count > 0:
            logger.info(f"📈 执行了 {buy_count} 笔买入")
        
        # 3. 输出组合摘要
        summary = self.portfolio.get_summary(self.data_client)
        
        logger.info(f"\n📊 组合摘要:")
        logger.info(f"   总资产: {summary['total_value']:,.0f}")
        logger.info(f"   现金: {summary['cash']:,.0f}")
        logger.info(f"   持仓数: {summary['positions_count']}")
        logger.info(f"   累计交易: {summary['trade_count']}")
        logger.info(f"   总收益: {summary['total_return']:+.2%}")
        
        return summary
    
    def run_backtest(self, days=30):
        """运行回测（模拟过去N天）"""
        logger.info(f"开始回测最近 {days} 天...")
        
        for day in range(days):
            self.run_daily()
            time.sleep(0.5)  # 避免API限流
        
        final_summary = self.portfolio.get_summary(self.data_client)
        
        logger.info("\n" + "=" * 60)
        logger.info("🎯 回测完成")
        logger.info(f"最终总资产: {final_summary['total_value']:,.0f}")
        logger.info(f"总收益率: {final_summary['total_return']:+.2%}")
        logger.info("=" * 60)
        
        return final_summary

def main():
from data_layer.pool_manager import sync_to_config
    config.WATCHLIST = sync_to_config()

    simulator = FullLiveSimulator()
    
    # 运行一次完整的分析（不实际交易，仅演示）
    logger.info("\n🔍 演示模式: 分析市场，不实际交易\n")
    
    for stock in config.WATCHLIST[:10]:  # 先分析前10只
        df = simulator.data_client.get_kline(stock['ts_code'], days=100)
        if len(df) >= 50:
            signal = simulator.kronos.predict(df)
            logger.info(f"{stock['name']:6s}: {signal['action']} "
                       f"(置信度:{signal['confidence']:.1%}, {signal.get('current_price', 0):.2f})")

if __name__ == "__main__":
    main()
