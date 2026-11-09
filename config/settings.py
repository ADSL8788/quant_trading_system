"""系统配置文件 - 统一股票池（手动JSON + 可选CSV）"""
import os
import json
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
    EXTRA_STOCKS = []   # 废弃，仅兼容

    # 开关：是否自动从 CSV 合并股票池
    AUTO_SYNC_FROM_CSV = True

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

# ========== 动态构建股票池 ==========
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, 'data', 'auto_screener_results.csv')
MANUAL_JSON_PATH = os.path.join(BASE_DIR, 'data', 'manual_stocks.json')

def load_manual_stocks():
    if os.path.exists(MANUAL_JSON_PATH):
        try:
            with open(MANUAL_JSON_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 读取手动股票 JSON 失败: {e}")
    return []

def load_csv_stocks():
    if not config.AUTO_SYNC_FROM_CSV:
        return []
    if os.path.exists(CSV_PATH):
        try:
            df = pd.read_csv(CSV_PATH)
            if 'ts_code' in df.columns and 'name' in df.columns:
                stocks = df[['ts_code', 'name']].to_dict('records')
                for s in stocks:
                    s.setdefault('sector', '自动筛选')
                return stocks
        except Exception as e:
            print(f"❌ 读取 CSV 失败: {e}")
    return []

def merge_stock_pools(csv_stocks, manual_stocks):
    merged = {}
    for s in manual_stocks:
        merged[s['ts_code']] = s
    for s in csv_stocks:
        if s['ts_code'] not in merged:
            merged[s['ts_code']] = s
    return list(merged.values())

csv_list = load_csv_stocks()
manual_list = load_manual_stocks()
config.WATCHLIST = merge_stock_pools(csv_list, manual_list)

print(f"✅ 配置加载成功")
print(f"   自动同步: {'开启' if config.AUTO_SYNC_FROM_CSV else '关闭'} | 手动池: {len(manual_list)} 只")
print(f"   总股票池: {len(config.WATCHLIST)} 只")
