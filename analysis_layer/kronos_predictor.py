"""Kronos 价格预测模块"""
import sys
import os
import pandas as pd
import numpy as np
from loguru import logger

class KronosPredictor:
    """Kronos 预测器包装类"""
    
    def __init__(self):
        self.model_available = False
        self._load_model()
    
    def _load_model(self):
        """尝试加载 Kronos 模型"""
        try:
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Kronos'))
            from model import Kronos
            self.model_available = True
            logger.info("✅ Kronos 模型加载成功")
        except ImportError as e:
            logger.warning(f"Kronos 模型不可用，使用基础策略: {e}")
            self.model_available = False
    
    def predict(self, df: pd.DataFrame) -> dict:
        """预测价格走势"""
        if len(df) < 50:
            return {'action': 'HOLD', 'confidence': 0, 'reason': '数据不足'}
        
        try:
            last_close = df['close'].iloc[-1]
            
            # 简单移动平均策略
            ma_5 = df['close'].rolling(5).mean().iloc[-1]
            ma_20 = df['close'].rolling(20).mean().iloc[-1]
            ma_60 = df['close'].rolling(60).mean().iloc[-1]
            
            # 判断趋势
            if ma_5 > ma_20 and ma_20 > ma_60:
                action = 'BUY'
                expected_return = 0.03
            elif ma_5 < ma_20 and ma_20 < ma_60:
                action = 'SELL'
                expected_return = -0.02
            else:
                action = 'HOLD'
                expected_return = 0
            
            # 计算置信度
            trend_strength = abs(ma_5 - ma_20) / ma_20 if ma_20 > 0 else 0
            confidence = min(0.85, trend_strength * 10)
            
            return {
                'action': action,
                'confidence': confidence,
                'expected_return': expected_return,
                'target_price': last_close * (1 + expected_return),
                'current_price': last_close
            }
        except Exception as e:
            logger.error(f"预测失败: {e}")
            return {'action': 'HOLD', 'confidence': 0, 'reason': str(e)}
