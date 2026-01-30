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

## 快速开始
1) 安装依赖

```bash
pnpm install
pip install -r services/ai/requirements.txt
```

2) 启动服务

```bash
# 启动 AI 服务（默认 8001）
python3 services/ai/app.py

# 启动后端（默认 8000）
pnpm dev:server

# 启动前端（默认 5173）
pnpm dev:web
```

3) 使用流程
- 前端输入活动链接或关键词，抓取摘要
- 录音并提交（自动 3 分钟上限），后端转发至 AI
- 前端展示总体评分、情感标签与关键词
- 邮箱注册为占位功能，后续接入邮件服务与链上绑定

## 参考文档
- PRD：PRD-Hackathon.md
- 技术思考：TECH-THINK.md
