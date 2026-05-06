#!/usr/bin/env python3
"""Dexter 简化版 - 完全静默（无日志）"""
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class DexterWrapper:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url='https://api.deepseek.com/v1'
        )
    
    def research_stock(self, ts_code, stock_name):
        from data_layer.tushare_client import TushareClient
        client = TushareClient()
        df = client.get_kline(ts_code, days=100)
        
        price_info = ""
        if len(df) >= 50:
            current = df['close'].iloc[-1]
            ma20 = df['close'].rolling(20).mean().iloc[-1]
            ma60 = df['close'].rolling(60).mean().iloc[-1]
            price_info = f"""
当前价格: {current:.2f}
20日均线: {ma20:.2f}
60日均线: {ma60:.2f}
趋势: {'上升' if current > ma60 else '下降'}
"""
        prompt = f"""你是一位专业的金融研究员。请对{stock_name}({ts_code})进行全面分析：

{price_info}

请按以下框架输出：
1. 财务健康度
2. 估值分析
3. 技术面分析
4. 风险因素
5. 投资结论（买入/持有/卖出）及目标价

输出简明扼要，不要多余解释。"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=1500
            )
            return {"success": True, "analysis": response.choices[0].message.content}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def research(self, query):
        try:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": query}],
                temperature=0.3,
                max_tokens=1500
            )
            return {"success": True, "stdout": response.choices[0].message.content}
        except Exception as e:
            return {"success": False, "error": str(e)}
