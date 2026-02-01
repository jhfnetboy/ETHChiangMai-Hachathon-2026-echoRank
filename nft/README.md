# echoRank Community NFT Developer Guide 🚀

本指南旨在帮助开发者快速上手 echoRank 的社区 NFT 体系，实现从“注册社区”到“通过 AI Agent 铸造 SBT”的完整闭环。

## 1. 核心合约地址 (Sepolia)

这些地址已经过审计并部署在 Sepolia 测试网。对于大多数开发者，这些是固定不变的：

| 合约名称 | 合约地址 | 说明 |
| :--- | :--- | :--- |
| **Registry** | `0x7Ba70C5bFDb3A4d0cBd220534f3BE177fefc1788` | 核心注册表，管理所有实体角色 |
| **NFT Factory** | `0x1D23352390FfA1634D5eE80ebD2c5C217250d8B9` | 用于一键 Clone 部署社区自己的 NFT 合约 |
| **Logic Impl** | `0xD18c88a9102cb61eE2361240854b83e4E6D91539` | NFT 的核心逻辑实现合约 |

---

## 2. 准备工作 (Onboarding)

在你部署自己的社区 NFT 之前，你（社区主人）必须在 `Registry` 中拥有 `ROLE_COMMUNITY` 角色。

### Step A: 获取入场券 (Testing Governance Tokens)
echoRank 使用质押治理模式。你首先需要通过 AAstar SDK 的 **Faucet** 获取测试网治理代币。
1.  参考 `aastar-sdk/scripts/test-faucet-and-gasless.ts`。
2.  使用 `SepoliaFaucetAPI.prepareTestAccount` 方法。
3.  这会为你的 EOA 账户充值测试 ETH 和用于质押的 Governance Tokens。

### Step B: 注册社区
在拥有代币后，调用 `Registry.registerCommunity()`（或通过项目提供的 onboard 脚本）。成功后，你的地址将在链上被标记为受信任社区。

---

## 3. 快速发行你的社区 NFT

一旦你拥有了角色，你可以直接使用我们提供的原子化脚本进行发行（位于 `contracts/script/`）：

### 第一步：部署社区合约
运行 `Step1_Anni_Deploy.s.sol`（请在 `.env` 中修改为你自己的私钥）。
- **业务动作**: 通过 Factory 克隆出一个全新的 NFT 合约。
- **模式建议**: 选择 `HYBRID` 模式，以支持通用的可转让 NFT 和不可转让的 SBT。

### 第二步：配置 AI Agent
运行 `Step2_Anni_AuthAgent.s.sol`。
- **业务动作**: 将你的 AI Agent 地址（如一个负责分析语音并自动发奖的机器人）授权为 `MINTER_ROLE`。
- **意义**: 这样你的后端 Agent 就可以在无需你亲自干预的情况下，根据活动反馈自动为用户铸造 NFT。

### 第三步：灵活铸造
使用 `Step3` 和 `Step4` 脚本进行测试：
- **可转让 NFT**: 用于奖励、门票。
- **SBT (Soulbound)**: 用于声誉、活动参与证明。在铸造时将 `isSoulbound` 参数设为 `true`，合约将永久禁止该 Token 的转让。

---

## 4. 常见问题 (FAQ)

**Q: 为什么我无法调用 Factory 部署合约？**
A: 请确保你的地址已在 `Registry` 中注册。Factory 会实时校验 `IRegistry(registry).hasRole(ROLE_COMMUNITY, msg.sender)`。

**Q: 我可以直接修改 NFT 的逻辑吗？**
A: 如果你有特殊需求，可以修改 `src/CommunityNFT.sol` 并重新部署实现合约。但对于常规的 SBT 和混合模式需求，现有的逻辑已足够完备。
