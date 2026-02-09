# 📧 Mail-Gateway-Hub：飞书 + Gemini 的邮件智能网关（超详细手把手版）
 
> **目标一句话**：自动读取邮箱邮件，用 Gemini 总结，推送飞书交互卡片；在飞书里一键 **标为已读 / 彻底删除**。

---

## ✅ 你将得到什么
- **AI 摘要**：几秒内把邮件变成一句话重点。
- **纯通知模式**：飞书里直接收到摘要提醒（无需公网回调）。
- **验证码高亮**：验证码邮件一眼识别。
- **多邮箱支持**：QQ/163/Gmail 等任意支持 IMAP 的邮箱。
- **防漏机制**：强制拉取 UNSEEN 邮件，时间窗口放宽，避免漏信。

---

## 🧭 新手村第一步：三件事先准备好
1. **Gemini API Key**
2. **邮箱授权码（不是登录密码）**
3. **飞书机器人 Webhook + 交互回调地址**

下面一条条喂到嘴里。

---

# ① Gemini API 申请（免费）

## 步骤
1. 打开 Google AI Studio。
2. 登录你的 Google 账号。
3. 点击左侧 **Get API key** → **Create API key in new project**。
4. 复制 API Key，保存到本地（等下放进 `config.json`）。

> [!IMPORTANT]
> **如果在国内访问不到 Gemini**，后面要用 `use_proxy` 配置“科学上网”代理。

---

# ② 邮箱授权码获取（QQ / 163 / Gmail 对比图描述）

> [!CAUTION]
> **脚本里填写的是“授权码”，不是邮箱登录密码！**

| 邮箱 | 获取入口 | “对比图描述”（你看到的页面大概长这样） | 要点 |
| --- | --- | --- | --- |
| **QQ 邮箱** | 设置 → 账号 → POP3/IMAP/SMTP | 右侧有“开启服务”的开关，下面有“生成授权码”按钮 | 开启 IMAP / POP3，短信验证后得到授权码 |
| **163 邮箱** | 设置 → POP3/SMTP/IMAP | 页面中部有“开启服务”，点击后弹出 16 位授权码 | 授权码只显示一次，务必复制保存 |
| **Gmail** | Google 账号 → 安全 | 先看到“2-Step Verification”，开启后出现“App Passwords” | 必须先开 2FA，再生成 App Password |

> [!TIP]
> Gmail 的授权码名称可以填 `Mail-Gateway-Hub`，只是备注用。

---

# ③ 飞书配置（只需 Webhook）

## A. 获取 Webhook（必须）
1. 进入飞书群聊 → 右上角 `...` → 群机器人 → 添加机器人。
2. 选择 **自定义机器人** → 设置名字（如“邮件助手”）。
3. 复制生成的 **Webhook**。

> [!NOTE]
> 目前是**纯通知模式**，不需要飞书回调服务器，也就不需要公网 IP。

---

# 🚀 一键部署流（本地/VPS + GitHub Actions + Cloudflare）

## 方案 A：本地 / VPS（强烈推荐）

### 1. 创建虚拟环境
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate
```

### 2. 安装依赖（建议国内换源）
```bash
pip install -r src/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 配置 `config.json`
复制模板：
```bash
copy config.json.example config.json
# Linux / macOS
cp config.json.example config.json
```

### 4. 启动服务（监听邮箱）
```bash
python src/main.py
```

### 5. 后台挂起（VPS）
```bash
nohup python src/main.py > mail_gateway.log 2>&1 &
```

---

## 方案 B：GitHub Actions 自动化（白嫖党首选）

### 1. Fork 本仓库
点击右上角 Fork。

### 2. 配置加密环境变量（Secrets）
1. 进入你的仓库 → `Settings` → `Secrets and variables` → `Actions`  
2. 点击 **New repository secret**  
3. 填写：
   - **Name**: `MAIL_CONFIG_JSON`
   - **Value**: 你的 `config.json` 完整内容（原样粘贴）

> [!NOTE]
> GitHub 会自动加密 Secrets，你的 `config.json` 不会被他人看到。

### 3. 触发工作流
1. 进入 `Actions` 页面  
2. 点击 `Check Mail` → **Run workflow**

---

## 方案 C：Cloudflare 配置详解（让回调有公网地址）

> 目的：让飞书能访问你的 `http://你的域名/callback`

### 方式 1：DNS 解析到 VPS
1. 在 Cloudflare 添加域名。
2. DNS 里新增 A 记录：  
   - Name：`mail`  
   - IPv4：你的 VPS 公网 IP  
   - 代理状态：可开启（橙云）
3. 回调地址填写：  
   `https://mail.你的域名/callback`

### 方式 2：Cloudflare Tunnel（适合本地电脑）
1. 安装 `cloudflared`。
2. 创建 Tunnel 并绑定到本地端口 8000。
3. 获得一个公网域名，如：  
   `https://xxx.trycloudflare.com/callback`

> [!TIP]
> 如果你是本地部署，又没有固定公网 IP，Tunnel 是最省事的方法。

---

# 📖 配置字典深度解析（大白话版本）

> 下面的解释 **每一个字段都解释清楚**，不用猜。

```json
{
  "gemini_api_key": "你的Gemini API Key",
  "feishu_webhook": "飞书机器人Webhook地址",
  "use_proxy": "http://127.0.0.1:7890",
  "system_prompt": "（可选）自定义AI系统提示词",
  "accounts": [
    {
      "alias": "生活号",
      "email": "xxx@qq.com",
      "password": "授权码",
      "imap_server": "imap.qq.com",
      "folder": "INBOX"
    }
  ]
}
```

| 字段 | 必填 | 作用 | 大白话解释 |
| --- | --- | --- | --- |
| `gemini_api_key` | ✅ | AI 密钥 | 没它 AI 不会工作 |
| `feishu_webhook` | ✅ | 飞书推送地址 | 机器人发消息就是靠它 |
| `use_proxy` | ❌ | 代理 | **国内网络访问 Gemini 常常需要科学上网**，填你的代理地址 |
| `system_prompt` | ❌ | 提示词 | 控制 AI 的风格，比如“请用一句话总结” |
| `accounts` | ✅ | 邮箱列表 | 可以配置多个邮箱 |
| `alias` | ✅ | 显示名称 | 飞书卡片上显示的标题 |
| `email` | ✅ | 邮箱地址 | 登录用 |
| `password` | ✅ | 授权码 | **不是登录密码** |
| `imap_server` | ✅ | IMAP 服务器 | 不同邮箱不同，比如 `imap.qq.com` |
| `folder` | ❌ | 目录 | 默认 `INBOX`，垃圾箱/订阅箱需手动写 |

> [!IMPORTANT]
> `use_proxy` 的逻辑：  
> - **不填**：默认直连 Gemini  
> - **填写**：所有 Gemini 请求会走这个代理  
> - 代理格式示例：`http://127.0.0.1:7890`

---

# 🧪 本地测试（建议先走一遍）

```bash
python src/main.py --once
```

看到类似日志：
```
发现 X 封未处理新邮件
处理成功: 主题xxx
```
说明功能正常。

---

# 🆘 排坑 FAQ（别怕，一条条排）

> [!WARNING]
> **Q1: 收不到提醒怎么办？**
> - 检查邮箱是否开启 IMAP  
> - 邮件是否处于 **未读（UNSEEN）** 状态  
> - 确认脚本一直在运行（非 `--once` 模式）  
> - 邮件是否在 `INBOX`，如果在订阅/广告箱，请在 `folder` 指定目录  
> - 如果你手动点了“已读”，脚本不会再抓到

> [!WARNING]
> **Q2: SSL 证书报错？**
> - 可能是 Gemini 在你地区不可访问  
> - 配置 `use_proxy` 走代理  
> - Actions 部署在海外，一般不需要代理  

> [!NOTE]
> **Q4: 为什么说“未找到对应账号配置”？**
> - 飞书回调里带的是邮箱地址，请确保 `config.json` 里邮箱正确  

---

# 📦 命令速查（小白版）

| 目的 | 命令 |
| --- | --- |
| 一次性扫描 | `python src/main.py --once` |
| 常驻监听 | `python src/main.py` |
| 查看最近记录 | `python src/main.py --list` |
| VPS 挂起 | `nohup python src/main.py > mail_gateway.log 2>&1 &` |

---

# 🤝 贡献
欢迎提 PR / issue。喜欢的话点个 ⭐！
