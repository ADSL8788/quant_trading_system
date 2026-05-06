import os
import tushare as ts
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("TUSHARE_TOKEN")
if not token:
    print("错误：请先在.env文件中设置TUSHARE_TOKEN")
    exit(1)

ts.set_token(token)
pro = ts.pro_api()

print("正在测试Tushare连接...")
try:
    # 获取股票列表（测试连接）
    df = pro.stock_basic(exchange='SSE', list_status='L', fields='ts_code,name')
    print(f"✅ 连接成功！获取到 {len(df)} 只股票")
    print("\n前5只股票:")
    print(df.head())
except Exception as e:
    print(f"❌ 连接失败: {e}")
