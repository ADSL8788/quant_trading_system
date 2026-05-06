import subprocess, sys
sys.path.insert(0, '/home/fafa6/auto_trading_system')
from auto_screener import AutoScreener
s = AutoScreener()
stocks = s.get_all_stocks()
tech = s.quick_technical_filter(stocks, top_n=300)
for _, row in tech.head(10).iterrows():
    subprocess.run(f"add {row['ts_code']} {row['name']}", shell=True)
