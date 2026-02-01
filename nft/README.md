# echoRank Community NFT Developer Guide 🚀 | 开发者指南

本指南旨在帮助开发者快速上手 echoRank 的社区 NFT 体系，实现从“注册社区”到“通过 AI Agent 铸造 SBT”的完整闭环。
This guide helps developers quickly get started with the echoRank Community NFT system, covering the full cycle from "Community Registration" to "SBT Minting via AI Agent."

## 1. 核心合约地址 (Sepolia) | Core Contract Addresses

这些地址已经过审计并部署在 Sepolia 测试网。
These addresses are audited and deployed on the Sepolia Testnet.

| 合约名称 | Contract Name | 合约地址 | Address | 说明 | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Registry** | Registry | `0x7Ba70C5bFDb3A4d0cBd220534f3BE177fefc1788` | 0x7Ba70... | 核心注册表 | Core Registry |
| **NFT Factory** | NFT Factory | `0x1D23352390FfA1634D5eE80ebD2c5C217250d8B9` | 0x1D233... | 一键 Clone 工厂 | One-click Clone Factory |
| **Logic Impl** | Logic Impl | `0xD18c88a9102cb61eE2361240854b83e4E6D91539` | 0xD18c8... | 核心逻辑实现 | Core Logic Implementation |

---

## 2. 准备工作 (Onboarding) | 准入流程

在部署社区 NFT 之前，你必须在 `Registry` 中拥有 `ROLE_COMMUNITY` 角色。
Before deploying your NFT, you must have the `ROLE_COMMUNITY` role in the `Registry`.

### Step A: 获取入场券 (Faucet & Gov Tokens)
echoRank 使用质押治理模式。你首先需要通过 AAstar SDK 的 **Faucet** 获取测试网治理代币。
echoRank uses a staking governance model. Obtain testnet governance tokens via the AAstar SDK **Faucet**.
1.  参考 (Ref): `aastar-sdk/scripts/test-faucet-and-gasless.ts`.
2.  使用 `SepoliaFaucetAPI.prepareTestAccount`.
3.  这会充值测试 ETH 和用于质押的 Governance Tokens。
    This funds your account with test ETH and staking tokens.

### Step B: 注册社区 | Register Community
调用 `Registry.registerCommunity()`。成功后，你的地址将在链上被标记为受信任社区。
Call `Registry.registerCommunity()`. Once successful, your address is marked as a trusted community on-chain.

---

## 3. 快速发行 (Quick Launch) | 发行你的 NFT

使用位于 `contracts/script/` 的原子化脚本：
Use the atomic scripts located in `contracts/script/`:

### 第一步：部署社区合约 | Step 1: Deploy
运行 (Run) `Step1_Anni_Deploy.s.sol`.
- **业务动作 (Action)**: 通过 Factory 克隆出一个全新的 NFT 合约。
  Clone a brand new NFT contract via the Factory.
- **模式建议 (Modes)**: 选择 `HYBRID` 模式支持常规 NFT 与 SBT。
  Choose `HYBRID` mode for both standard NFTs and SBTs.

### 第二步：配置 AI Agent | Step 2: Auth Agent
运行 (Run) `Step2_Anni_AuthAgent.s.sol`.
- **业务动作 (Action)**: 将你的 AI Agent 授权为 `MINTER_ROLE`。
  Authorize your AI Agent as the `MINTER_ROLE`.
- **意义 (Significance)**: Agent 即可自动化为用户铸造 NFT。
  Enables the Agent to mint NFTs for users autonomously.

### 第三步：灵活铸造 | Step 3: Flexible Minting
使用 `Step3` (Transferable) 和 `Step4` (SBT) 脚本进行测试。
Test with `Step3` (Transferable) and `Step4` (SBT) scripts.
- **SBT (Soulbound)**: 铸造时将 `isSoulbound` 设为 `true`，永久禁止转让。
  Set `isSoulbound` to `true` to permanently disable transfers.

---

## 4. FAQ | 常见问题

**Q: 为什么我无法调用 Factory 部署合约？(Why can't I call the Factory?)**
A: 请确保你的地址已在 `Registry` 中注册。
Ensure your address is registered in the `Registry`.

**Q: 我可以直接修改 NFT 的逻辑吗？(Can I modify the NFT logic?)**
A: 如果你有特殊需求，可以修改 `src/CommunityNFT.sol` 并重新部署。
If you have custom needs, modify `src/CommunityNFT.sol` and redeploy.
