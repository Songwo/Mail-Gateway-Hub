from fastapi import FastAPI, Request
from imap_tools import MailBox
import json

app = FastAPI()

@app.post("/callback")
async def feishu_callback(request: Request):
    data = await request.json()
    # 飞书回调包含 value 字段
    action_value = data.get("action", {}).get("value", {})
    action = action_value.get("action") # "mark_read" or "delete"
    uid = action_value.get("uid")
    
    # 示例：执行删除
    if action == "delete":
        # 实际代码中应从 config 获取账号信息
        with MailBox('imap.gmail.com').login('user@gmail.com', 'password') as mailbox:
            mailbox.delete(uid)
            return {"text": f"邮件 {uid} 已成功删除"}
            
    return {"text": "指令已接收"}

# 运行: uvicorn callback_server:app --port 8000
