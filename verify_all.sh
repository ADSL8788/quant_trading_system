#!/bin/bash
# 一键批量验证所有量化交易系统命令

cd ~/auto_trading_system
source venv/bin/activate

echo "=========================================="
echo "量化交易系统 - 全命令一键验证"
echo "=========================================="
echo "开始时间: $(date)"
echo

# 定义测试结果
declare -A results
declare -A reasons

# 测试函数
test_cmd() {
    local cmd="$1"
    local desc="$2"
    local test_action="$3"
    echo -n "测试 $desc ($cmd) ... "
    if eval "$test_action" &> /tmp/verify_${cmd// /_}.log; then
        echo "✅ 通过"
        results["$cmd"]="PASS"
    else
        local exit_code=$?
        echo "❌ 失败 (exit $exit_code)"
        results["$cmd"]="FAIL"
        reasons["$cmd"]="$(tail -1 /tmp/verify_${cmd// /_}.log 2>/dev/null | cut -c1-100)"
    fi
}

# 1. 核心分析命令
test_cmd "kr" "快速技术分析 (kr 000001)" "python quick.py 000001"
test_cmd "tr" "完整三工具分析 (仅检查导入)" "python -c 'from three_tools_system_final import ThreeToolsTradingSystem; print(\"OK\")'"
test_cmd "an" "单股深度分析 (an 000001)" "python analyze_one.py 000001 平安银行 | head -20"
test_cmd "dexs" "Dexter 基本面研究" "python dex_stock.py 000001 平安银行 | head -10"
test_cmd "dex" "Dexter 预设池分析" "python dex_analysis.py | head -10"

# 2. 全市场扫描与选股
test_cmd "sc" "全市场快速扫描 (前10只)" "python auto_screener.py | head -20"
test_cmd "hot" "技术面最强10只" "python hot_stocks.py | head -10"
test_cmd "codes" "仅输出股票代码" "python codes.py | head -5"
test_cmd "myscan" "手工扫描 (模块导入测试)" "python -c 'import manual_scan'"

# 3. 股票池管理
test_cmd "lst" "查看自选池" "python list_stocks.py"
test_cmd "add" "添加股票 (平安银行)" "python add_stock.py 000001 平安银行 && python remove_stock.py 000001"
test_cmd "rmm" "删除股票" "python remove_stock.py 000001"  # 不存在的也返回成功
test_cmd "clr" "清空手动股票" "python clear_extra.py"
test_cmd "aad" "批量添加 (需扫描结果)" "python batch_add_from_csv.py 2"

# 4. 微信推送与日志
test_cmd "wx" "微信推送测试 (只检查导入)" "python -c 'from wechat_push import WeChatPusher; print(\"WeChat module OK\")'"
test_cmd "log" "查看日志" "tail -5 logs/trading.log"

# 5. 辅助命令
test_cmd "krui" "Kronos WebUI (检查脚本存在)" "test -f Kronos/webui/run.py"
test_cmd "alias" "快速分析脚本存在" "test -f quick.py"

echo
echo "=========================================="
echo "验证结果汇总"
echo "=========================================="
pass_count=0
fail_count=0
for cmd in "${!results[@]}"; do
    if [ "${results[$cmd]}" == "PASS" ]; then
        echo "✅ $cmd : 通过"
        ((pass_count++))
    else
        echo "❌ $cmd : 失败 - ${reasons[$cmd]}"
        ((fail_count++))
    fi
done
echo
echo "通过: $pass_count, 失败: $fail_count"
echo "结束时间: $(date)"
echo "详细日志请查看 /tmp/verify_*.log"
