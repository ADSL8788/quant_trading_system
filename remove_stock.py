#!/usr/bin/env python3
"""从预设池中删除股票（从 EXTRA_STOCKS 移除）"""
import sys
import re

SETTINGS_FILE = "config/settings.py"

def remove_stock(ts_code):
    with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    found = False
    for line in lines:
        if f'"{ts_code}"' in line:
            found = True
            continue
        new_lines.append(line)

    if not found:
        print(f"⚠️ {ts_code} 不在预设池中")
        return False

    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"✅ 已删除 {ts_code}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: remove <股票代码>")
        print("示例: remove 300906")
        sys.exit(0)

    ts_code = sys.argv[1]
    if '.' not in ts_code:
        if ts_code.startswith(('60', '68')):
            ts_code = f"{ts_code}.SH"
        else:
            ts_code = f"{ts_code}.SZ"

    remove_stock(ts_code)
