#!/usr/bin/env python3
"""安全添加股票到预设池（支持空列表，直接操作行）"""
import sys
import os
from config.settings import config

SETTINGS_FILE = "config/settings.py"

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

def add_stock(ts_code, name=None, sector=None):
    if name is None:
        print(f"🔍 获取 {ts_code} 信息...")
        name, auto_sector = get_stock_info(ts_code)
        if name is None:
            print("❌ 无法自动获取名称，请手动提供名称")
            return False
        if sector is None:
            sector = auto_sector
        print(f"   名称: {name}, 板块: {sector}")

    if sector is None:
        sector = '其他'

    with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 查找 EXTRA_STOCKS 定义行
    extra_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith('EXTRA_STOCKS ='):
            extra_idx = i
            break

    if extra_idx is None:
        print("❌ 未找到 EXTRA_STOCKS 定义")
        return False

    # 检查是否已存在
    for line in lines:
        if f'"{ts_code}"' in line:
            print(f"⚠️ {ts_code} 已在预设池中")
            return False

    # 处理 EXTRA_STOCKS = [] 在同一行的情况
    line = lines[extra_idx]
    if '[]' in line:
        # 把 "EXTRA_STOCKS = []" 替换为 "EXTRA_STOCKS = [\n    ...\n    ]"
        indent = line[:line.index('E')]  # 保留原有缩进
        new_line = f'{indent}EXTRA_STOCKS = [\n'
        new_line += f'{indent}    {{"ts_code": "{ts_code}", "name": "{name}", "sector": "{sector}"}},\n'
        new_line += f'{indent}]\n'
        lines[extra_idx] = new_line
    else:
        # 列表已跨多行，找到结束的 ] 并在之前插入新行
        end_idx = extra_idx
        for i in range(extra_idx+1, len(lines)):
            if ']' in lines[i] and not lines[i].strip().startswith('EXTRA_STOCKS'):
                end_idx = i
                break
        # 在 end_idx 行之前插入（保持缩进）
        indent = lines[extra_idx][:lines[extra_idx].index('E')]
        new_line = f'{indent}    {{"ts_code": "{ts_code}", "name": "{name}", "sector": "{sector}"}},\n'
        lines.insert(end_idx, new_line)

    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"✅ 已添加 {name} ({ts_code}) 到 EXTRA_STOCKS")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: add <股票代码> [股票名称] [板块名]")
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
