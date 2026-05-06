#!/usr/bin/env python3
"""安全添加股票到预设池（放入 EXTRA_STOCKS 列表）"""
import sys
import os
import re
import tushare as ts
from config.settings import config

SETTINGS_FILE = "config/settings.py"

def get_stock_info(ts_code):
    try:
        pro = ts.pro_api(config.TUSHARE_TOKEN)
        df = pro.stock_basic(ts_code=ts_code, fields='name,industry')
        if not df.empty:
            name = df.iloc[0]['name']
            industry = df.iloc[0]['industry']
            sector = industry.replace('行业', '').strip() if industry else '其他'
            return name, sector
    except Exception as e:
        print(f"⚠️ 获取失败: {e}")
    return None, None

def add_stock(ts_code, name=None, sector=None):
    if name is None:
        print(f"🔍 获取 {ts_code} 信息...")
        name, auto_sector = get_stock_info(ts_code)
        if name is None:
            print("❌ 无法获取，请手动指定名称")
            return False
        if sector is None:
            sector = auto_sector
        print(f"   名称: {name}, 板块: {sector}")

    if sector is None:
        sector = '其他'

    with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 检查是否已存在
    for line in lines:
        if f'"{ts_code}"' in line:
            print(f"⚠️ {ts_code} 已在预设池中")
            return False

    # 查找 EXTRA_STOCKS 列表
    extra_index = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('EXTRA_STOCKS = ['):
            extra_index = i
            break

    if extra_index == -1:
        print("❌ 未找到 EXTRA_STOCKS 列表")
        return False

    # 找到列表结束位置
    end_index = extra_index
    for i in range(extra_index + 1, len(lines)):
        if lines[i].strip() == ']' or lines[i].strip().startswith(']'):
            end_index = i
            break

    indent = '    '
    new_line = f'{indent}{{"ts_code": "{ts_code}", "name": "{name}", "sector": "{sector}"}},\n'
    lines.insert(end_index, new_line)

    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    print(f"✅ 已添加 {name} ({ts_code}) 到 EXTRA_STOCKS")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: add <股票代码> [股票名称] [板块名]")
        print("示例: add 300750                # 自动获取名称和板块")
        print("      add 600519 贵州茅台       # 自动获取板块")
        print("      add 002273 水晶光电 元器件")
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
