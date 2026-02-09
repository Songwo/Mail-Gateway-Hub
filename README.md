# 📧 Mail-Gateway-Hub 

> **「让 AI 替你读信，让通知回归本质。」**  
> **由 Gemini 1.5 Flash 驱动的全平台邮件智能网关。**

---

## 🚀 项目亮点

- 🤖 **AI 深度读信**: 接入 Gemini 1.5 Flash，秒级生成 50 字精简摘要，拒绝邮件焦虑。
- 🔢 **验证码自动提取**: 智能识别各类验证码，在飞书卡片中高亮显示。
- 🎭 **身份标签化**: 为不同邮箱配置别名（如“工作”、“社交”、“银行”），卡片页脚清晰区分。
- 📱 **飞书交互卡片**: 采用飞书高级卡片格式，重要邮件红色预警，支持移动端一键预览。
- ☁️ **极低资源占用**: 深度优化 `asyncio` 异步架构，10+ 邮箱并发运行内存仅约 80MB。
- 🛡️ **旧信防轰炸**: 智能过滤逻辑，只处理脚本启动后的新邮件。

---

## 📊 部署矩阵

| 模式 | 延迟 | 成本 | 复杂度 | 推荐场景 |
| :--- | :--- | :--- | :--- | :--- |
| **A: VPS/本地** | < 20s | 极低 | ★★☆ | 深度用户，管理 10+ 传统邮箱 |
| **B: GitHub Actions** | ~10min | **$0** | ★★★ | 追求极致白嫖，无需服务器 |
| **C: CF Workers** | **即时** | **$0** | ★☆☆ | 拥有自定义域名，零延迟转发 |

---

## 🛠️ 准备工作 (Hardcore Guide)

> [!IMPORTANT]
> **安全警告：严禁使用邮箱登录密码！**  
> 你必须在邮箱设置中开启 **IMAP** 服务，并获取 **“授权码”**（或称“应用专用密码”）。  
> [查看：如何获取 Gmail 应用专用密码?](https://support.google.com/accounts/answer/185833)

1. **AI 端**: 前往 [Google AI Studio](https://aistudio.google.com/) 获取免费的 Gemini API Key。
2. **推送端**: 飞书群 -> 设置 -> 机器人 -> 添加自定义机器人 -> 获取 **Webhook 地址**。  
   > [!TIP]
   > 飞书机器人安全设置建议选择「自定义关键词」，并填入 `邮件`。

---

## 📦 部署模式

### 模式 A：自建服务器 (VPS/Docker)
```bash
# 安装依赖
pip install -r requirements.txt
# 运行
python src/main.py
```

### 模式 B：GitHub Actions (Serverless)
1. **Fork** 本仓库。
2. 在 `Settings -> Secrets -> Actions` 中添加 `MAIL_CONFIG_JSON`。
3. 填入你的 `config.json` 完整内容。脚本将每 10 分钟自动巡检。

### 模式 C：Cloudflare Workers (Real-time)
1. 开启 **Email Routing** 转发至 Worker。
2. 部署 `workers/email-worker.js`。
3. 配置环境变量 `GEMINI_API_KEY` 和 `FEISHU_WEBHOOK`。

---

## ⚠️ 学生党避坑指南 (Troubleshooting)

> [!CAUTION]
> **1. 代理与 SSL 报错 (最常见)**  
> 很多同学使用 TUN 模式代理会导致 Python 抛出 `SSL: CERTIFICATE_VERIFY_FAILED`。  
> **解决**: 尝试关闭代理或在终端执行 `export NO_PROXY=localhost,127.0.0.1`。本项目代码已内置对常规代理的兼容性。

> [!WARNING]
> **2. Gemini 404 / 地区不可用**  
> 如果你的 VPS 位于香港或其他 Gemini 不支持的地区，会返回 404。  
> **解决**: 必须使用支持地区的代理（如美国、日本、新加坡），或者在 `config.json` 中配置代理服务器。

> [!IMPORTANT]
> **3. 飞书机器人“关键词不匹配”**  
> 如果日志显示推送成功但飞书没收到，大概率是关键词没设对。  
> **解决**: 确保飞书机器人关键词包含“邮件”二字，或者直接在卡片标题中包含你设置的关键词。

> [!TIP]
> **4. 旧信“轰炸”问题**  
> 第一次启动时，脚本会自动记录当前时间。它**只会**处理启动之后收到的未读邮件，不会把你邮箱里几年前的未读件全推出来。

---

## 🤝 贡献与感谢
灵感来源于 **Linux Do** 社区的极客精神。感谢所有为本项目提供灵感的“白嫖王”们！

---
*Developed with ❤️ for Geeks.*