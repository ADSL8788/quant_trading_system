#!/usr/bin/env python3
import pandas as pd
import numpy as np
import logging
import os
from datetime import datetime, timedelta
from config.settings import config

# 配置日志，方便在后台查看报错
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TushareClient:
    def __init__(self, cache_dir=".cache_data"):
        """
        Tushare 客户端初始化
        :param cache_dir: 本地缓存文件夹名称
        """
        import tushare as ts
        try:
            # 使用配置中的 token 初始化
            self.pro = ts.pro_api(config.TUSHARE_TOKEN)
            logger.info("✅ Tushare API 初始化成功")
        except Exception as e:
            logger.error(f"❌ Tushare API 初始化失败: {e}")
            raise e

        # 创建缓存目录
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            logger.info(f"📁 创建缓存目录: {self.cache_dir}")

    def get_kline(self, ts_code: str, days: int = 500, use_cache: bool = True):
        """
        获取K线数据 - 增强版 (含缓存与类型修复)
        :param ts_code: 股票代码 (例如 '000001.SZ')
        :param days: 回溯天数
        :param use_cache: 是否使用本地缓存
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')

        # --- 1. 缓存检查逻辑 ---
        # 缓存文件名包含 ts_code 和 days，防止不同时间窗口的数据混淆
        cache_file = os.path.join(self.cache_dir, f"{ts_code}_{days}.csv")
        
        if use_cache and os.path.exists(cache_file):
            # 检查文件最后修改时间是否为今天
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if file_mod_time.date() == end_date.date():
                # logger.debug(f"📦 从缓存加载: {ts_code}")
                try:
                    df = pd.read_csv(cache_file, index_col=0)
                    # 重新将 timestamp 转换为 datetime 对象
                    if 'timestamp' in df.columns:
                        df['timestamp'] = pd.to_datetime(df['timestamp'])
                    return df
                except Exception as e:
                    logger.warning(f"⚠️ 缓存读取失败 {ts_code}, 将重新请求 API: {e}")

        # --- 2. API 请求逻辑 ---
        df = self._fetch_from_api(ts_code, start_date=start_str, end_date=end_str)

        # --- 3. 保存至缓存 ---
        if df is not None and not df.empty and use_cache:
            try:
                df.to_csv(cache_file)
            except Exception as e:
                logger.error(f"❌ 保存缓存失败 {ts_code}: {e}")

        return df

    def _fetch_from_api(self, ts_code, start_date=None, end_date=None):
        """
        底层API调用函数，处理数据清洗和类型转换
        """
        # 保底日期处理
        if start_date is None or end_date is None:
            end_dt = datetime.now()
            start_dt = end_dt - timedelta(days=200)
            start_date = start_dt.strftime('%Y%m%d')
            end_date = end_dt.strftime('%Y%m%d')

        try:
            # 调用 Tushare 接口获取日线数据
            df = self.pro.daily(ts_code=ts_code, start=start_date, end=end_date)
            
            if df is None or df.empty:
                return None

            # ============================================================
            # 核心修复 1: 强制数值类型转换 (pd.to_numeric)
            # Tushare 有时返回 object 类型，会导致 numpy 计算或 TA-Lib 报错
            # ============================================================
            numeric_cols = ['open', 'high', 'low', 'close', 'vol', 'amount']
            for col in numeric_cols:
                if col in df.columns:
                    # errors='coerce' 会将无法转换的值设为 NaN，随后可以通过 ffill 处理
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            # ============================================================
            # 核心修复 2: 时间戳标准化与排序
            # ============================================================
            if 'trade_date' in df.columns:
                # 统一创建 timestamp 列，方便 AutoScreener 和预测模型处理
                df['timestamp'] = pd.to_datetime(df['trade_date']).dt.normalize()
                
                # 强制升序排列 (旧 $\rightarrow$ 新)，这是时间序列分析的必须条件
                df = df.sort_values('timestamp', ascending=True).reset_index(drop=True)
            
            return df

        except Exception as e:
            logger.error(f"❌ API Fetch Error for {ts_code}: {e}")
            return None
