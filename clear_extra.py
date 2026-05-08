#!/usr/bin/env python3
"""清空 EXTRA_STOCKS 列表（保留空列表结构，不破坏语法）"""
import re
import sys

SETTINGS_FILE = "config/settings.py"

def clear_extra_stocks():
    try:
        with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则匹配 EXTRA_STOCKS = [...] 并替换为 EXTRA_STOCKS = []
        # 支持多行和空列表
        pattern = r'(EXTRA_STOCKS\s*=\s*)\[.*?\]'
        new_content = re.sub(pattern, r'\1[]', content, flags=re.DOTALL)
        
        if new_content == content:
            print("⚠️ 未找到 EXTRA_STOCKS 列表或已是空列表")
        else:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("✅ 已清空 EXTRA_STOCKS（手动添加的股票）")
    except Exception as e:
        print(f"❌ 清空失败: {e}")

if __name__ == "__main__":
    clear_extra_stocks()
