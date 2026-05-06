# 量化交易系统 (Kronos + Dexter + TradingAgents)

基于三智能体的A股量化分析系统，集成了技术预测（Kronos）、基本面研究（Dexter）和多智能体决策（TradingAgents），支持全市场扫描、数据缓存、回测、微信推送等功能。

## 📌 项目简介

- **Kronos**：时序模型预测股价趋势，输出 BUY/SELL/HOLD 信号及置信度。
- **Dexter**：DeepSeek 驱动的基本面研究，生成财务、估值、风险报告。
- **TradingAgents**：多角色智能体（技术、基本面、风控、交易员、总监）辩论，输出最终交易决策。
- **全市场扫描**：多因子技术面筛选，候选股一键加入自选池。
- **数据缓存**：本地 Parquet 缓存，二次分析秒级响应。
- **回测框架**：基于 Backtrader，验证策略历史表现。
- **实盘模拟**：模拟交易，计算总资产、收益率、持仓。
- **微信推送**：支持 Server酱 / 企业微信，可定时推送晨报。

## 🚀 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/你的用户名/quant_trading_system.git
cd quant_trading_system

2. 安装第三方核心工具
# 必须克隆三个独立项目（系统依赖）
git clone https://github.com/shiyu-coder/Kronos.git
git clone https://github.com/TauricResearch/TradingAgents.git
git clone https://github.com/virattt/dexter.git


3. 创建虚拟环境并安装 Python 依赖
python -m venv venv
source venv/bin/activate        # Linux/Mac
# .\venv\Scripts\activate       # Windows
pip install -r requirements.txt

4. 配置环境变量
# Tushare 数据接口 Token（必须）
TUSHARE_TOKEN=你的tushare_token

# DeepSeek API Key（必须，用于 Dexter）
DEEPSEEK_API_KEY=你的deepseek_key

# Server酱 SendKey（可选，用于微信推送）
SERVER_CHAN_KEY=你的serverchan_key
若无 .env.example，请手动创建 .env 文件，内容如上。
5. 预热缓存（首次运行）
bash
python preheat_cache.py   # 可选，下载预设池的K线数据
📖 常用命令（别名）
命令	功能	示例
kr	快速分析预设池（仅 Kronos）	kr 或 kr 300750
tr	完整三工具分析（预设池）	tr
an	单股深度分析（含完整报告）	an 300750 宁德时代
anv	单股详细分析（更冗长）	anv 000858 五粮液
dex	Dexter 分析预设池前5只	dex
dexs	Dexter 分析指定股票	dexs 600150 中国船舶
sc	全市场快速扫描（技术面）	sc
scfull	全市场完整扫描（全部股票）	scfull
sim	实盘模拟交易	sim
wx	测试微信推送	wx
log	查看最近50条日志	log
lst	列出预设股票池（含板块）	lst
add	添加股票到预设池	add 600186 莲花控股
remove	删除预设池中的股票	remove 600186
hot	输出技术面最强10只股票	hot
codes	仅输出技术面最强10只股票代码	codes
addhot	一键添加最强10只到预设池	addhot
所有命令已集成虚拟环境激活，直接输入即可。

🧪 运行回测
bash
python run_backtest.py
回测策略为 Kronos 信号 + 趋势过滤 + 动态止损，输出初始/最终资金、交易记录。

📁 项目结构
text
.
├── analysis_layer/           # Kronos 预测模块
├── data_layer/               # Tushare 数据客户端（带缓存）
├── config/                   # 配置文件（settings.py）
├── .env                      # 环境变量（需自行创建，已忽略）
├── three_tools_system_final.py   # 三工具主程序（tr）
├── quick.py                       # 快速分析（kr）
├── analyze_one.py                 # 单股深度分析（an）
├── auto_screener.py               # 全市场扫描（sc）
├── backtest_strategy.py           # 回测策略类
├── run_backtest.py                # 回测执行脚本
├── wechat_push.py                 # 微信推送模块
├── ……
⚠️ 注意事项
首次运行 kr 或 sc 会自动获取并缓存K线数据，后续分析秒级响应。

Dexter 和 TradingAgents 调用 DeepSeek API，每次分析耗时约30秒，请耐心等待。

微信推送免费版每天仅5条，建议仅推送重要信号。

若需全市场完整扫描，运行 scfull 约需数小时，建议夜间执行。

📄 License
MIT

text
