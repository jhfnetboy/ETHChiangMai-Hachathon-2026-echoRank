# EchoRank 生产环境与公共服务指南 (Bilingual)

[跳转到英文版本 (Jump to English) ↓](#english-version)

<a name="chinese-version"></a>

## 1. 架构模型 (Hub-and-Spoke)
为了降低社区参与门槛，我们设计了灵活的部署模式：

### A. 公共服务模式 (极简使用)
*   **适用对象**：小型社区、Hachathon 参与者。
*   **原理**：仅需部署轻量级 **Telegram Bot**，语音分析请求发往 **公共 AI Hub**。
*   **部署要求**：任何 Python 环境 (如 1核2G 云主机)。

### B. 主权部署模式 (完全独立)
*   **适用对象**：对隐私有极高要求、或希望拥有算力主权的组织。
*   **原理**：本地同时运行 AI Hub、Bot 与 数据库。
*   **部署要求**：建议 Mac M 系列 (16G+ 内存) 或 带 GPU 的 Linux 服务器。

---

## 2. 一键产品化部署 (Docker)
我们提供了 `setup-production.sh` 脚本，可一键完成环境配置。

### 步骤 1：准备环境
确保安装了 [Docker Desktop](https://www.docker.com/products/docker-desktop/)。

### 步骤 2：启动脚本
```bash
chmod +x setup-production.sh
./setup-production.sh
```

### 步骤 3：配置
脚本会引导你输入 `BOT_TOKEN` 和 `GEMINI_API_KEY`。完成后将自动启动：
1.  **echorank-db**: 持久化反馈数据库。
2.  **echorank-ai**: **本地隐私计算节点** (SenseVoice)。
3.  **echorank-bot**: 业务逻辑与 Telegram 交互节点。

---

## 3. 运维注意事项
*   **模型预载**：首次启动约下载 1.2GB 模型，请确保网络通畅。
*   **扩展性**：支持通过 Load Balancer 增加 AI 实例，应对大型活动。
*   **API 代理**：Gemini API 在部分地区可能需要配置全局代理或中转反佣。

---

<a name="english-version"></a>

# [English Version]
[返回中文版本 ↑](#chinese-version)

## 1. Architecture Model (Hub-and-Spoke)
EchoRank offers flexible deployment modes to lower the entry barrier:

### A. Public Service Mode (Minimalist)
*   **Target**: Small communities, hackathon participants.
*   **Logic**: Host only the lightweight **Telegram Bot**; requests are sent to a **Public AI Hub**.
*   **Reqs**: Any basic Python environment (e.g., 1-core 2G Cloud VM).

### B. Sovereign Mode (Independent)
*   **Target**: Privacy-centric organizations or those seeking computing sovereignty.
*   **Logic**: Run AI Hub, Bot, and Database locally.
*   **Reqs**: Apple Silicon Mac (16G+ RAM) or Linux server with GPU.

---

## 2. One-Click Production Setup (Docker)
The `setup-production.sh` script automates the environment configuration.

### Step 1: Prep
Ensure [Docker Desktop](https://www.docker.com/products/docker-desktop/) is installed.

### Step 2: Execute
```bash
chmod +x setup-production.sh
./setup-production.sh
```

### Step 3: Configure
The script will prompt for `BOT_TOKEN` and `GEMINI_API_KEY`. It then starts:
1.  **echorank-db**: Persistent feedback database.
2.  **echorank-ai**: **Local Privacy Computing Node** (SenseVoice).
3.  **echorank-bot**: Business logic and Telegram interaction.

---

## 3. Operational Notes
*   **Model Caching**: Downloads approx. 1.2GB model on the first run.
*   **Scalability**: Add AI instances via Load Balancer for mass-scale events.
*   **API Proxy**: Gemini API might require proxies in certain regions.
