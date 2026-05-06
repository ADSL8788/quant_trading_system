#!/bin/bash
cd ~/auto_trading_system
source venv/bin/activate
REPORT=$(python three_tools_system_final.py 2>&1)
echo "$REPORT"
python -c "
from wechat_push import WeChatPusher
pusher = WeChatPusher()
content = '''$REPORT'''[:2000]
pusher.send_to_serverchan('深度分析报告', content)
"
