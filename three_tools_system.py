#!/usr/bin/env python3
"""三工具集成系统 - 优化版"""
import sys
import os
import json
from datetime import datetime
from loguru import logger

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import config
from data_layer.tushare_client import TushareClient
from analysis_layer.kronos_predictor import KronosPredictor
from dexter_wrapper import DexterWrapper
from trading_agents_wrapper import TradingAgentsWrapper

class ThreeToolsTradingSystem:
    def __init__(self):
        logger.info("=" * 60)
        logger.info("初始化三工具集成交易系统 (优化版)")
        logger.info("=" * 60)
        
        self.data_client = TushareClient()
        self.kronos = KronosPredictor()
        self.dexter = DexterWrapper()
        self.trading_agents = TradingAgentsWrapper(llm_provider="deepseek")
        
        # 交易状态
        self.cash = config.INITIAL_CAPITAL
        self.positions = {}
        
        logger.info("✅ 所有工具初始化完成")
    
    def analyze_single_stock(self, stock):
        ts_code = stock['ts_code']
        name = stock['name']
        
        logger.info(f"\n{'='*50}")
        logger.info(f"🔍 联合分析: {name} ({ts_code})")
        logger.info(f"{'='*50}")
        
        result = {
            "ts_code": ts_code,
            "name": name,
            "timestamp": datetime.now().isoformat(),
            "kronos": None,
            "dexter": None,
            "final_decision": None
        }
        
        # Step 1: Kronos 技术预测
        logger.info("📈 [1/3] Kronos 技术分析...")
        df = self.data_client.get_kline(ts_code, days=200)
        if len(df) >= 50:
            kronos_signal = self.kronos.predict(df)
            result["kronos"] = kronos_signal
            logger.info(f"   信号: {kronos_signal['action']}, 置信度: {kronos_signal['confidence']:.1%}")
        else:
            logger.warning(f"   数据不足")
            return None
        
        # Step 2: Dexter 深度研究 (使用 DeepSeek 模拟)
        logger.info("📚 [2/3] Dexter 深度研究...")
        try:
            dexter_result = self.dexter.research_stock(ts_code, name)
            result["dexter"] = {
                "success": dexter_result.get("success"),
                "analysis_preview": dexter_result.get("analysis", "")[:500] if dexter_result.get("analysis") else ""
            }
            logger.info(f"   Dexter 研究完成 (success: {dexter_result.get('success')})")
        except Exception as e:
            logger.warning(f"   Dexter 失败: {e}")
            result["dexter"] = {"success": False, "error": str(e)}
        
        # Step 3: TradingAgents 综合决策
        logger.info("🤖 [3/3] TradingAgents 综合决策...")
        
        decision_result = self.trading_agents.decide(
            ticker=ts_code,
            analysis_date=datetime.now().strftime('%Y-%m-%d'),
            kronos_signal=kronos_signal,
            dexter_report=result["dexter"].get("analysis_preview") if result["dexter"] else None,
            market_data=None
        )
        
        result["final_decision"] = decision_result
        
        final_action = decision_result.get("decision", {}).get("action", "HOLD")
        logger.info(f"🎯 最终决策: {final_action}")
        
        return result
    
    def run(self, stock_list=None):
        if stock_list is None:
            stock_list = config.WATCHLIST
        
        logger.info("=" * 60)
        logger.info("🚀 三工具集成交易系统启动")
        logger.info(f"分析股票数: {len(stock_list)}")
        logger.info("=" * 60)
        
        results = []
        for stock in stock_list:
            result = self.analyze_single_stock(stock)
            if result:
                results.append(result)
        
        # 输出汇总
        logger.info("\n" + "=" * 60)
        logger.info("📊 分析汇总")
        logger.info("=" * 60)
        
        for r in results:
            action = r.get("final_decision", {}).get("decision", {}).get("action", "HOLD")
            emoji = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "⚪"
            logger.info(f"{emoji} {r['name']}: {action}")
        
        return results

def main():
    system = ThreeToolsTradingSystem()
    results = system.run()
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ 系统运行完成")

if __name__ == "__main__":
    main()
