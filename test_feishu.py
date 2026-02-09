import requests
import json

# === 请填入你的飞书 Webhook 链接 ===
FEISHU_WEBHOOK = "https://open.feishu.cn/open-apis/bot/v2/hook/de976dde-04d4-407e-a1a0-3349c01445b9"

def test_push():
    payload = {
        "msg_type": "interactive",
        "card": {
            "header": {
                "template": "green",
                "title": {"tag": "plain_text", "content": "🚀 Mail-Gateway-Hub 测试成功"}
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "**Hello L站！**这是来自 Mail-Gateway-Hub 的第一条测试消息。如果你能看到这张卡片，说明 Webhook 配置完全正确！"
                    }
                },
                {"tag": "hr"},
                {
                    "tag": "note",
                    "elements": [{"tag": "plain_text", "content": "🤖 由 Mail-Gateway-Hub 驱动"}]
                }
            ]
        }
    }
    
    try:
        resp = requests.post(FEISHU_WEBHOOK, json=payload)
        if resp.status_code == 200:
            print("✅ 推送成功！请查看你的飞书群。")
        else:
            print(f"❌ 推送失败，错误代码: {resp.status_code}, 响应: {resp.text}")
    except Exception as e:
        print(f"❌ 连接异常: {e}")

if __name__ == "__main__":
    if "YOUR_" in FEISHU_WEBHOOK:
        print("💡 请先在脚本中填入真实的 FEISHU_WEBHOOK 链接！")
    else:
        test_push()
