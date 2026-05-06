#!/usr/bin/env python3
"""独立的多智能体决策系统 - 完全不依赖 TradingAgents 源码"""
import os
import json
from datetime import datetime
from loguru import logger
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class IndependentAgents:
    """独立多智能体系统 - 使用 DeepSeek 实现所有角色"""
    
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url='https://api.deepseek.com/v1'
        )
        logger.info("✅ 独立多智能体系统初始化完成")
    
    def decide(self, ticker, name, kronos_signal, dexter_report, market_data=None):
        """
        综合决策
        
        Args:
            ticker: 股票代码
            name: 股票名称
            kronos_signal: Kronos 的量化信号
            dexter_report: Dexter 的研究报告
            market_data: 市场数据（可选）
        
        Returns:
            dict: 最终决策
        """
        logger.info(f"🤖 启动独立多智能体讨论: {name}")
        
        # 准备输入数据
        current_price = kronos_signal.get('current_price', 0)
        kronos_action = kronos_signal.get('action', 'HOLD')
        kronos_confidence = kronos_signal.get('confidence', 0)
        expected_return = kronos_signal.get('expected_return', 0)
        
        # 提取 Dexter 报告中的关键信息
        dexter_summary = self._extract_dexter_summary(dexter_report) if dexter_report else "无"
        
        # 构建各智能体的提示词
        agents_responses = {}
        
        # 1. 技术分析师
        logger.info("  📊 技术分析师分析中...")
        agents_responses['技术分析师'] = self._technical_analyst(
            name, current_price, kronos_action, kronos_confidence, expected_return
        )
        
        # 2. 基本面分析师
        logger.info("  📈 基本面分析师分析中...")
        agents_responses['基本面分析师'] = self._fundamental_analyst(
            name, dexter_summary
        )
        
        # 3. 风险分析师
        logger.info("  ⚠️ 风险分析师评估中...")
        agents_responses['风险分析师'] = self._risk_analyst(
            name, kronos_confidence, dexter_summary
        )
        
        # 4. 交易员（综合意见）
        logger.info("  💼 交易员综合判断中...")
        trader_opinion = self._trader(
            name, current_price, agents_responses
        )
        
        # 5. 风控总监（最终决策）
        logger.info("  🛡️ 风控总监最终审批...")
        final = self._risk_manager(
            name, current_price, trader_opinion, agents_responses, kronos_confidence
        )
        
        return final
    
    def _extract_dexter_summary(self, dexter_report):
        """从 Dexter 报告中提取关键信息"""
        if not dexter_report or len(dexter_report) < 50:
            return "无详细报告"
        
        # 提取前500字符作为摘要
        summary = dexter_report[:500]
        
        # 简单关键词提取
        keywords = []
        if '买入' in summary or '推荐' in summary:
            keywords.append('积极')
        if '卖出' in summary or '谨慎' in summary:
            keywords.append('谨慎')
        if '持有' in summary:
            keywords.append('中性')
        if '风险' in summary:
            keywords.append('有风险提示')
            
        return f"研究报告摘要: {summary[:200]}... 关键词: {', '.join(keywords) if keywords else '中性'}"
    
    def _technical_analyst(self, name, price, action, confidence, expected_return):
        """技术分析师"""
        prompt = f"""你是专业的技术分析师。请对{name}给出简短技术分析（50字以内）：

当前价格: {price}
量化信号: {action}
信号置信度: {confidence:.1%}
预期收益: {expected_return:+.2%}

请输出格式：【判断】买入/卖出/持有 【理由】一句话"""
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=100
            )
            return response.choices[0].message.content
        except:
            return f"【判断】{action} 【理由】基于量化模型信号"
    
    def _fundamental_analyst(self, name, dexter_summary):
        """基本面分析师"""
        prompt = f"""你是专业的基本面分析师。基于以下研究，给出简短判断（50字以内）：

{name} 基本面研究:
{dexter_summary}

请输出格式：【判断】买入/卖出/持有 【理由】一句话"""
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=100
            )
            return response.choices[0].message.content
        except:
            return "【判断】持有 【理由】基本面中性"
    
    def _risk_analyst(self, name, confidence, dexter_summary):
        """风险分析师"""
        if confidence < 0.2:
            risk_level = "高"
            advice = "建议观望"
        elif confidence < 0.5:
            risk_level = "中"
            advice = "建议小仓位"
        else:
            risk_level = "低"
            advice = "建议正常仓位"
        
        # 检查 Dexter 报告中的风险提示
        has_risk = '风险' in dexter_summary if dexter_summary else False
        
        return f"【风险等级】{risk_level} 【建议】{advice} {'【注意】报告中提到风险' if has_risk else ''}"
    
    def _trader(self, name, price, agents_responses):
        """交易员 - 综合各分析师意见"""
        tech = agents_responses.get('技术分析师', '')
        fund = agents_responses.get('基本面分析师', '')
        risk = agents_responses.get('风险分析师', '')
        
        prompt = f"""你是经验丰富的交易员。请综合以下意见，给出交易建议：

技术分析师: {tech}
基本面分析师: {fund}
风险分析师: {risk}

股票: {name}
当前价格: {price}

请只输出一个词: BUY, SELL, 或 HOLD"""
        
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=10
            )
            action = response.choices[0].message.content.strip().upper()
            if action not in ['BUY', 'SELL', 'HOLD']:
                action = 'HOLD'
            return action
        except:
            return 'HOLD'
    
    def _risk_manager(self, name, price, trader_action, agents_responses, confidence):
        """风控总监 - 最终审批"""
        # 置信度过滤
        if confidence < 0.2 and trader_action != 'HOLD':
            final_action = 'HOLD'
            reason = f"信号置信度过低({confidence:.1%})，风控拒绝交易"
        else:
            final_action = trader_action
            reason = f"综合多智能体意见，建议{final_action}"
        
        return {
            "action": final_action,
            "reason": reason,
            "confidence": confidence,
            "agents_opinions": {
                "技术分析师": agents_responses.get('技术分析师', ''),
                "基本面分析师": agents_responses.get('基本面分析师', ''),
                "风险分析师": agents_responses.get('风险分析师', '')
            },
            "provider": "独立多智能体系统 (DeepSeek)"
        }

# 替换原有的 TradingAgentsWrapper
class TradingAgentsWrapper(IndependentAgents):
    """兼容原有接口的包装器"""
    pass

if __name__ == "__main__":
    # 测试
    agents = IndependentAgents()
    test_signal = {
        "action": "BUY",
        "confidence": 0.18,
        "expected_return": 0.03,
        "current_price": 11.49
    }
    result = agents.decide("000001.SZ", "平安银行", test_signal, "测试报告")
    print(json.dumps(result, indent=2, ensure_ascii=False))
