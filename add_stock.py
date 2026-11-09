#!/usr/bin/env python3
"""安全添加股票到手动池（JSON 存储）"""
import sys
import os
import json

MANUAL_JSON = "data/manual_stocks.json"

def get_stock_info(ts_code):
    try:
        import tushare as ts
        from dotenv import load_dotenv
        load_dotenv()
        ts.set_token(os.getenv('TUSHARE_TOKEN'))
        pro = ts.pro_api()
        df = pro.stock_basic(ts_code=ts_code, fields='name,industry')
        if not df.empty:
            name = df.iloc[0]['name']
            industry = df.iloc[0]['industry']
            sector = industry.replace('行业', '').strip() if industry else '其他'
            return name, sector
    except:
        pass
    return None, None

def migrate_old_extras():
    if os.path.exists(MANUAL_JSON):
        return
    old_settings = "config/settings.py"
    if not os.path.exists(old_settings):
        with open(MANUAL_JSON, 'w') as f:
            json.dump([], f)
        return
    print("🔁 迁移旧 EXTRA_STOCKS...")
    try:
        with open(old_settings, 'r') as f:
            content = f.read()
        import re
        pattern = r'EXTRA_STOCKS\s*=\s*(\[[\s\S]*?\n\])'
        match = re.search(pattern, content)
        if match:
            extra = eval(match.group(1))
            if isinstance(extra, list):
                with open(MANUAL_JSON, 'w') as f:
                    json.dump(extra, f, indent=2, ensure_ascii=False)
                print(f"✅ 迁移 {len(extra)} 只股票")
                return
    except Exception as e:
        print(f"⚠️ 迁移失败: {e}")
    with open(MANUAL_JSON, 'w') as f:
        json.dump([], f)

def load_manual_stocks():
    if not os.path.exists(MANUAL_JSON):
        migrate_old_extras()
    with open(MANUAL_JSON, 'r') as f:
        return json.load(f)

def save_manual_stocks(stocks):
    with open(MANUAL_JSON, 'w') as f:
        json.dump(stocks, f, indent=2, ensure_ascii=False)

def add_stock(ts_code, name=None, sector=None):
    if name is None:
        print(f"🔍 获取 {ts_code} 信息...")
        name, auto_sector = get_stock_info(ts_code)
        if name is None:
            print("❌ 无法自动获取名称")
            return False
        if sector is None:
            sector = auto_sector
        print(f"   名称: {name}, 板块: {sector}")
    if sector is None:
        sector = '其他'

    stocks = load_manual_stocks()
    for s in stocks:
        if s['ts_code'] == ts_code:
            print(f"⚠️ {ts_code} 已存在")
            return False

    stocks.append({"ts_code": ts_code, "name": name, "sector": sector})
    save_manual_stocks(stocks)
    print(f"✅ 已添加 {name} ({ts_code}) 到手动池 (共 {len(stocks)} 只)")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: add <代码> [名称] [板块]")
        sys.exit(0)
    ts_code = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else None
    sector = sys.argv[3] if len(sys.argv) > 3 else None
    if '.' not in ts_code:
        if ts_code.startswith(('60', '68')):
            ts_code = f"{ts_code}.SH"
        else:
            ts_code = f"{ts_code}.SZ"
    add_stock(ts_code, name, sector)
