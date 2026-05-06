#!/usr/bin/env python3
"""轻量级多智能体决策模块 - 不使用 Yahoo Finance"""
import os
from datetime import datetime
from loguru import logger
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class LightTradingAgents:
    """轻量级多智能体决策框架"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url='https://api.deepseek.com/v1'
        )
        logger.info("✅ 轻量级 TradingAgents 初始化完成")
    
    def decide(self, ticker, name, kronos_signal, dexter_report, market_data):
        """多智能体决策"""
        
        # 模拟多个智能体的角色
        agents = {
            "技术分析师": self._technical_analysis,
            "基本面分析师": self._fundamental_analysis,
            "风控经理": self._risk_analysis,
            "投资总监": self._final_decision
        }
        
        # 收集各智能体意见
        opinions = {}
        for role, func in agents.items():
            if role != "投资总监":
                opinion = func(ticker, name, kronos_signal, dexter_report, market_data)
                opinions[role] = opinion
                logger.info(f"  {role}: {opinion[:50]}...")
        
        # 最终决策
        final = self._final_decision(ticker, name, kronos_signal, dexter_report, market_data, opinions)
        return final
    
    def _technical_analysis(self, ticker, name, kronos_signal, dexter_report, market_data):
        """技术分析智能体"""
        prompt = f"""你是技术分析师。基于以下信号给出简短的判断：

Kronos 信号: {kronos_signal.get('action', 'HOLD')}
置信度: {kronos_signal.get('confidence', 0):.1%}
预期收益: {kronos_signal.get('expected_return', 0):+.2%}

请用一句话给出建议（买入/卖出/持有）。"""
        
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50
        )
        return response.choices[0].message.content
    
    def _fundamental_analysis(self, ticker, name, kronos_signal, dexter_report, market_data):
        """基本面分析智能体"""
        # 从 Dexter 报告中提取关键信息
        if dexter_report and len(dexter_report) > 100:
            preview = dexter_report[:300]
        else:
            preview = "无详细报告"
        
        prompt = f"""你是基本面分析师。基于以下研究给出判断：

研究报告摘要:
{preview}

请用一句话给出建议（买入/卖出/持有）。"""
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50
            )
            return response.choices[0].message.content
        except:
            return "持有"
    
    def _risk_analysis(self, ticker, name, kronos_signal, dexter_report, market_data):
        """风险分析智能体"""
        confidence = kronos_signal.get('confidence', 0)
        
        if confidence < 0.2:
            return f"风险较高：信号置信度过低({confidence:.1%})，建议观望"
        elif confidence > 0.7:
            return "风险可控：信号置信度较高"
        else:
            return "风险中等：建议控制仓位"
    
    def _final_decision(self, ticker, name, kronos_signal, dexter_report, market_data, opinions):
        """最终决策智能体"""
        # 综合各智能体意见
        prompt = f"""你是投资总监。综合以下意见做出最终决策：

技术分析师: {opinions.get('技术分析师', '无')}
基本面分析师: {opinions.get('基本面分析师', '无')}
风控经理: {opinions.get('风控经理', '无')}

Kronos 原始信号: {kronos_signal.get('action', 'HOLD')}

请只输出一个词: BUY, SELL, 或 HOLD"""
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10
            )
            action = response.choices[0].message.content.strip().upper()
            if action not in ['BUY', 'SELL', 'HOLD']:
                action = 'HOLD'
        except:
            action = kronos_signal.get('action', 'HOLD')
        
        return {
            "action": action,
            "reason": f"综合决策: {action}",
            "provider": "轻量级多智能体"
        }

# 替换原来的 wrapper
class TradingAgentsWrapper(LightTradingAgents):
    """兼容原有接口"""
    pass
