# 产品需求文档 (PRD): EchoRank V2 - 去中心化活动共创平台

## 1. 产品核心理念
**"去中心化活动反馈与共创 (Decentralized Event Feedback & Co-creation)"**
我们将用户群体划分为两类，分别通过不同的工作流进行交互，旨在构建高质量、真实、且具有Web3共创精神的活动数据网络。

## 2. 用户画像与核心流程

### A. 提交者 (The Submitter)
*   **目标用户**: 活动主办方、黑客松Builder、高声誉KOL。
*   **核心诉求**: 将优质活动录入系统，建立索引。

**交互流程:**
1.  **提交 (Input)**: 用户通过 **Telegram Bot** 或 **Web页面** 发送活动链接。
    *   指令: `/submit <url>`
2.  **智能验证 (AI Validator)**: 系统抓取内容，由AI进行 **轻量化信息提取 (Lightweight Extraction)**:
    *   **核心字段**: 活动名称 (Title), 地点 (Location), 时间 (Time)。
    *   **简要概述**: 限制在 **20-30字** 以内的精炼描述。
    *   **原则**: 详细信息不存储，用户需点击原链接查看。
    *   **3选2 校验**: 检查是否符合 (1.清迈本地 2.Web3 3.共创/学术) 标准。
3.  **反馈结果 (Output)**:
    *   **通过**: 存入数据库，Bot回复 "✅ 活动 [名称] 已录入 (含简要)"。
    *   **失败**: Bot回复 "❌ 录入失败：仅符合1项标准 [原因]"。

### B. 参与者 (The Participant)
*   **目标用户**: 普通参会者、数字游民、游客。
*   **核心诉求**: 发现活动，并以最便捷的方式（语音）提供真实反馈。

**交互流程:**
1.  **发现 (Discovery)**:
    *   用户对Bot说关键词：**"活动"** 或 **"Event"**。
    *   Bot返回近期通过验证的活动列表 (Numbered List)。
        > 1. ETH Chiang Mai Opening (Today 10:00)
        > 2. Luma Developer Workshop (Today 14:00)
2.  **选择 (Selection)**: 用户回复数字 (如 "1")。
3.  **反馈 (Feedback)**:
    *   Bot提示: "请发送语音分享您的体验/建议。"
    *   用户录制并发送 **语音消息 (Voice Note)**。
4.  **分析 (AI Analysis)**:
    *   **语音转文字 (STT)**: 转换音频内容。
    *   **情感与关键词**: AI提取Top关键词 (Keywords) 并计算情感得分 (Sentiment Score)。
    *   数据关联至该活动ID。
5.  **报告 (Report)**:
    *   系统聚合所有反馈，生成 **词云 (Word Cloud)** 和 **情感摘要**，并最终在Web端展示。

## 3. 技术架构 (Technical Architecture)

### 核心服务 (Services)
1.  **Telegram Bot (`services/bot`)**: 双向交互入口。
2.  **Crawler Service (`services/crawler`)**:
    *   负责抓取提交的URL内容。
    *   管理 PostgreSQL 数据库连接。
3.  **AI Service (`services/ai`)**:
    *   **Validator Agent**: 执行3选2校验。
    *   **Feedback Agent**: 执行语音转写与情感分析。

### 数据存储 (Schema)
*   **活动表 (`activities`)**: 
    *   新增字段: `tags` (标签), `validation_status` (验证状态), `ai_summary` (AI摘要)。
*   **反馈表 (`feedbacks`) - [新增]**:
    *   字段: `user_id`, `activity_id`, `audio_url`, `transcription` (转写), `sentiment` (情感), `keywords` (关键词)。

## 4. 执行路线图 (Roadmap)

### 第一阶段: 提交与验证 (The Filter)
- [ ] 数据库变更: 升级 `activities` 表，创建 `feedbacks` 表。
- [ ] Bot指令: 实现 `/submit` 命令处理。
- [ ] AI验证器: 实现 "3选2" 提示词逻辑。

### 第二阶段: 发现与反馈 (The Loop)
- [ ] Bot逻辑: 监听 "活动" 关键词，查询数据库返回列表。
- [ ] 会话状态: 管理用户当前的 "选定活动"。
- [ ] 语音处理: 接收音频 -> 触发AI分析 -> 存储结果。

### 第三阶段: 聚合与展示 (The Cloud)
- [ ] 数据可视化: 生成词云。
- [ ] 自动报告: Bot端返回简报。
