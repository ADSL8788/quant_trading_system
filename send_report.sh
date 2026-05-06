#!/bin/bash
cd ~/auto_trading_system
source venv/bin/activate
python quick.py > /tmp/report.txt
cat /tmp/report.txt
# 发送到微信（需要先配置 SERVER_CHAN_KEY）
python -c "
import os
from wechat_push import WeChatPusher
with open('/tmp/report.txt', 'r') as f:
    content = f.read()
pusher = WeChatPusher()
pusher.send_to_serverchan('量化报告', content[:2000])
"
