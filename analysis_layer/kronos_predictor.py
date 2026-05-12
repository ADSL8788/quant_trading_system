"""Kronos 价格预测模块 - 极致兼容版（修复所有 DatetimeIndex 属性访问）"""
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
        self._load_model()

    def _load_model(self):
        try:
            sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Kronos'))
            from model import Kronos, KronosTokenizer, KronosPredictor as KP
            
            model_name = "NeoQuasar/Kronos-small"
            tokenizer_name = "NeoQuasar/Kronos-Tokenizer-base"
            
            logger.info(f"正在加载 Kronos 模型: {model_name}")
            self.tokenizer = KronosTokenizer.from_pretrained(tokenizer_name)
            self.model = Kronos.from_pretrained(model_name)
            self.predictor = KP(self.model, self.tokenizer, max_context=512)
            logger.info("✅ Kronos 模型加载成功")
            self.model_available = True
        except Exception as e:
            logger.warning(f"Kronos 模型加载失败，将使用基础策略: {e}")
            self.model_available = False

    def predict(self, df: pd.DataFrame) -> dict:
        if len(df) < 50:
            return {'action': 'HOLD', 'confidence': 0, 'reason': '数据不足'}

        if not self.model_available:
            return self._fallback_predict(df)

        try:
            # 1. 准备数据窗口
            lookback = min(400, len(df))
            df_use = df.tail(lookback).copy()
            
            x_df = df_use[['open', 'high', 'low', 'close', 'volume']]
            
            # 2. 【关键修复】x_timestamp 强制转为 Series
            # 无论原始数据是字符串还是 Index，统一转为 datetime Series
            x_timestamp_series = pd.to_datetime(df_use['timestamp']).to_series() if hasattr(pd.to_datetime(df_use['timestamp']), 'to_series') else pd.Series(pd.to_datetime(df_use['timestamp']))
            
            # 3. 【关键修复】y_timestamp 强制转为 Series
            pred_len = 60
            last_ts = pd.to_datetime(df_use['timestamp'].iloc[-1])
            # pd.date_range 返回的是 DatetimeIndex，必须转为 Series 才能使用 .dt
            y_timestamp_index = pd.date_range(start=last_ts + pd.Timedelta(days=1), periods=pred_len, freq='D')
            y_timestamp_series = pd.Series(y_timestamp_index)
            
            # 4. 调用模型
            pred_df = self.predictor.predict(
                df=x_df,
                x_timestamp=x_timestamp_series, # 传 Series
                y_timestamp=y_timestamp_series, # 传 Series
                pred_len=pred_len,
                T=1.0,
                top_p=0.9,
                sample_count=5
            )
            
            if pred_df is None or pred_df.empty:
                return self._fallback_predict(df)

            current_price = df['close'].iloc[-1]
            predicted_last = pred_df['close'].iloc[-1]
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
            logger.error(f"Kronos 预测内部执行失败: {e}")
            return self._fallback_predict(df)
    
    def _fallback_predict(self, df: pd.DataFrame) -> dict:
        """降级策略：简单移动平均"""
        try:
            last_close = df['close'].iloc[-1]
            ma_5 = df['close'].rolling(5).mean().iloc[-1]
            ma_20 = df['close'].rolling(20).mean().iloc[-1]
            ma_60 = df['close'].rolling(60).mean().iloc[-1]
            
            if ma_5 > ma_20 and ma_20 > ma_60:
                action, expected_return = 'BUY', 0.03
            elif ma_5 < ma_20 and ma_20 < ma_60:
                action, expected_return = 'SELL', -0.02
            else:
                action, expected_return = 'HOLD', 0
                
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
            return {'action': 'HOLD', 'confidence': 0, 'reason': f'Fallback failed: {e}'}
