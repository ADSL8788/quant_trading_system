"""Kronos 价格预测模块 - 真实模型版"""
import sys
import os
import pandas as pd
import numpy as np
from loguru import logger

class KronosPredictor:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.predictor = None
        self.max_context = 512
        self._load_model()

    def _load_model(self):
        """加载真正的 Kronos 模型"""
        try:
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Kronos'))
            from model import Kronos, KronosTokenizer, KronosPredictor as KP
            
            # 加载预训练模型（使用 small 版本，可根据需要改为 base）
            model_name = "NeoQuasar/Kronos-small"
            tokenizer_name = "NeoQuasar/Kronos-Tokenizer-base"
            
            logger.info(f"正在加载 Kronos 模型: {model_name}")
            self.tokenizer = KronosTokenizer.from_pretrained(tokenizer_name)
            self.model = Kronos.from_pretrained(model_name)
            self.predictor = KP(self.model, self.tokenizer, max_context=self.max_context)
            logger.info("✅ Kronos 模型加载成功")
            self.model_available = True
        except Exception as e:
            logger.warning(f"Kronos 模型加载失败，将使用基础策略: {e}")
            self.model_available = False

    def predict(self, df: pd.DataFrame) -> dict:
        if len(df) < 50:
            return {'action': 'HOLD', 'confidence': 0, 'reason': '数据不足'}

        if not self.model_available:
            # 降级策略
            return self._fallback_predict(df)

        try:
            # 准备数据
            lookback = 400  # Kronos 需要的上下文长度（不超过 max_context）
            if len(df) > lookback:
                df = df.tail(lookback)
            
            x_df = df[['open', 'high', 'low', 'close', 'volume']]
            x_timestamp = pd.to_datetime(df['timestamp'])
            # 预测未来 60 根 K 线（可根据配置调整）
            pred_len = 60
            last_ts = x_timestamp.iloc[-1]
            y_timestamp = pd.date_range(start=last_ts + pd.Timedelta(days=1), periods=pred_len, freq='D')
            
            pred_df = self.predictor.predict(
                df=x_df,
                x_timestamp=x_timestamp,
                y_timestamp=y_timestamp,
                pred_len=pred_len,
                T=1.0,
                top_p=0.9,
                sample_count=5
            )
            
            # 提取预测结果
            current_price = df['close'].iloc[-1]
            predicted_last = pred_df['close'].iloc[-1] if not pred_df.empty else current_price
            expected_return = (predicted_last - current_price) / current_price
            confidence = min(0.9, abs(expected_return) * 10)
            
            action = 'BUY' if expected_return > 0.02 else 'SELL' if expected_return < -0.02 else 'HOLD'
            
            return {
                'action': action,
                'confidence': confidence,
                'expected_return': expected_return,
                'target_price': predicted_last,
                'current_price': current_price
            }
        except Exception as e:
            logger.error(f"Kronos 预测失败: {e}")
            return self._fallback_predict(df)
    
    def _fallback_predict(self, df: pd.DataFrame) -> dict:
        """降级策略：简单移动平均"""
        last_close = df['close'].iloc[-1]
        ma_5 = df['close'].rolling(5).mean().iloc[-1]
        ma_20 = df['close'].rolling(20).mean().iloc[-1]
        ma_60 = df['close'].rolling(60).mean().iloc[-1]
        if ma_5 > ma_20 and ma_20 > ma_60:
            action = 'BUY'
            expected_return = 0.03
        elif ma_5 < ma_20 and ma_20 < ma_60:
            action = 'SELL'
            expected_return = -0.02
        else:
            action = 'HOLD'
            expected_return = 0
        trend_strength = abs(ma_5 - ma_20) / ma_20 if ma_20 > 0 else 0
        confidence = min(0.85, trend_strength * 10)
        return {
            'action': action,
            'confidence': confidence,
            'expected_return': expected_return,
            'target_price': last_close * (1 + expected_return),
            'current_price': last_close
        }
