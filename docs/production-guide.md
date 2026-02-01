# EchoRank 生产环境与公共服务指南

为了让社区能更简单地使用 EchoRank，我们将项目设计为 **“云端中心 AI + 轻量化社区 Bot”** 的混合架构。

## 1. 架构模型 (Hub-and-Spoke)
本项目的核心是 SenseVoice 语音分析。为了降低社区参与门槛，我们推荐以下两种模式：

### A. 公共服务模式 (极简使用)
*   **适用对象**：小型社区、Hachathon 参与者。
*   **原理**：你只需要部署一个轻量级的 **Telegram Bot**，语音分析请求直接发送到我们提供的 **公共 AI Hub 地址**。
*   **部署要求**：任何能跑 Python 的环境 (如 1核2G 的云主机)。

### B. 主权部署模式 (完全独立)
*   **适用对象**：对隐私有极高要求、或希望拥有算力主权的组织。
*   **原理**：本地同时运行 AI Hub 和 Bot。
*   **部署要求**：建议配有 GPU 或高性能 CPU 的服务器 (如 Mac Studio / NVIDIA 云主机)。

---

## 2. 一键产品化部署 (Docker)

我们提供了 `setup-production.sh` 脚本，可以自动完成环境配置并启动所有服务。

### 步骤 1：准备环境
确保你的 Mac 已安装 [Docker Desktop](https://www.docker.com/products/docker-desktop/)。

### 步骤 2：执行安装脚本
```bash
chmod +x setup-production.sh
./setup-production.sh
```

### 步骤 3：按照提示输入 API Key
脚本会提示你输入 `BOT_TOKEN` 和 `GEMINI_API_KEY`。完成后，它将自动启动以下容器：
1.  **echorank-db**: 本地 PostgreSQL 数据库，持久化存储所有反馈。
2.  **echorank-ai**: **本地隐私计算节点**，加载 SenseVoice 模型进行语音识别。
3.  **echorank-bot**: 业务逻辑节点，处理 Telegram 指令并调用 AI 接口。

---

## 3. 运维注意事项
*   **模型预加载**：AI 服务首次启动时会下载模型 (约 1.2GB)，请预留足够的带宽和存储空间。
*   **并发处理**：公开服务模式下，建议在 Bot 端配置速率限制 (Rate Limiting)，防止算力被滥用。
*   **扩展性**：可以通过增加 AI Service 的实例并使用 Load Balancer，轻松应对上千人的大型活动反馈。

---

## 4. 社区开发者参与
*   **插件开发**：你可以为 Bot 增加更多的“情绪指令”，通过简单的 Python 修改即可实现。
*   **前端墙**：我们提供标准 JSON API，你可以基于此开发自己的活动实时情绪墙 (Event Dashboard)。
