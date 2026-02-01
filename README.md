# echoRank — ETHChiangMai-Hackathon-2026
目标：建立社区 AI + 去中心化的社区收集与验证模式，用“人们的声音”与可验证反馈为活动与机构形成可信声誉与激励闭环。

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