export default {
  async email(message, env, ctx) {
    const rawEmail = await new Response(message.raw).text();
    const subject = message.headers.get("subject") || "无主题";
    const from = message.from;

    // 1. 调用 Gemini API 进行摘要
    const aiResult = await summarizeEmail(rawEmail, subject, env);

    // 2. 推送至飞书
    await pushToFeishu(from, subject, aiResult, env);
  }
};

async function summarizeEmail(content, subject, env) {
  const url = `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent?key=${env.GEMINI_API_KEY}`;
  
  const systemPrompt = env.SYSTEM_PROMPT || "你是一个助手，请总结邮件内容并返回JSON格式：{"category":"...","summary":"...","priority":1-5}";
  const prompt = `${systemPrompt}
邮件主题: ${subject}
邮件内容: ${content.slice(0, 3000)}
请直接返回 JSON，不要包含 markdown 标记。`;

  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      contents: [{ parts: [{ text: prompt }] }]
    })
  });

  const data = await response.json();
  try {
    const text = data.candidates[0].content.parts[0].text;
    return JSON.parse(text.replace(/```json|```/g, "").strip());
  } catch (e) {
    return { category: "解析失败", summary: "AI 摘要生成出错或格式不正确", priority: 1 };
  }
}

async function pushToFeishu(from, subject, ai, env) {
  const isUrgent = ai.category === "验证码" || ai.priority >= 4;
  const color = isUrgent ? "red" : "blue";

  const payload = {
    msg_type: "interactive",
    card: {
      header: { template: color, title: { tag: "plain_text", content: `[CF] ${subject}` } },
      elements: [
        { tag: "div", text: { tag: "lark_md", content: `**摘要**: ${ai.summary}
**发件人**: ${from}` } },
        { tag: "note", elements: [{ tag: "plain_text", content: "🤖 由 Mail-Gateway-Hub (Worker) 驱动" }] }
      ]
    }
  };

  await fetch(env.FEISHU_WEBHOOK, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
}
