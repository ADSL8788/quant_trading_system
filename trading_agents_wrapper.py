#!/usr/bin/env python3
"""TradingAgents 多智能体决策框架封装器 - 增强决策理由"""
import sys
import os
import re
import warnings
warnings.filterwarnings("ignore")

# 禁止所有日志输出
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
import logging
logging.disable(logging.CRITICAL)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'TradingAgents'))

def generate_reason(kronos_signal, dexter_report=None):
    """根据 Kronos 信号和 Dexter 报告生成决策理由"""
    action = kronos_signal.get('action', 'HOLD')
    conf = kronos_signal.get('confidence', 0)
    conf_pct = f"{conf:.0%}"
    
    # 解析 Dexter 报告中的评级（买入/持有/卖出）
    dexter_rating = None
    if dexter_report:
        # 优先匹配明确评级
        if re.search(r'评级[：:]\s*买入', dexter_report):
            dexter_rating = "买入"
        elif re.search(r'评级[：:]\s*卖出', dexter_report):
            dexter_rating = "卖出"
        elif re.search(r'评级[：:]\s*持有', dexter_report):
            dexter_rating = "持有"
        elif re.search(r'投资结论[：:]\s*买入', dexter_report):
            dexter_rating = "买入"
        elif re.search(r'投资结论[：:]\s*卖出', dexter_report):
            dexter_rating = "卖出"
        elif re.search(r'投资结论[：:]\s*持有', dexter_report):
            dexter_rating = "持有"
        # 其次匹配核心结论
        elif re.search(r'核心结论[：:]\s*买入', dexter_report):
            dexter_rating = "买入"
        elif re.search(r'核心结论[：:]\s*卖出', dexter_report):
            dexter_rating = "卖出"
        elif re.search(r'核心结论[：:]\s*持有', dexter_report):
            dexter_rating = "持有"
        # 从文本中提取“看多/看空/中性”
        elif '看多' in dexter_report:
            dexter_rating = "看多"
        elif '看空' in dexter_report:
            dexter_rating = "看空"
        elif '中性' in dexter_report:
            dexter_rating = "中性"
    
    # 构建理由
    if dexter_rating:
        if action == 'BUY':
            if '买入' in dexter_rating or '看多' in dexter_rating:
                reason = f"Kronos信号BUY({conf_pct})，Dexter评级{dexter_rating}，综合建议买入"
            else:
                reason = f"Kronos信号BUY({conf_pct})，但Dexter评级{dexter_rating}，建议谨慎"
        elif action == 'SELL':
            if '卖出' in dexter_rating or '看空' in dexter_rating:
                reason = f"Kronos信号SELL({conf_pct})，Dexter评级{dexter_rating}，综合建议卖出"
            else:
                reason = f"Kronos信号SELL({conf_pct})，Dexter评级{dexter_rating}，观望为宜"
        else:
            reason = f"Kronos信号HOLD({conf_pct})，Dexter评级{dexter_rating}，建议持有观望"
    else:
        if action == 'BUY':
            reason = f"Kronos信号BUY({conf_pct})，无明确基本面信号，建议轻仓试探"
        elif action == 'SELL':
            reason = f"Kronos信号SELL({conf_pct})，无明确基本面信号，建议减仓"
        else:
            reason = f"Kronos信号HOLD({conf_pct})，等待更明确信号"
    return reason

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
            self.ta = TradingAgentsGraph(debug=False, config=config)
        except Exception:
            self.ta = None

    def decide(self, ticker, name, kronos_signal, dexter_report=None, market_data=None):
        # 降级方案：生成理由直接返回
        if self.ta is None:
            action = kronos_signal.get('action', 'HOLD')
            reason = generate_reason(kronos_signal, dexter_report)
            return {
                "success": False,
                "decision": {
                    "action": action,
                    "reason": reason,
                    "confidence": kronos_signal.get('confidence', 0)
                },
                "fallback": True
            }

        try:
            _, decision = self.ta.propagate(ticker, __import__('datetime').datetime.now().strftime('%Y-%m-%d'))
            # 如果 TradingAgents 返回的 decision 中没有 reason，则根据输入生成
            if isinstance(decision, dict) and 'reason' not in decision:
                decision['reason'] = generate_reason(kronos_signal, dexter_report)
            elif isinstance(decision, str):
                # 若 decision 是字符串，构造标准格式
                action = decision if decision in ['BUY','SELL','HOLD'] else 'HOLD'
                decision = {
                    "action": action,
                    "reason": generate_reason(kronos_signal, dexter_report)
                }
            return {"success": True, "decision": decision}
        except Exception as e:
            # 出错时降级
            action = kronos_signal.get('action', 'HOLD')
            reason = generate_reason(kronos_signal, dexter_report)
            return {
                "success": False,
                "decision": {"action": action, "reason": reason},
                "fallback": True
            }
