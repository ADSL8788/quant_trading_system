#!/usr/bin/env python3
"""微信推送模块 - 支持企业微信和Server酱"""
import requests
import json
from datetime import datetime
from loguru import logger

class WeChatPusher:
    """微信推送器"""
    
    def __init__(self):
        self.webhook_url = None
        self.server_chan_key = None
        self._init_config()
    
    def _init_config(self):
        """初始化配置"""
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        self.webhook_url = os.getenv('WECHAT_WEBHOOK', '')
        self.server_chan_key = os.getenv('SERVER_CHAN_KEY', '')
    
    def send_to_webhook(self, content):
        """通过企业微信机器人发送"""
        if not self.webhook_url:
            logger.warning("未配置企业微信webhook")
            return False
        
        try:
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "content": content
                }
            }
            response = requests.post(self.webhook_url, json=data, timeout=10)
            if response.status_code == 200:
                logger.info("✅ 企业微信推送成功")
                return True
        except Exception as e:
            logger.error(f"企业微信推送失败: {e}")
        
        return False
    
    def send_to_serverchan(self, title, content):
        """通过Server酱发送"""
        if not self.server_chan_key:
            logger.warning("未配置Server酱")
            return False
        
        try:
            url = f"https://sctapi.ftqq.com/{self.server_chan_key}.send"
            data = {
                "title": title,
                "desp": content
            }
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                logger.info("✅ Server酱推送成功")
                return True
        except Exception as e:
            logger.error(f"Server酱推送失败: {e}")
        
        return False
    
    def send_trading_summary(self, summary, decisions):
        """发送交易汇总"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 构建消息内容
        content = f"""
## 📊 量化交易日报
**时间**: {now}

### 💰 组合状态
- 总资产: {summary.get('total_value', 0):,.0f}
- 现金: {summary.get('cash', 0):,.0f}
- 持仓数: {summary.get('positions_count', 0)}
- 总收益: {summary.get('total_return', 0):+.2%}

### 📈 今日决策
"""
        for d in decisions[:10]:
            content += f"- {d}\n"
        
        if decisions:
            content += f"\n共 {len(decisions)} 条分析"
        
        # 发送
        self.send_to_webhook(content)
        self.send_to_serverchan(f"量化日报 {now[:10]}", content)
    
    def send_alert(self, title, message):
        """发送告警"""
        content = f"## ⚠️ {title}\n\n{message}"
        self.send_to_webhook(content)
        self.send_to_serverchan(title, message)

# 测试
if __name__ == "__main__":
    pusher = WeChatPusher()
    pusher.send_alert("测试", "量化交易系统已启动")
