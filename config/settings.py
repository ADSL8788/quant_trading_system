"""系统配置文件 - 安全版（支持动态扩展股票池）"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """全局配置"""
    
    TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    
    # ========== 板块分类（固定部分） ==========
    BATTERY_STOCKS = []
    
    ROBOT_STOCKS = [
    ]
    
    TRANSFORMER_STOCKS = [
    ]
    
    AI_STOCKS = []
    
    DIGITAL_COIN_STOCKS = []
    
    # ========== 通过 add 命令添加的股票（仅存放于此） ==========
    EXTRA_STOCKS = [
        # 示例：{"ts_code": "002273.SZ", "name": "水晶光电", "sector": "元器件"},
    {"ts_code": "600186.SH", "name": "莲花控股", "sector": "其他"},
    {"ts_code": "000007.SZ", "name": "全新好", "sector": "其他"},
    ]
    
    # ========== 合并所有股票池 ==========
    WATCHLIST = (BATTERY_STOCKS + ROBOT_STOCKS + TRANSFORMER_STOCKS +
                 AI_STOCKS + DIGITAL_COIN_STOCKS + EXTRA_STOCKS)
    
    KRONOS_CONFIG = {"lookback": 120, "pred_len": 60, "min_confidence": 0.25}
    PAPER_TRADING = os.getenv("PAPER_TRADING", "true").lower() == "true"
    INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", 1000000))
    MAX_SINGLE_POSITION = 0.10
    MAX_SECTOR_POSITION = 0.30
    STOP_LOSS = 0.07
    TAKE_PROFIT = 0.15
    WECHAT_WEBHOOK = os.getenv("WECHAT_WEBHOOK", "")
    SERVER_CHAN_KEY = os.getenv("SERVER_CHAN_KEY", "")

config = Config()

# 打印信息
from collections import defaultdict
sector_count = defaultdict(int)
for stock in config.WATCHLIST:
    sector_count[stock.get('sector', '未分类')] += 1

print(f"✅ 配置加载成功")
print(f"   股票池数量: {len(config.WATCHLIST)} 只")
print(f"   板块分布: {', '.join([f'{k}:{v}只' for k,v in sector_count.items()])}")
print(f"   仓位管理: 单票{config.MAX_SINGLE_POSITION:.0%} | 板块{config.MAX_SECTOR_POSITION:.0%}")
print(f"   风控: 止损{config.STOP_LOSS:.0%} | 止盈{config.TAKE_PROFIT:.0%}")
