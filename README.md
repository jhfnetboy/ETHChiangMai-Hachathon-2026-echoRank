# echoRank — ETHChiangMai-Hackathon-2026
目标：建立社区 AI + 去中心化的社区收集与验证模式，用“人们的声音”与可验证反馈为活动与机构形成可信声誉与激励闭环。
- https://youtu.be/Yb5aJ4jrNpc
- https://x.com/jhfnetboy/status/2017949836918845593


## 项目结构（pnpm workspace）
- apps/web：前端 React 单页（无登录）
  - 活动搜索/URL 抓取摘要
  - 语音录制（最长 3 分钟）与上传
  - 展示总体评分、情感与关键词
- apps/server：后端 Node.js（Express）
  - /api/activity 抓取活动页信息
  - /api/analyze 转发音频到 Python AI
  - /api/register 邮箱注册占位（后续接邮件与链上绑定）
- services/ai：Python FastAPI
  - /analyze 接收音频字节流，返回情感标签与关键词（MVP 占位逻辑）
- contracts：Foundry 合约
  - IdentityAttestor.sol（身份与参加记录验证占位）
  - 预留 BLS + DVT 路线（后续接入签名与阈值验证）

## 🚀 快速开始 (生产环境/一键部署)

我们推荐使用 Docker 进行一键部署，这会自动处理所有 Mac 上的环境依赖（如 `torch` 和 `llvmlite`）。

```bash
# 1. 克隆代码
git clone <project_url> && cd ETHChiangMai-Hachathon-2026

# 2. 运行一键式安装脚本
chmod +x setup-production.sh
./setup-production.sh
```
按照脚本提示输入你的 `BOT_TOKEN` 和 `GEMINI_API_KEY`，即可自动启动 **数据库、AI 引擎 和 机器人**。

详细部署说明请参考：[docs/production-guide.md](./docs/production-guide.md)

---

## 🛠️ 开发者指南 (本地开发模式)
如果你需要在此基础上进行代码修改或独立调试，可以使用 **Conda** 环境运行本地开发模式：

### 1. AI 服务 (Python FastAPI)
位于 `services/ai` 目录。
```bash
cd services/ai

# 1. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 2. 安装依赖
# 注意：Mac M-series 可能会遇到 torch 安装问题，建议先安装基础依赖
pip install -r requirements.txt

# 3. 生成 BLS 密钥对
# 这将生成 3 个验证者密钥并写入项目根目录的 .env 文件
python ../../scripts/generate_keys.py

# 4. 配置环境变量
# 将根目录 .env 同步到服务目录
cp ../../.env .env

# 5. 启动服务
python app.py
```

### 2. Telegram Bot 服务
位于 `services/bot` 目录。
```bash
cd services/bot

# 1. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
# 确保目录下的 .env 包含 BOT_TOKEN（咨询管理员或 @BotFather）

# 4. 启动 Bot
python bot.py
```

3) 使用流程
- 前端输入活动链接或关键词，抓取摘要
- 录音并提交（自动 3 分钟上限），后端转发至 AI
- 前端展示总体评分、情感标签与关键词
- 邮箱注册为占位功能，后续接入邮件服务与链上绑定

## 参考文档
- 项目演示 PPT (Bilingual)：[docs/demo-ppt.md](./docs/demo-ppt.md)
- 演示脚本/叙事：[docs/demo-show.md](./docs/demo-show.md)
- 生产环境指南：[docs/production-guide.md](./docs/production-guide.md)
- PRD：PRD-Hackathon.md
- 技术思考：TECH-THINK.md

## 文件接收与存储方式
- 后端在收到语音后立即计算 SHA256 摘要，并按日期分目录保存
  - 路径模式：apps/server/uploads/YYYY-MM-DD/<timestamp>_<audiohash8>.<ext>
  - 接口返回包含 audio_hash 与 stored_path，便于审计与复现
- 说明：这是原始字节的落盘副本；后续可扩展为按“活动名称”分桶目录，如 uploads/<date>/<activity>/...

## Telegram Bot 行为
- 群聊
  - 忽略语音，不分析不回复
  - 仅在被提及时（@communityEchoRankBot）或发送 help 且同时提及时，回复统一说明
  - 说明（中英双语）：
    - 👋 欢迎使用 echoRank bot
    - 使用方式：请按住对话框右侧的麦克风说话；后台 AI 返回分析结果并自动上链；务必提及你反馈的活动名称，否则反馈无效。
    - EN: Welcome to echoRank bot. Press the microphone button to speak. AI will analyze and record on-chain. Please mention the event name, otherwise feedback is invalid.
- 私聊
  - 文本：仅发送上述说明（不回显消息内容）
  - 语音：转发到后端 /api/analyze，返回 score/sentiment/keywords；同时返回 audio_hash 与存储路径

## 会话聚合与目录策略
- 会话标识：session_id = <user_id>-<bucket>，其中 bucket 为 10 分钟时间窗（同一用户 10 分钟内多次语音归为同一会话）
- 存储目录：apps/server/uploads/YYYY-MM-DD/<session_id>/<timestamp>_<audiohash8>.<ext>
- 接口返回：audio_hash、stored_path、session_id、user_id、activity_name
- 聚合接口：GET /api/analyze_session?session_id=...，返回聚合评分（均值）、聚合情感（多数投票）、聚合关键词（并集）及每条明细
- 说明：可切换为按活动名称分桶（uploads/<date>/<activity>/...）；若启用则需强校验 activity_name

## 后端角色说明
- 后端（apps/server，Node.js）：接收文件、计算并存储摘要、调用 AI 服务、提供聚合与存证接口，并统一对外提供 /api
- AI 后端（services/ai，Python）：提供 /analyze，将音频字节流转为结构化分析结果（sentiment、keywords 等）

## 配置
- apps/server/.env
  - SENDGRID_API_KEY、SENDGRID_FROM、APP_BASE_URL
  - AI_URL：AI 服务地址（完整 HTTP Endpoint），默认为 http://127.0.0.1:8001/analyze，可配置为外部地址
- services/bot/.env
  - BOT_TOKEN、BACKEND_URL、BOT_NAME、Tele_URL

当前系统使用的是 PostgreSQL 关系型数据库，而不是简单的本地文件（如 JSON 或 SQLite）。

根据代码中的 
services/bot/bot.py
 的 
get_db_connection
 函数显示，系统通过 psycopg2 连接到数据库。

数据库配置详情：
数据库名: echorank_crawler
用户名: jason (之前根据你的系统环境从 postgres 修改为了 jason)
连接方式: 通过 TCP/IP 连接到 localhost:5432
为什么选择 PostgreSQL 而非文件？
并发处理: 支持机器人多用户同时提交、同时查询报告。
数据关联: 方便将反馈表 (feedbacks) 与活动表 (activities) 通过 activity_id 进行关联查询，这对于场景 3 的 "聚合报告" 特别重要。
持久化: 相比 JSON 文件更安全稳定，不会因为并发写入导致损坏。
如果你想查看数据库里的数据，可以运行以下命令：
bash
- 查看已通过验证的活动
psql -h localhost -d echorank_crawler -c "SELECT id, title, validation_status FROM activities;"
- 查看提交的反馈
psql -h localhost -d echorank_crawler -c "SELECT * FROM feedbacks;"

## More
1. 声纹提取是否稳定和一致？
结论：技术上可以做到“基本稳定”，但不能直接像指纹那样拿来做 SHA256 哈希。

稳定性（Stability）：在 AI 领域，这叫 Speaker Embedding（声纹嵌入）。目前的深度学习模型（如 ECAPA-TDNN）可以将一段语音转化为一串 256 位或 512 位的固定数字（向量）。对于同一个人，无论他说什么，这串数字在“数学空间”里的位置是非常接近的。
一致性挑战：与密码不同，生物特征是“模糊”的。你感冒了、换了个麦克风、或者背景特别吵，生成的这串数字都会有微小的偏移。
如何解决识别？：我们不能对比两个哈希值是否完全相同，而是对比两个向量之间的**“余弦距离（Cosine Similarity）”**。如果相似度 > 85%，AI 就会判定：“这就是刚才那个用户”。
2. 为 NFT 提供 hash(声纹 + 活动名称) 的想法
你的方案非常有前瞻性，但也面临一个“哈希悖论”：

因为声纹嵌入（Embedding）每次都有微小抖动，如果你直接对原始 Embedding 做哈希，结果永远是不一样的。
改进方案：我们需要一个“量化（Quantization）”步骤。先将声纹向量转化为某种“固定的特征网格”，然后再做哈希。或者，在我们的本地 AI Node 里维护一个映射表：声纹向量 -> 虚拟用户 ID，然后将 sha256(虚拟用户ID + 活动名称) 存入 NFT。

我已经为你要求的“身份识别”功能增加了专门的测试板块。现在机器人不仅能听懂你在说什么，还能“听出你是谁”。

🛠️ 新增功能：/test_voice
你可以按照以下步骤测试 AI 的声纹稳定性：

开启测试：在 Telegram 中输入 /test_voice。
录入指纹：发送第一段语音（比如：“我是 Jason，这是我的第一段录音”）。AI 会提取你的声纹嵌入 (Speaker Embedding)。
身份核验：发送第二段语音（可以换一段话，比如：“今天天气不错，AI 你认得出我吗？”）。
结果反馈：AI 会计算两段语音的余弦相似度 (Cosine Similarity)，并告诉你是否匹配。
🧠 技术亮点：
CAM++ 模型：我们使用了高性能的声纹特征提取模型，它关注的是你声道的物理特征，而不是文字内容。
ID 绑定辅助：在匹配成功后，AI 会显式显示你的 Telegram ID，证明它成功将这段声音与你的数字身份关联。
隐私安全：所有的声纹比对都在你的本地 AI Hub 进行，原始声纹向量不会发往云端。
🚀 架构更新：
AI 服务：新增了 /voiceprint（提取）和 /compare_voiceprints（比对）端点。
服务自愈：修复了启动脚本中的路径和环境问题，现在所有 AI 模型（SenseVoice + CAM++）已进入“满血”工作状态。

------

你可以现在去 Telegram 试试看！ 即使你故意捏着嗓子或者换个语言，看看 AI 能不能依然锁定你的身份。这就是你提到的“让记忆在链上流动”时，最具冲击力的底层证明技术。🔥✨如有任何进一步的想法（比如将这个哈希上链的具体格式），请随时告诉我
