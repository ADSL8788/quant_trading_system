"""系统配置文件 - 自动从选股结果加载股票池"""
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

class Config:
    TUSHARE_TOKEN = os.getenv("TUSHARE_TOKEN")
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

    BATTERY_STOCKS = []
    ROBOT_STOCKS = []
    TRANSFORMER_STOCKS = []
    AI_STOCKS = []
    DIGITAL_COIN_STOCKS = []
    EXTRA_STOCKS = [
        {"ts_code": "002240.SZ", "name": "盛新锂能", "sector": "其他"},
        {"ts_code": "601778.SH", "name": "晶科科技", "sector": "其他"},
        {"ts_code": "002361.SZ", "name": "神剑股份", "sector": "其他"},
        {"ts_code": "603777.SH", "name": "来伊份", "sector": "其他"},
        {"ts_code": "688525.SH", "name": "佰维存储", "sector": "其他"},
        {"ts_code": "603890.SH", "name": "春秋电子", "sector": "其他"},
        {"ts_code": "920171.BJ", "name": "志晟信息", "sector": "其他"},
        {"ts_code": "603315.SH", "name": "福鞍股份", "sector": "其他"},
        {"ts_code": "300870.SZ", "name": "欧陆通", "sector": "其他"},
        {"ts_code": "600338.SH", "name": "西藏珠峰", "sector": "其他"},
        {"ts_code": "301489.SZ", "name": "思泉新材", "sector": "其他"},
        {"ts_code": "300097.SZ", "name": "智云股份", "sector": "其他"},
        {"ts_code": "301265.SZ", "name": "华新科技", "sector": "其他"},
        {"ts_code": "300322.SZ", "name": "硕贝德", "sector": "其他"},
        {"ts_code": "301358.SZ", "name": "湖南裕能", "sector": "其他"},
        {"ts_code": "002824.SZ", "name": "和胜股份", "sector": "其他"},
        {"ts_code": "603906.SH", "name": "龙蟠科技", "sector": "其他"},
        {"ts_code": "603052.SH", "name": "可川科技", "sector": "其他"},
        {"ts_code": "300900.SZ", "name": "广联航空", "sector": "其他"},
        {"ts_code": "605303.SH", "name": "园林股份", "sector": "其他"},
    ]

    # 注意：WATCHLIST 将在创建 config 实例后被动态覆盖
    WATCHLIST = EXTRA_STOCKS

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

# ========== 动态加载股票池（从选股结果 CSV）==========
# 获取项目根目录（auto_trading_system）
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, 'data', 'auto_screener_results.csv')

if os.path.exists(CSV_PATH):
    try:
        df = pd.read_csv(CSV_PATH)
        # 检查必要的列是否存在
        if 'ts_code' in df.columns and 'name' in df.columns:
            config.WATCHLIST = df[['ts_code', 'name']].to_dict('records')
            print(f"✅ 从 {CSV_PATH} 加载了 {len(config.WATCHLIST)} 只股票")
        else:
            print(f"⚠️ CSV 文件缺少 'ts_code' 或 'name' 列，使用空股票池")
            config.WATCHLIST = []
    except Exception as e:
        print(f"❌ 读取 CSV 文件失败: {e}，使用空股票池")
        config.WATCHLIST = []
else:
    print(f"⚠️ 未找到股票池文件: {CSV_PATH}")
    print(f"   请先运行选股脚本生成 {CSV_PATH}")
    config.WATCHLIST = []
# =================================================

print(f"✅ 配置加载成功")
print(f"   股票池数量: {len(config.WATCHLIST)} 只")
print(f"   仓位管理: 单票{config.MAX_SINGLE_POSITION:.0%} | 板块{config.MAX_SECTOR_POSITION:.0%}")
print(f"   风控: 止损{config.STOP_LOSS:.0%} | 止盈{config.TAKE_PROFIT:.0%}")
