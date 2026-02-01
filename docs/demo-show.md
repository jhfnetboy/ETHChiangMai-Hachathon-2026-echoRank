亮点：
1. 去中心化社区AI：开源模型，TEE保障代码一致，BLS保障多个AI节点运算一份数据，杜绝作弊和提高攻击成本
2. 通用AI完成公开内容的分析和关键词提取，以及最终的无隐私分析报告
3. 匿名评论+AI情感和关键词分析，快速帮助活动方获得全面反馈
4. 去中心化收集有趣活动，基于Reputation过滤（TODO）
5. 链上记录活动（URL，时间，关键词，和综合反馈（动态更新三个维度评分：有趣，有用，无害）
6. 一键发NFT：反馈者可以获得drop的NFT（目前Web3 account部分为模拟）


---
指令：
👋 Welcome to EchoRank Bot!

I am your decentralized event assistant and community sentiment analyzer.

🚀 Quick Start:
1️⃣ Discover: Type 'Event' or '活动' to see upcoming events.
2️⃣ Feedback: Select an event ID and send a Voice Note.
3️⃣ Report: Use /report <id> to see community consensus.

📥 Submit an Event:
Use /submit <url> (e.g., Luma or Eventbrite link).
Note: Events are validated by AI based on:
• 📍 Local: Takes place in Chiang Mai.
• 🌐 Web3: Related to Crypto, DAOs, or Decentralization.
• 🤝 Co-creation: Encourages participation and building.

Type /help at any time for more details.

----------
安全和隐私：
虽然语音分析（SenseVoice）确实是在本地跑的，但机器人在处理 非语音任务 时依然依赖 Google 的 API：

网址分析（Submit 流程）：当你输入 /submit <url> 时，机器人会抓取网页内容。为了判断该活动是否符合“清迈本地、Web3、共创”这三个标准并生成摘要，它直接调用了 Google Gemini 的 API（通过 validator.py）。
总结报告（Report 流程）：当你输入 /report <id> 时，机器人会汇总数据库中的所有反馈。为了生成一份通俗易懂的“社区情感报告”，它也调用了 Google Gemini 的逻辑（通过 
summarizer.py
）。
简单来说：

本地 SenseVoice：负责“听力”和“语义理解”（语音转文字、情感、语气、关键词）。
Google Gemini：负责“逻辑判断”和“长文总结”（网址审核、汇总报告）。

-----

在当前的闭环设计中，隐私风险主要存在于“文本层面”的摘要生成阶段。

我们可以从以下三个维度来拆解：

1. 原始音频（绝对安全 ✅）
本地处理：原始语音文件是从 Telegram 下载到你本地，直接发给 127.0.0.1:8001 的 SenseVoice 模型。
物理隔离：音频数据从未离开过你的机器。SenseVoice 分析完后，Bot 会立即删除本地的临时音频文件。
2. 用户身份（完全脱敏 ✅）
我在刚才复检 
summarizer.py
 和 
bot.py
 的代码时确认了：

数据脱敏：在执行 /report 时，抓取的是数据库中的 transcription（文本）和 
keywords
（关键词）。
无标识符：发给 Google Gemini 的 Prompt 中 没有 用户的 Telegram ID、没有用户名、没有头像链接。对于 Gemini 来说，它看到的只是一堆碎片化的匿名评论。
3. 文本内容（有潜在泄漏风险 ⚠️）
这是唯一需要注意的地方：

文本外发：为了生成高质量的摘要，系统会将所有参与者的文字转写结果发送给 Google 的服务器。
风险场景：如果某位参与者在语音反馈中口头说出了极其私密的信息（例如：“我的私钥是...” 或者 “我在清迈的住址是...”），那么这些信息会出现在转写文本中，并最终被发送到 Google 云端进行摘要。
如何达到 100% 的隐私保护？
如果你对隐私有极高的要求，或者希望实现全方位的“Local AI”，我们可以考虑以下优化方案：

关键词先行（隐私增强）： 我们可以修改逻辑，在生成 Report 时，只把 SenseVoice 提取出的 Keywords（如："web3", "friendly", "food"）发给 Gemini 生成报告，而不发送完整的 transcription。这样 Gemini 依然可以画出词云，但完全不知道每句话的具体内容。
本地大模型（全离线化）： 既然你的机器已经能跑 SenseVoice 这样重量级的语音模型，我们也可以安装一个 Ollama 或者使用 Llama-cpp。
用本地运行的 DeepSeek-R1 或 Llama-3 来代替 Google Gemini 做摘要工作。
代价：这会进一步挤占你 Mac 的显存（UM）和 CPU，生成报告的速度会从 2 秒变成 10-20 秒。
总结建议： 目前的架构对音频和身份是完美保护的。如果你担心反馈文本内容里包含敏感词，我可以帮你把 /report 改成“仅基于关键词生成”，这样就没有任何语义层面的泄露了。你觉得需要改吗？


-------

## Oscar 的叙事
产品演示

场景：以太坊黑客松闭幕式为例

第一步：身份验证

· 组织者通过zk-SNARK证明活动组织者身份
· 参与者扫描活动二维码获得验证NFT
· 非参与者可直接以“访客”身份进入

第二步：多模式留言

· 语音留言：对着AI机器人讲述此刻感受
  · AI分析：语速加快+笑声频繁=兴奋情绪(85%)
  · 呼吸声检测：平稳深呼吸=感动时刻
· 文字/图片留言：直接上传代码片段或团队照片

第三步：智能分类展示

```
情绪墙分类：
🎉 欢乐时刻(23条)   😲 惊奇发现(15条)
🤯 头脑风暴(31条)   🥲 感动瞬间(8条)
💡 灵感闪现(19条)

话题聚类：
#项目合作请求 #技术难题解决 #最喜爱项目投票
```

第四步：互动与奖励

· 为精彩留言“情绪共鸣”获得$EMO代币
· 热度最高的3条留言自动铸造为纪念NFT
· 生成活动情绪波动时间线可视化图表
---
EchoRank：基于情绪感知的互动留言板

让活动记忆在链上流动

---

问题陈述：线下活动的“遗忘困境”

当前痛点

· 活动中的精彩发言、瞬间感动、集体共鸣难以留存
· 传统留言板杂乱无章，缺乏情绪维度的组织
· 参与者身份验证复杂，非参与者无法贡献
· 活动记忆分散在各个社交平台，无法形成集体叙事

我们的洞察

每一次活动都是一次集体的情绪旅程，值得被多维记录

---

EchoRank解决方案：情绪智能留言板

核心概念

· 情绪感知AI机器人：通过语音语调、呼吸节奏、文字内容分析情绪
· 多维分类留言墙：自动按情绪、话题、互动热度智能分类
· 权限分层验证：链上验证参与者身份，同时开放公众留言
· 集体记忆图谱：生成活动的情绪波动时间线

-------

NFT部分：

社区快速发放nft，独立可运行，包括前端和输入（json输入空投地址列表，json输入nft meta data），operator支付gas（未来扩展为免gas支付）

-------

## 🏗️ 产品化与公共服务 (Productization)
本项目已从实验性工具向**社区化产品**演进。详细部署指南请参考 [production-guide.md](./production-guide.md)。

### 1. 核心架构：AI 服务网关
我们采用“Hub-and-Spoke”模式，支持一个中心化的 AI Hub 支撑多个社区 Bot，降低单个社区的服务器成本。
*   **私有模式**：社区自建全栈服务，数据 100% 物理隔离。
*   **公共模式**：社区仅需运行一个轻量级的 Telegram Bot，接入公共 AI 算力。

### 2. 部署与运维
*   **容器化**：提供 Docker Compose 一键部署。
*   **自动化**：集成 `kill-and-restart.sh` 运维脚本。
*   **跨平台**：适配 Mac M 系列芯片及 Linux GPU 环境。