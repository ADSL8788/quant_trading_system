#!/usr/bin/env python3
"""TradingAgents 多智能体决策框架封装器 - 完全静默版"""
import sys
import os
import warnings
warnings.filterwarnings("ignore")

# 禁止所有日志输出
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
import logging
logging.disable(logging.CRITICAL)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'TradingAgents'))

class TradingAgentsWrapper:
    def __init__(self, llm_provider="deepseek"):
        self.llm_provider = llm_provider
        self.ta = None
        self._initialize()
    
    def _initialize(self):
        try:
            from tradingagents.graph.trading_graph import TradingAgentsGraph
            from tradingagents.default_config import DEFAULT_CONFIG
            
            config = DEFAULT_CONFIG.copy()
            config["llm_provider"] = self.llm_provider
            config["deep_think_llm"] = "deepseek-reasoner"
            config["quick_think_llm"] = "deepseek-chat"
            config["max_debate_rounds"] = 1
            # 关闭调试输出
            self.ta = TradingAgentsGraph(debug=False, config=config)
        except Exception:
            self.ta = None
    
    def decide(self, ticker, name, kronos_signal, dexter_report=None, market_data=None):
        if self.ta is None:
            return self._fallback_decision(kronos_signal)
        try:
            _, decision = self.ta.propagate(ticker, __import__('datetime').datetime.now().strftime('%Y-%m-%d'))
            return {"success": True, "decision": decision}
        except Exception:
            return self._fallback_decision(kronos_signal)
    
    def _fallback_decision(self, kronos_signal):
        action = kronos_signal.get('action', 'HOLD') if kronos_signal else 'HOLD'
        return {"success": False, "decision": {"action": action}}
