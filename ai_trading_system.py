#!/usr/bin/env python3
"""AI 增强版交易系统（集成 DeepSeek 智能分析）"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from datetime import datetime
from loguru import logger
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

from config.settings import config
from data_layer.tushare_client import TushareClient
from analysis_layer.kronos_predictor import KronosPredictor

class AITradingSystem:
    """AI 增强交易系统"""
    
    def __init__(self):
        self.data_client = TushareClient()
        self.predictor = KronosPredictor()
        self.llm_client = OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url='https://api.deepseek.com/v1'
        )
        logger.info("AI 交易系统初始化完成")
    
    def get_ai_analysis(self, stock_name: str, price: float, signal: dict) -> str:
        """使用 DeepSeek 进行智能分析"""
        prompt = f"""
        你是专业的股票分析师。请对{stock_name}进行简要分析：
        
        当前价格: {price}
        技术信号: {signal['action']}
        置信度: {signal['confidence']:.2%}
        
        请给出：
        1. 一句话总结
        2. 操作建议（买入/卖出/持有）
        3. 风险提示
        """
        
        try:
            response = self.llm_client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"AI 分析失败: {e}")
            return "AI 分析服务暂时不可用"
    
    def run(self):
        """运行 AI 交易系统"""
        logger.info("=" * 60)
        logger.info("🤖 AI 增强版自动化交易系统启动")
        logger.info("=" * 60)
        
        for stock in config.WATCHLIST:
            logger.info(f"\n📊 分析: {stock['name']}")
            
            # 获取数据
            df = self.data_client.get_kline(stock['ts_code'], days=200)
            if len(df) < 50:
                continue
            
            # 获取预测信号
            signal = self.predictor.predict(df)
            latest_price = df['close'].iloc[-1]
            
            # AI 智能分析
            logger.info(f"💡 AI 智能分析中...")
            ai_advice = self.get_ai_analysis(stock['name'], latest_price, signal)
            
            logger.info(f"📈 技术信号: {signal['action']} (置信度: {signal['confidence']:.2%})")
            logger.info(f"🧠 AI 建议:\n{ai_advice}")
            logger.info("-" * 40)
        
        logger.info("✅ 系统运行完成")

if __name__ == "__main__":
    system = AITradingSystem()
    system.run()
