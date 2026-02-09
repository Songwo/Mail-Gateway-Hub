import asyncio
import argparse
import json
import sqlite3
import sys
import traceback
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional

import requests
import google.generativeai as genai
from imap_tools import MailBox, AND
from loguru import logger

# ===========================
# 0. 全局变量与日志配置
# ===========================
SCRIPT_START_TIME = datetime.now()
DB_PATH = "mail_gateway.db"
CONFIG_FILE = "config.json"

logger.remove()
logger.add(sys.stdout, colorize=True, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{message}</cyan>")
logger.add("mail_gateway.log", rotation="10 MB", retention="7 days")

# ===========================
# 1. 核心配置与数据库
# ===========================
def load_config() -> Dict:
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"❌ [CONFIG] 配置文件 '{CONFIG_FILE}' 未找到！")
        sys.exit(1)

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS processed_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_email TEXT NOT NULL,
                alias TEXT,
                uid TEXT NOT NULL,
                category TEXT,
                summary TEXT,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(account_email, uid)
            )
        ''')
        try:
            conn.execute("ALTER TABLE processed_emails ADD COLUMN alias TEXT")
        except sqlite3.OperationalError:
            pass 

def is_processed(email: str, uid: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM processed_emails WHERE account_email=? AND uid=?", (email, uid))
        return cur.fetchone() is not None

def save_result(email: str, alias: str, uid: str, ai_result: Dict):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            INSERT OR IGNORE INTO processed_emails 
            (account_email, alias, uid, category, summary) 
            VALUES (?, ?, ?, ?, ?)
        """, (email, alias, uid, ai_result.get('category'), ai_result.get('summary')))

def get_db_stats(limit=15):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM processed_emails ORDER BY processed_at DESC LIMIT ?", (limit,))
        return [dict(row) for row in cursor.fetchall()]

# ===========================
# 2. 异步 IO 包装 (AI & 推送)
# ===========================
executor = ThreadPoolExecutor(max_workers=10)

async def async_call_gemini(content: str, config: Dict) -> Dict:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, _sync_call_gemini, content, config)

def _sync_call_gemini(content: str, config: Dict) -> Dict:
    api_key = config.get("gemini_api_key")
    if not api_key:
        return {"category": "未配置AI", "summary": "未配置 Gemini API Key", "priority": 1}
    
    genai.configure(api_key=api_key)
    
    target_models = ['gemini-1.5-flash-latest', 'gemini-1.5-flash', 'gemini-pro']
    model_to_use = "gemini-1.5-flash-latest"
    
    try:
        # 尝试发现可用模型
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        for tm in target_models:
            if f"models/{tm}" in available_models:
                model_to_use = tm
                break
        
        model = genai.GenerativeModel(model_to_use)
        prompt = f"{config.get('system_prompt', '')}\nEmail Content: {content[:3000]}\nOutput JSON ONLY."
        resp = model.generate_content(prompt)
        text = resp.text.replace('```json', '').replace('```', '').strip()
        return json.loads(text)
    except Exception:
        logger.error(f"❌ [AI] Gemini 调用失败 (尝试模型: {model_to_use})")
        logger.error(traceback.format_exc())
        return {"category": "AI Error", "summary": "解析失败", "priority": 1}

async def async_send_feishu(msg_data: Dict, ai_result: Dict, config: Dict, account_cfg: Dict):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(executor, _sync_send_feishu, msg_data, ai_result, config, account_cfg)

def _sync_send_feishu(msg_data: Dict, ai_result: Dict, config: Dict, account_cfg: Dict):
    webhook = config.get("feishu_webhook")
    if not webhook: return

    alias = account_cfg.get('alias', '默认')
    category = ai_result.get('category', '其他')
    is_urgent = category in ["验证码", "重要通知"] or ai_result.get('priority', 0) >= 4
    header_color = "red" if is_urgent else "blue"
    
    email = account_cfg['email']
    summary = ai_result.get('summary', '无摘要')
    v_code = ai_result.get('verification_code')
    
    content_md = f"**摘要**: {summary}\n**发件人**: {msg_data['from']}"
    if v_code and str(v_code).lower() != "null":
        content_md += f"\n\n**验证码**: <font color='red'>{v_code}</font>"

    payload = {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": header_color,
                "title": {"tag": "plain_text", "content": f"[{alias}] {msg_data['subject']}"}
            },
            "elements": [
                {"tag": "div", "text": {"tag": "lark_md", "content": content_md}},
                {"tag": "hr"},
                {
                    "tag": "note", 
                    "elements": [
                        {"tag": "plain_text", "content": f"📍 身份: {alias} | 账号: {email}\n🤖 由 Mail-Gateway-Hub 驱动"}
                    ]
                }
            ]
        }
    }
    try:
        requests.post(webhook, json=payload, timeout=10)
    except Exception:
        logger.error("❌ [NOTIFY] 飞书推送网络异常！")

# ===========================
# 3. 核心业务逻辑
# ===========================
async def check_account(acc: Dict, global_config: Dict):
    email = acc['email']
    alias = acc.get('alias', 'Unknown')
    server = acc['imap_server']
    
    logger.info(f"🔍 [CONN] 正在检查: [{alias}] ({email})...")
    
    loop = asyncio.get_running_loop()
    try:
        def fetch_unread():
            with MailBox(server).login(email, acc['password'], initial_folder=acc.get('folder', 'INBOX')) as mb:
                msgs = []
                for m in mb.fetch(AND(seen=False)):
                    msg_date = m.date.replace(tzinfo=None)
                    if msg_date < SCRIPT_START_TIME.replace(tzinfo=None):
                        continue
                    msgs.append({
                        "uid": m.uid, "subject": m.subject, "from": m.from_,
                        "content": m.text or m.html or ""
                    })
                return msgs

        messages = await loop.run_in_executor(executor, fetch_unread)
        
        if not messages:
            logger.debug(f"✨ [{alias}] 无新邮件。")
            return

        logger.success(f"📩 [{alias}] 发现 {len(messages)} 封新邮件！")

        for msg in messages:
            if is_processed(email, msg['uid']):
                continue
            ai_result = await async_call_gemini(msg['content'], global_config)
            await async_send_feishu(msg, ai_result, global_config, acc)
            save_result(email, alias, msg['uid'], ai_result)
            logger.success(f"✅ [{alias}] 处理成功: {msg['subject']}")
            await asyncio.sleep(2) # 频率限制

    except Exception:
        logger.error(f"❌ [{alias}] 连接或处理错误！")
        logger.error(traceback.format_exc())

async def scheduler(config: Dict, run_once: bool = False):
    accounts = config.get('accounts', [])
    if not accounts:
        logger.error("❌ [SYSTEM] 未配置账号。")
        return

    if run_once:
        logger.info("🕒 [SYSTEM] 执行单次扫描模式...")
        await asyncio.gather(*[check_account(acc, config) for acc in accounts])
    else:
        logger.success(f"🚀 [SYSTEM] 正在监听 {len(accounts)} 个邮箱...")
        while True:
            await asyncio.gather(*[check_account(acc, config) for acc in accounts])
            logger.info("💓 [HEARTBEAT] 监听中，20秒后下一轮...")
            await asyncio.sleep(20)

# ===========================
# 4. 入口
# ===========================
if __name__ == "__main__":
    init_db()
    parser = argparse.ArgumentParser(description="Mail-Gateway-Hub")
    parser.add_argument("--list", action="store_true", help="显示最近处理记录")
    parser.add_argument("--once", action="store_true", help="单次扫描后退出")
    args = parser.parse_args()

    if args.list:
        stats = get_db_stats()
        print(f"\n{'时间':<20} | {'别名':<10} | {'分类':<10} | {'摘要'}")
        print("-" * 100)
        for s in stats:
            print(f"{s['processed_at']:<20} | {s['alias']:<10} | {s['category']:<10} | {s['summary']}")
        print()
        sys.exit(0)

    config = load_config()
    try:
        asyncio.run(scheduler(config, run_once=args.once))
    except KeyboardInterrupt:
        logger.warning("🛑 [SYSTEM] 服务已停止。")
