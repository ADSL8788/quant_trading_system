#!/bin/bash
cd ~/auto_trading_system
source venv/bin/activate
REPORT=$(python quick.py 2>&1)
echo "$REPORT"
python -c "
from wechat_push import WeChatPusher
pusher = WeChatPusher()
content = '''$REPORT'''[:2000]
pusher.send_to_serverchan('KRONOS快报', content)
"
