#!/usr/bin/env python3
"""批量删除预设池中的股票（仅从 EXTRA_STOCKS 中删除）"""
import sys
import os
import re

SETTINGS_FILE = "config/settings.py"

def remove_from_extra(ts_codes):
    """从 EXTRA_STOCKS 列表中删除指定股票代码（精确匹配）"""
    if not ts_codes:
        print("❌ 未提供股票代码")
        return False

    with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 定位 EXTRA_STOCKS 列表的起止行
    start_idx = -1
    end_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('EXTRA_STOCKS = ['):
            start_idx = i
        if start_idx != -1 and line.strip() == ']':
            end_idx = i
            break
    if start_idx == -1 or end_idx == -1:
        print("❌ 未找到 EXTRA_STOCKS 列表")
        return False

    # 提取列表内容（不含首尾行）
    extra_lines = lines[start_idx+1:end_idx]
    # 筛选要保留的行（不包含任一待删除代码的行）
    kept_lines = []
    removed = []
    for line in extra_lines:
        # 检查该行是否包含待删除的代码
        should_remove = False
        for code in ts_codes:
            if f'"{code}"' in line:
                should_remove = True
                removed.append(code)
                break
        if not should_remove:
            kept_lines.append(line)

    # 重新构建文件内容
    new_lines = lines[:start_idx+1] + kept_lines + lines[end_idx:]
    with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    # 输出结果
    if removed:
        print(f"✅ 已删除 {len(set(removed))} 只股票: {', '.join(set(removed))}")
    else:
        print("⚠️ 未找到匹配的股票")
    return True

def main():
    if len(sys.argv) < 2:
        print("用法: rmmulti <股票代码1> [股票代码2] ...")
        print("示例: rmmulti 000001.SZ 000002.SZ")
        print("或者从文件读取：cat codes.txt | xargs rmmulti")
        print("注意：只删除 EXTRA_STOCKS 中的股票，预设板块（电池、机器人等）不受影响")
        sys.exit(0)

    codes = sys.argv[1:]
    # 自动补全市场后缀（若无）
    formatted_codes = []
    for code in codes:
        if '.' not in code:
            if code.startswith(('60', '68')):
                formatted_codes.append(f"{code}.SH")
            else:
                formatted_codes.append(f"{code}.SZ")
        else:
            formatted_codes.append(code)
    remove_from_extra(formatted_codes)

if __name__ == "__main__":
    main()
