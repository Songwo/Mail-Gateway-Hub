# Mail-Gateway-Hub 架构设计

## 1. 技术选型
- **语言:** Python 3.10+
- **IMAP 库:** `imap_tools` (支持 IDLE 和 简单的 API)
- **Web 框架:** `FastAPI` (用于接收飞书指令回调)
- **数据库:** `SQLite` (记录邮件处理状态)
- **AI:** `google-generativeai` (Gemini)
- **异步任务:** `Asyncio` + `Threaded Pool` (处理阻塞的 IMAP 操作)

## 2. 数据库设计 (SQLite)
```sql
CREATE TABLE processed_emails (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_email TEXT NOT NULL,
    mail_uid TEXT NOT NULL,
    summary TEXT,
    category TEXT,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_email, mail_uid)
);
```
