#!/usr/bin/env python3
"""微信推送测试"""
import sys
sys.path.insert(0, '/home/fafa6/auto_trading_system')

from wechat_push import WeChatPusher

def main():
    pusher = WeChatPusher()
    print("=" * 50)
    print("📱 微信推送测试")
    print("=" * 50)
    print("发送中...")
    result = pusher.send_to_serverchan("测试消息", "Hello from quant system")
    if result:
        print("✅ 推送成功（Server酱）")
    else:
        print("❌ 推送失败，请检查 .env 中的 SERVER_CHAN_KEY")

if __name__ == "__main__":
    main()
