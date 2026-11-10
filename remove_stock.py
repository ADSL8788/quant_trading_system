#!/usr/bin/env python3
"""从手动池（data/manual_stocks.json）删除股票"""
import sys, json, os

JSON_PATH = os.path.join(os.path.dirname(__file__), 'data', 'manual_stocks.json')

def remove_stock(ts_code):
    if not os.path.exists(JSON_PATH):
        print(f"❌ 未找到 {JSON_PATH}")
        return False
    with open(JSON_PATH, encoding='utf-8') as f:
        data = json.load(f)
    before = len(data)
    data = [s for s in data if s.get('ts_code') != ts_code]
    if len(data) == before:
        print(f"⚠️ {ts_code} 不在手动池中")
        return False
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"✅ 已删除 {ts_code}（手动池 {before} → {len(data)}）")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: remove <股票代码>")
        sys.exit(0)
    code = sys.argv[1]
    if '.' not in code:
        code = code + ('.SH' if code.startswith(('60','68')) else '.SZ')
    remove_stock(code)
