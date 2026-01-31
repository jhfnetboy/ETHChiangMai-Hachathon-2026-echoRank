# 技术思考与架构拆分

## 目标与约束
- 前端使用 pnpm，React 单页，无登录
- 前后端与合约分别拆分：React、Node.js、Forge
- 语音输入限时 3 分钟，文件上传至后端
- 后端调用 Python AI 模型完成情感与关键词分析
- 合约采用 BLS + DVT 方向验证身份与参与记录，前端提供 Email 注册与绑定

## Monorepo
- pnpm workspace，目录：apps/web、apps/server、services/ai、contracts
- JS/TS 包用 pnpm 管理，Python 独立服务；链上部分用 Foundry

## 前端（apps/web）
- React + Vite，单页
- 功能：活动链接抓取摘要、语音录制与上传、结果展示、Email 注册
- 录音：MediaRecorder，强制 180s 停止；提交后展示总体评分与情感、关键词
- 代理：开发态代理到 Node 服务 /api

## 后端（apps/server）
- Express + Multer 接收音频
- /api/activity：抓取活动页内容并提取标题与摘要
- /api/analyze：转发音频到 Python AI，返回情感与关键词，并映射总体评分
- /api/register：接受邮箱，返回注册与绑定的占位结果（后续接入邮件服务与合约）

## AI 服务（services/ai）
- FastAPI 提供 /analyze，接受音频字节流
- 输出：sentiment、keywords；MVP 可先用启发式占位，后续替换为 ASR+NLP
- 部署：独立端口，Node 后端通过 HTTP 调用

## 合约（contracts）
- Foundry 初始化
- 身份与参与记录验证接口：verifyIdentity、hasParticipation
- BLS + DVT 方向：
  - 签名与多参与方验证的链下生成与链上验证分离
  - MVP 用占位合约，后续接入 BLS 验证库或可信证明
  - DVT 思路用于将身份与参与的签名证明在多方下达成阈值共识

## 安全与隐私
- 语音原始文件不公开；链上仅存摘要哈希与评分引用
- 明确授权与加密存储；遵循地区合规要求

## 路线与联动
- D1：端到端跑通录音上传与展示
- D2：接入真实 ASR/NLP；调整评分与风控
- D3：链上绑定与 BLS/DVT 验证集成
