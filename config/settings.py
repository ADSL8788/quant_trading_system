"""系统配置文件 - 干净版（无预设板块）"""
import os
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
        {"ts_code": "301219.SZ", "name": "腾远钴业", "sector": "小金属"},
        {"ts_code": "002463.SZ", "name": "沪电股份", "sector": "元器件"},
        {"ts_code": "603538.SH", "name": "美诺华", "sector": "化学制药"},
        {"ts_code": "301316.SZ", "name": "慧博云通", "sector": "其他"},
        {"ts_code": "301152.SZ", "name": "天力锂能", "sector": "其他"},
        {"ts_code": "601991.SH", "name": "大唐发电", "sector": "其他"},
        {"ts_code": "002091.SZ", "name": "江苏国泰", "sector": "其他"},
        {"ts_code": "600961.SH", "name": "株冶集团", "sector": "其他"},
        {"ts_code": "601512.SH", "name": "中新集团", "sector": "其他"},
        {"ts_code": "603660.SH", "name": "苏州科达", "sector": "其他"},
        {"ts_code": "002763.SZ", "name": "汇洁股份", "sector": "其他"},
        {"ts_code": "301290.SZ", "name": "东星医疗", "sector": "其他"},
        {"ts_code": "301176.SZ", "name": "逸豪新材", "sector": "其他"},
        {"ts_code": "301232.SZ", "name": "飞沃科技", "sector": "其他"},
        {"ts_code": "301018.SZ", "name": "申菱环境", "sector": "其他"},
        {"ts_code": "688519.SH", "name": "南亚新材", "sector": "其他"},
        {"ts_code": "002957.SZ", "name": "科瑞技术", "sector": "其他"},
        {"ts_code": "300870.SZ", "name": "欧陆通", "sector": "其他"},
        {"ts_code": "603890.SH", "name": "春秋电子", "sector": "其他"},
        {"ts_code": "688667.SH", "name": "菱电电控", "sector": "其他"},
        {"ts_code": "300243.SZ", "name": "瑞丰高材", "sector": "其他"},
        {"ts_code": "600103.SH", "name": "青山纸业", "sector": "其他"},
        {"ts_code": "603777.SH", "name": "来伊份", "sector": "其他"},
        {"ts_code": "301358.SZ", "name": "湖南裕能", "sector": "其他"},
        {"ts_code": "300058.SZ", "name": "蓝色光标", "sector": "其他"},
        {"ts_code": "301265.SZ", "name": "华新科技", "sector": "其他"},
        {"ts_code": "301517.SZ", "name": "陕西华达", "sector": "其他"},
        {"ts_code": "002361.SZ", "name": "神剑股份", "sector": "其他"},
        {"ts_code": "300051.SZ", "name": "琏升科技", "sector": "其他"},
        {"ts_code": "000026.SZ", "name": "飞亚达", "sector": "其他"},
        {"ts_code": "688525.SH", "name": "佰维存储", "sector": "其他"},
        {"ts_code": "002418.SZ", "name": "康盛股份", "sector": "其他"},
        {"ts_code": "301235.SZ", "name": "华康洁净", "sector": "其他"},
        {"ts_code": "300840.SZ", "name": "酷特智能", "sector": "其他"},
        {"ts_code": "300283.SZ", "name": "温州宏丰", "sector": "其他"},
        {"ts_code": "002297.SZ", "name": "博云新材", "sector": "其他"},
        {"ts_code": "002406.SZ", "name": "远东传动", "sector": "其他"},
        {"ts_code": "300599.SZ", "name": "雄塑科技", "sector": "其他"},
        {"ts_code": "003026.SZ", "name": "中晶科技", "sector": "其他"},
        {"ts_code": "600736.SH", "name": "苏州高新", "sector": "其他"},
        {"ts_code": "002217.SZ", "name": "合力泰", "sector": "其他"},
        {"ts_code": "000546.SZ", "name": "金圆股份", "sector": "其他"},
        {"ts_code": "300571.SZ", "name": "平治信息", "sector": "其他"},
        {"ts_code": "600379.SH", "name": "宝光股份", "sector": "其他"},
        {"ts_code": "301387.SZ", "name": "光大同创", "sector": "其他"},
        {"ts_code": "300687.SZ", "name": "赛意信息", "sector": "其他"},
        {"ts_code": "600433.SH", "name": "冠豪高新", "sector": "其他"},
        {"ts_code": "300553.SZ", "name": "集智股份", "sector": "其他"},
        {"ts_code": "300133.SZ", "name": "华策影视", "sector": "其他"},
        {"ts_code": "688545.SH", "name": "兴福电子", "sector": "其他"},
        {"ts_code": "600744.SH", "name": "华银电力", "sector": "其他"},
        {"ts_code": "002522.SZ", "name": "浙江众成", "sector": "其他"},
        {"ts_code": "002439.SZ", "name": "启明星辰", "sector": "其他"},
    ]

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

print(f"✅ 配置加载成功")
print(f"   股票池数量: {len(config.WATCHLIST)} 只")
print(f"   仓位管理: 单票{config.MAX_SINGLE_POSITION:.0%} | 板块{config.MAX_SECTOR_POSITION:.0%}")
print(f"   风控: 止损{config.STOP_LOSS:.0%} | 止盈{config.TAKE_PROFIT:.0%}")
