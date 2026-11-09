import json, os

FILTER_FILE = os.path.join(os.path.dirname(__file__), 'config', 'filters.json')

DEFAULTS = {
    "yearline_filter":  {"enabled": True,  "desc": "年线过滤：股价须在250日均线上方"},
    "crowding_filter":  {"enabled": True,  "desc": "拥挤度约束：20日涨幅>40%降权"},
    "rsi_upper_filter": {"enabled": True,  "desc": "RSI上限：RSI>70剔除"},
    "pullback_filter":  {"enabled": True,  "desc": "回撤约束：20日高点回撤>15%剔除"},
    "volume_filter":    {"enabled": False, "desc": "量能过滤：量比<0.8剔除"},
    "moneyflow_rank":   {"enabled": True,  "desc": "资金流二次排序：V4C结果按近5日主力净流入重排"},
}

def load():
    if not os.path.exists(FILTER_FILE):
        save(DEFAULTS)
        return DEFAULTS
    with open(FILTER_FILE, encoding='utf-8') as f:
        data = json.load(f)
    for k, v in DEFAULTS.items():
        data.setdefault(k, v)
    return data

def save(data):
    os.makedirs(os.path.dirname(FILTER_FILE), exist_ok=True)
    with open(FILTER_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_on(name: str) -> bool:
    return load().get(name, {}).get("enabled", False)

def toggle_interactive():
    data = load()
    while True:
        print("\n" + "=" * 55)
        print("  过滤规则开关  (Y=启用 / N=关闭)")
        print("=" * 55)
        for i, (k, v) in enumerate(data.items(), 1):
            print(f"  {i}. [{'Y' if v['enabled'] else 'N'}]  {v['desc']}")
        print("  0. 保存并退出")
        print("=" * 55)
        c = input("选择要切换的编号: ").strip()
        if c == "0":
            save(data)
            print("✅ 开关已保存，下次运行 sc/kr 立即生效")
            break
        if c.isdigit() and 1 <= int(c) <= len(data):
            key = list(data.keys())[int(c) - 1]
            data[key]["enabled"] = not data[key]["enabled"]
            print(f"   → {key} 已切换为 {'Y' if data[key]['enabled'] else 'N'}")

def prompt_filter_switches():
    data = load()
    print("\n" + "=" * 55)
    print("  当前过滤规则状态")
    print("=" * 55)
    for i, (k, v) in enumerate(data.items(), 1):
        print(f"  {i}. [{'Y' if v['enabled'] else 'N'}]  {v['desc']}")
    print("=" * 55)
    ans = input("是否调整开关？(y/N，直接回车=保持当前并开始扫描): ").strip().lower()
    if ans != 'y':
        print("→ 使用当前开关状态开始扫描...\n")
        return
    while True:
        print()
        for i, (k, v) in enumerate(data.items(), 1):
            print(f"  {i}. [{'Y' if v['enabled'] else 'N'}]  {v['desc']}")
        print("  0. 保存并继续扫描")
        c = input("输入编号切换 Y/N（0=继续）: ").strip()
        if c == '0':
            save(data)
            print("✅ 开关已保存，开始扫描...\n")
            return
        if c.isdigit() and 1 <= int(c) <= len(data):
            key = list(data.keys())[int(c) - 1]
            data[key]["enabled"] = not data[key]["enabled"]
            print(f"   → {key}: {'Y' if data[key]['enabled'] else 'N'}")
