#!/usr/bin/env python3
"""自动化交易系统 - 主程序"""
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from loguru import logger

# 配置日志
os.makedirs("logs", exist_ok=True)
logger.add("logs/trading.log", rotation="1 day", level="INFO")
logger.add(sys.stderr, level="INFO")

from config.settings import config
from data_layer.tushare_client import TushareClient
from analysis_layer.kronos_predictor import KronosPredictor

def main():
    logger.info("=" * 60)
    logger.info("自动化交易系统启动")
    logger.info(f"运行模式: {'纸面模拟' if config.PAPER_TRADING else '实盘'}")
    logger.info(f"监控标的: {[s['name'] for s in config.WATCHLIST]}")
    logger.info("=" * 60)
    
    # 初始化组件
    try:
        data_client = TushareClient()
        predictor = KronosPredictor()
    except Exception as e:
        logger.error(f"初始化失败: {e}")
        return
    
    # 分析每只股票
    for stock in config.WATCHLIST:
        logger.info(f"\n正在分析: {stock['name']} ({stock['ts_code']})")
        
        try:
            # 获取数据
            df = data_client.get_kline(stock['ts_code'], days=200)
            
            if len(df) < 50:
                logger.warning(f"  数据不足: 仅{len(df)}条")
                continue
            
            # 获取预测信号
            signal = predictor.predict(df)
            
            # 获取最新行情
            latest = df.iloc[-1]
            
            logger.info(f"  最新日期: {latest['timestamp'].strftime('%Y-%m-%d')}")
            logger.info(f"  当前价格: {latest['close']:.2f}")
            logger.info(f"  预测操作: {signal['action']}")
            logger.info(f"  置信度: {signal['confidence']:.2%}")
            
            if signal['action'] == 'BUY':
                logger.info(f"  🟢 建议买入，目标价: {signal['target_price']:.2f}")
            elif signal['action'] == 'SELL':
                logger.info(f"  🔴 建议卖出")
            else:
                logger.info(f"  ⚪ 建议持有")
                
        except Exception as e:
            logger.error(f"  分析失败: {e}")
    
    logger.info("\n" + "=" * 60)
    logger.info("系统运行完成")

if __name__ == "__main__":
    main()
