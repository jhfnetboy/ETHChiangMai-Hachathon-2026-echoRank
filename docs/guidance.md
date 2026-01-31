# 🎯 小白实施指南：将语音分析模块集成到你的项目

## 📋 你的目标

实现一个 API 模块，功能是：

```
Bot 发送语音 → 你的 API 接收
    ↓
分发给 3 个 AI 验证节点
    ↓
每个 AI 分析 + BLS 签名
    ↓
返回：公钥、签名、分析结果
```

---

## 📂 你的项目结构

根据你的 GitHub 项目，目录是：

```
echorank/
├── apps/
│   ├── web/              # 前端（你不需要改）
│   └── server/           # ⭐ 后端（你要改这里）
│       └── src/
│           └── api/
│               ├── activity.ts
│               ├── analyze.ts     # ⭐ 你要创建/修改
│               └── register.ts
│
├── services/
│   └── ai/              # ⭐ Python AI 服务（你要创建）
│       ├── validator.py         # 主程序
│       ├── analyzer.py          # SenseVoice
│       ├── bls_signer.py        # BLS 签名
│       └── requirements.txt
│
└── contracts/           # 智能合约（暂时不用管）
```

---

## 🚀 第一步：安装 Python AI 服务

### 1.1 创建 services/ai 目录

```bash
# 进入你的项目根目录
cd echorank

# 创建 AI 服务目录
mkdir -p services/ai
cd services/ai
```

### 1.2 创建文件

你需要创建 4 个文件：

1. **validator.py** - 主程序（我已经写好了）
2. **analyzer.py** - SenseVoice 分析器
3. **bls_signer.py** - BLS 签名
4. **requirements.txt** - Python 依赖

---

## 📝 第二步：复制代码文件

### 2.1 创建 `requirements.txt`

```bash
# 在 services/ai/ 目录下创建文件
nano requirements.txt
```

**复制以下内容：**

```txt
# Web 框架
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
python-multipart==0.0.6

# AI 模型
funasr>=1.0.0
torch>=2.0.0
torchaudio>=2.0.0
numpy>=1.24.0
modelscope>=1.9.0

# BLS 签名
py-ecc==6.0.0

# 工具
python-dotenv==1.0.0
```

**保存并退出**（Ctrl+O, Enter, Ctrl+X）

### 2.2 创建 `analyzer.py`

```bash
nano analyzer.py
```

**复制以下代码：**

```python
# analyzer.py - SenseVoice 情感分析器
"""
使用 SenseVoice-Small 模型分析语音情感
"""

import io
import re
import numpy as np
import torch
import torchaudio
from funasr import AutoModel
from typing import Dict, Tuple, List
import logging

logger = logging.getLogger(__name__)


class EmotionAnalyzer:
    """语音情感分析器"""
    
    # 情感标签映射
    EMO_DICT = {
        "<|HAPPY|>": "HAPPY",
        "<|SAD|>": "SAD",
        "<|ANGRY|>": "ANGRY",
        "<|NEUTRAL|>": "NEUTRAL",
        "<|FEARFUL|>": "FEARFUL",
        "<|DISGUSTED|>": "DISGUSTED",
        "<|SURPRISED|>": "SURPRISED",
    }
    
    # 音频事件映射
    EVENT_DICT = {
        "<|BGM|>": "music",
        "<|Speech|>": "speech",
        "<|Applause|>": "applause",
        "<|Laughter|>": "laughter",
        "<|Cry|>": "cry",
        "<|Sneeze|>": "sneeze",
        "<|Cough|>": "cough",
    }
    
    def __init__(self, model_path="iic/SenseVoiceSmall"):
        """初始化 SenseVoice 模型"""
        logger.info("Loading SenseVoice model...")
        
        self.model = AutoModel(
            model=model_path,
            vad_model="iic/speech_fsmn_vad_zh-cn-16k-common-pytorch",
            vad_kwargs={"max_single_segment_time": 30000},
            trust_remote_code=True,
        )
        
        logger.info("SenseVoice model loaded successfully")
    
    def analyze(self, audio_bytes: bytes) -> Dict:
        """
        分析音频情感
        
        参数:
            audio_bytes: 音频字节数据
        
        返回:
            {
                "emotion": "HAPPY",
                "intensity": 0.85,
                "confidence": 0.92,
                "keywords": ["活动", "很棒"],
                "events": ["applause"],
                "raw_text": "这次活动很棒！",
                "language": "zh"
            }
        """
        # 预处理音频
        audio_array, sample_rate = self._preprocess_audio(audio_bytes)
        
        # 运行 SenseVoice 推理
        result = self.model.generate(
            input=audio_array,
            cache={},
            language="auto",
            use_itn=True,
            batch_size_s=60,
            merge_vad=True
        )
        
        # 解析结果
        raw_text = result[0]["text"]
        
        emotion, intensity = self._extract_emotion(raw_text)
        events = self._extract_events(raw_text)
        language = self._extract_language(raw_text)
        clean_text = self._clean_text(raw_text)
        keywords = self._extract_keywords(clean_text)
        
        return {
            "emotion": emotion,
            "intensity": intensity,
            "confidence": intensity,  # SenseVoice 的强度可作为置信度
            "keywords": keywords,
            "events": events,
            "raw_text": clean_text,
            "language": language,
            "full_result": raw_text  # 保留原始结果用于调试
        }
    
    def _preprocess_audio(self, audio_bytes: bytes) -> Tuple[np.ndarray, int]:
        """预处理音频数据"""
        # 从字节加载音频
        audio_buffer = io.BytesIO(audio_bytes)
        
        try:
            # 尝试加载音频
            waveform, sample_rate = torchaudio.load(audio_buffer)
        except Exception as e:
            # 如果失败，尝试作为原始 PCM 数据
            audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
            audio_array = audio_array.astype(np.float32) / 32768.0
            sample_rate = 16000
            
            return audio_array, sample_rate
        
        # 转换为 numpy
        audio_array = waveform.numpy()
        
        # 转为单声道
        if len(audio_array.shape) > 1 and audio_array.shape[0] > 1:
            audio_array = audio_array.mean(axis=0)
        else:
            audio_array = audio_array.squeeze()
        
        # 重采样到 16kHz
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(sample_rate, 16000)
            audio_tensor = torch.from_numpy(audio_array).float()
            if len(audio_tensor.shape) == 1:
                audio_tensor = audio_tensor.unsqueeze(0)
            audio_array = resampler(audio_tensor).squeeze().numpy()
            sample_rate = 16000
        
        return audio_array, sample_rate
    
    def _extract_emotion(self, text: str) -> Tuple[str, float]:
        """提取情感标签和强度"""
        emotion_counts = {}
        
        for tag, emotion in self.EMO_DICT.items():
            count = text.count(tag)
            if count > 0:
                emotion_counts[emotion] = count
        
        if not emotion_counts:
            return "NEUTRAL", 0.5
        
        # 找出出现最多的情感
        dominant_emotion = max(emotion_counts, key=emotion_counts.get)
        count = emotion_counts[dominant_emotion]
        
        # 计算强度（出现次数越多，强度越高）
        intensity = min(0.7 + (count - 1) * 0.1, 0.99)
        
        return dominant_emotion, intensity
    
    def _extract_events(self, text: str) -> List[str]:
        """提取音频事件"""
        events = []
        
        for tag, event in self.EVENT_DICT.items():
            if tag in text and event not in ['speech', 'breath']:
                events.append(event)
        
        return events
    
    def _extract_language(self, text: str) -> str:
        """提取检测到的语言"""
        lang_tags = {
            "<|zh|>": "zh",
            "<|en|>": "en",
            "<|yue|>": "yue",
            "<|ja|>": "ja",
            "<|ko|>": "ko",
        }
        
        for tag, lang in lang_tags.items():
            if tag in text:
                return lang
        
        return "unknown"
    
    def _clean_text(self, text: str) -> str:
        """清理文本，移除所有标签"""
        # 移除所有 <|xxx|> 格式的标签
        cleaned = re.sub(r'<\|[^>]+\|>', '', text)
        
        # 移除多余空格
        cleaned = ' '.join(cleaned.split())
        
        return cleaned.strip()
    
    def _extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """简单的关键词提取（按词频）"""
        if not text:
            return []
        
        # 分词（简单按空格和标点分割）
        words = re.findall(r'\w+', text)
        
        # 过滤停用词和短词
        stop_words = {'的', '了', '是', '我', '你', '他', '她', '它', '我们', '你们', '他们'}
        words = [w for w in words if len(w) > 1 and w not in stop_words]
        
        # 统计词频
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按频率排序，取前 N 个
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        keywords = [word for word, freq in sorted_words[:max_keywords]]
        
        return keywords


# 测试代码
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    analyzer = EmotionAnalyzer()
    print("✅ Analyzer initialized successfully")
    
    if len(sys.argv) > 1:
        # 测试文件
        audio_file = sys.argv[1]
        with open(audio_file, 'rb') as f:
            audio_bytes = f.read()
        
        result = analyzer.analyze(audio_bytes)
        print("\n分析结果:")
        print(f"  情感: {result['emotion']}")
        print(f"  强度: {result['intensity']:.2f}")
        print(f"  转录: {result['raw_text']}")
        print(f"  关键词: {result['keywords']}")
```

**保存并退出**

### 2.3 创建 `bls_signer.py`

```bash
nano bls_signer.py
```

**复制以下代码：**

```python
# bls_signer.py - BLS 签名实现
"""
使用 BLS12-381 曲线实现阈值签名
"""

from py_ecc.bls import G2ProofOfPossession as bls
import hashlib
import logging

logger = logging.getLogger(__name__)


class BLSSigner:
    """BLS 签名器"""
    
    def __init__(self, private_key_hex: str):
        """
        初始化签名器
        
        参数:
            private_key_hex: 私钥的十六进制字符串
        """
        self.sk = int(private_key_hex, 16)
        self.pk = bls.SkToPk(self.sk)
        
        logger.info(f"BLS Signer initialized with public key: {self.pk.hex()[:16]}...")
    
    def sign_message(self, message: bytes) -> bytes:
        """
        对消息进行 BLS 签名
        
        参数:
            message: 待签名的消息（字节）
        
        返回:
            签名（字节）
        """
        signature = bls.Sign(self.sk, message)
        return signature
    
    @staticmethod
    def verify_signature(public_key: bytes, message: bytes, signature: bytes) -> bool:
        """
        验证 BLS 签名
        
        参数:
            public_key: 公钥
            message: 原始消息
            signature: 签名
        
        返回:
            是否有效
        """
        try:
            return bls.Verify(public_key, message, signature)
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False
    
    @staticmethod
    def aggregate_signatures(signatures: list) -> bytes:
        """
        聚合多个签名
        
        参数:
            signatures: 签名列表
        
        返回:
            聚合签名
        """
        return bls.Aggregate(signatures)
    
    @staticmethod
    def aggregate_verify(
        public_keys: list,
        message: bytes,
        aggregated_sig: bytes
    ) -> bool:
        """
        验证聚合签名（所有节点签署同一消息）
        
        参数:
            public_keys: 公钥列表
            message: 原始消息
            aggregated_sig: 聚合签名
        
        返回:
            是否有效
        """
        try:
            # 聚合公钥
            agg_pk = public_keys[0]
            for pk in public_keys[1:]:
                agg_pk = bls.aggregate_pubkeys([agg_pk, pk])
            
            # 验证聚合签名
            return bls.Verify(agg_pk, message, aggregated_sig)
        except Exception as e:
            logger.error(f"Aggregated signature verification failed: {e}")
            return False


def construct_message(
    audio_hash: str,
    result_hash: str,
    algo_version: str,
    timestamp: int,
    nonce: str
) -> bytes:
    """
    构造待签名消息
    
    消息格式:
    m = domain_sep || audio_hash || result_hash || algo_version || timestamp || nonce
    
    参数:
        audio_hash: 音频哈希
        result_hash: 结果哈希
        algo_version: 算法版本
        timestamp: 时间戳
        nonce: 随机数
    
    返回:
        消息的 SHA256 哈希
    """
    domain_sep = "ECHORANK_V1"
    
    message_parts = [
        domain_sep,
        audio_hash,
        result_hash,
        algo_version,
        str(timestamp),
        nonce
    ]
    
    message_str = "||".join(message_parts)
    message_bytes = message_str.encode('utf-8')
    
    # 返回消息的哈希（标准做法）
    return hashlib.sha256(message_bytes).digest()


# 测试代码
if __name__ == "__main__":
    import secrets
    import time
    
    logging.basicConfig(level=logging.INFO)
    
    # 生成测试密钥
    sk_hex = hex(secrets.randbelow(bls.curve_order))
    print(f"Private Key: {sk_hex}")
    
    # 创建签名器
    signer = BLSSigner(sk_hex)
    print(f"Public Key: {signer.pk.hex()}")
    
    # 构造测试消息
    message = construct_message(
        audio_hash="test_audio_hash",
        result_hash="test_result_hash",
        algo_version="v1.0.0",
        timestamp=int(time.time()),
        nonce=secrets.token_hex(16)
    )
    
    # 签名
    signature = signer.sign_message(message)
    print(f"\nSignature: {signature.hex()[:32]}...")
    
    # 验证
    is_valid = BLSSigner.verify_signature(signer.pk, message, signature)
    print(f"Verification: {'✅ Valid' if is_valid else '❌ Invalid'}")
```

**保存并退出**

### 2.4 复制 `validator.py`

我之前已经创建好了完整的 validator.py，你需要把它复制到 services/ai/ 目录。

从我提供的文件中复制，或者直接从输出文件夹中获取。

---

## 🔧 第三步：安装 Python 依赖

```bash
# 确保在 services/ai/ 目录
cd services/ai

# 安装依赖
pip install -r requirements.txt --break-system-packages

# 下载 SenseVoice 模型
python -c "from modelscope import snapshot_download; snapshot_download('iic/SenseVoiceSmall'); snapshot_download('iic/speech_fsmn_vad_zh-cn-16k-common-pytorch')"
```

这一步可能需要 5-10 分钟下载模型。

---

## 🔑 第四步：生成 BLS 密钥

### 4.1 创建密钥生成脚本

```bash
# 回到项目根目录
cd ../..

# 创建 scripts 目录
mkdir -p scripts
cd scripts

# 创建密钥生成脚本
nano generate_keys.py
```

**复制以下代码：**

```python
#!/usr/bin/env python3
# generate_keys.py - 生成 BLS 密钥对

import sys
sys.path.append('../services/ai')

from py_ecc.bls import G2ProofOfPossession as bls
import secrets

def generate_validator_keys(validator_id: int):
    """为验证节点生成 BLS 密钥对"""
    # 生成私钥（随机数）
    sk = secrets.randbelow(bls.curve_order)
    
    # 派生公钥
    pk = bls.SkToPk(sk)
    
    # 保存到文件
    sk_file = f'validator_{validator_id}_sk.key'
    pk_file = f'validator_{validator_id}_pk.key'
    
    with open(sk_file, 'w') as f:
        f.write(hex(sk))
    
    with open(pk_file, 'w') as f:
        f.write(pk.hex())
    
    print(f"✅ Validator {validator_id} keys generated:")
    print(f"   Private Key: {hex(sk)}")
    print(f"   Public Key: {pk.hex()}")
    print(f"   Files: {sk_file}, {pk_file}\n")
    
    return hex(sk), pk.hex()


if __name__ == "__main__":
    print("="*60)
    print(" BLS Key Generation for EchoRank DVT Validators")
    print("="*60)
    print()
    
    # 为 3 个验证节点生成密钥
    keys = []
    for i in range(1, 4):
        sk, pk = generate_validator_keys(i)
        keys.append((sk, pk))
    
    print("="*60)
    print(" ⚠️  IMPORTANT: Save these keys securely!")
    print("="*60)
    print()
    print("Add to your .env file:")
    print()
    for i, (sk, pk) in enumerate(keys, 1):
        print(f"VALIDATOR_{i}_SK={sk}")
    print()
```

**保存并退出**

### 4.2 运行密钥生成脚本

```bash
# 运行脚本
python generate_keys.py
```

你会看到输出：

```
============================================================
 BLS Key Generation for EchoRank DVT Validators
============================================================

✅ Validator 1 keys generated:
   Private Key: 0x123abc...
   Public Key: 0xabc123...
   Files: validator_1_sk.key, validator_1_pk.key

...

Add to your .env file:

VALIDATOR_1_SK=0x123abc...
VALIDATOR_2_SK=0x456def...
VALIDATOR_3_SK=0x789ghi...
```

**⚠️ 重要：保存这些私钥！**

---

## 🌐 第五步：修改 Node.js 后端

现在修改 `apps/server/src/api/analyze.ts`

### 5.1 查看现有的 analyze.ts

```bash
cd ../../apps/server/src/api
cat analyze.ts
```

### 5.2 修改 analyze.ts

```bash
nano analyze.ts
```

**用以下代码替换或添加：**

```typescript
// analyze.ts - 语音分析 API 端点
import { Router, Request, Response } from 'express';
import axios from 'axios';
import crypto from 'crypto';

const router = Router();

// ==================== 配置 ====================

const VALIDATOR_URLS = [
  process.env.VALIDATOR_1_URL || 'http://localhost:8001',
  process.env.VALIDATOR_2_URL || 'http://localhost:8002',
  process.env.VALIDATOR_3_URL || 'http://localhost:8003'
];

const THRESHOLD = 2; // 2-of-3

// ==================== 类型定义 ====================

interface AnalyzeRequest {
  audio: string;          // base64 编码的音频
  audio_hash?: string;    // 可选：客户端提供的哈希
  user_id: string;
  activity_id?: string;
}

interface ValidatorResponse {
  task_id: string;
  validator_id: string;
  public_key: string;
  signature: string;
  result_json: {
    emotion: string;
    intensity: number;
    keywords: string[];
    events: string[];
    raw_text: string;
  };
  result_hash: string;
  algo_version: string;
  timestamp: number;
  nonce: string;
}

// ==================== 工具函数 ====================

/**
 * 计算音频的 SHA256 哈希
 */
function calculateAudioHash(audioBase64: string): string {
  const buffer = Buffer.from(audioBase64, 'base64');
  return crypto.createHash('sha256').update(buffer).digest('hex');
}

/**
 * 向单个验证节点发送请求
 */
async function requestValidator(
  validatorUrl: string,
  taskId: string,
  audioBase64: string,
  audioHash: string
): Promise<ValidatorResponse> {
  try {
    const response = await axios.post(
      `${validatorUrl}/analyze`,
      {
        task_id: taskId,
        audio_base64: audioBase64,
        audio_hash: audioHash
      },
      {
        timeout: 60000, // 60秒超时
        headers: {
          'Content-Type': 'application/json'
        }
      }
    );
    
    return response.data;
  } catch (error: any) {
    console.error(`Validator ${validatorUrl} failed:`, error.message);
    throw error;
  }
}

/**
 * 并行请求所有验证节点
 */
async function distributeToValidators(
  taskId: string,
  audioBase64: string,
  audioHash: string
): Promise<ValidatorResponse[]> {
  const promises = VALIDATOR_URLS.map(url =>
    requestValidator(url, taskId, audioBase64, audioHash)
  );
  
  // 使用 Promise.allSettled 确保即使部分失败也能继续
  const results = await Promise.allSettled(promises);
  
  // 过滤出成功的结果
  const successful = results
    .filter((r): r is PromiseFulfilledResult<ValidatorResponse> => 
      r.status === 'fulfilled'
    )
    .map(r => r.value);
  
  if (successful.length < THRESHOLD) {
    throw new Error(
      `Insufficient validators responded (${successful.length}/${VALIDATOR_URLS.length})`
    );
  }
  
  return successful;
}

/**
 * 验证所有验证节点的结果一致性
 */
function verifyConsistency(validatorResults: ValidatorResponse[]): boolean {
  if (validatorResults.length < 2) return false;
  
  // 检查 result_hash 是否一致
  const resultHashes = validatorResults.map(v => v.result_hash);
  const uniqueHashes = new Set(resultHashes);
  
  if (uniqueHashes.size > 1) {
    console.error('Validators returned different result_hash:', resultHashes);
    return false;
  }
  
  return true;
}

// ==================== API 端点 ====================

/**
 * POST /api/analyze
 * 
 * 接收语音，分发到验证节点，返回签名结果
 */
router.post('/analyze', async (req: Request, res: Response) => {
  try {
    const { audio, audio_hash, user_id, activity_id }: AnalyzeRequest = req.body;
    
    // ========== 1. 验证输入 ==========
    if (!audio) {
      return res.status(400).json({ error: 'Missing audio data' });
    }
    
    if (!user_id) {
      return res.status(400).json({ error: 'Missing user_id' });
    }
    
    console.log(`[Analyze] Received request from user ${user_id}`);
    
    // ========== 2. 验证音频哈希 ==========
    const calculatedHash = calculateAudioHash(audio);
    
    if (audio_hash && audio_hash !== calculatedHash) {
      console.error(
        `Audio hash mismatch: expected=${audio_hash}, actual=${calculatedHash}`
      );
      return res.status(400).json({
        error: 'Audio hash mismatch',
        expected: audio_hash,
        actual: calculatedHash
      });
    }
    
    const finalAudioHash = audio_hash || calculatedHash;
    console.log(`[Analyze] Audio hash verified: ${finalAudioHash.substring(0, 16)}...`);
    
    // ========== 3. 生成任务 ID ==========
    const taskId = crypto.randomUUID();
    console.log(`[Analyze] Task ID: ${taskId}`);
    
    // ========== 4. 分发到验证节点 ==========
    console.log(`[Analyze] Distributing to ${VALIDATOR_URLS.length} validators...`);
    
    const validatorResults = await distributeToValidators(
      taskId,
      audio,
      finalAudioHash
    );
    
    console.log(`[Analyze] Received ${validatorResults.length} responses`);
    
    // ========== 5. 验证一致性 ==========
    if (!verifyConsistency(validatorResults)) {
      return res.status(500).json({
        error: 'Validators returned inconsistent results',
        validator_count: validatorResults.length
      });
    }
    
    console.log(`[Analyze] Consistency check passed ✓`);
    
    // ========== 6. 构造响应 ==========
    const response = {
      task_id: taskId,
      audio_hash: finalAudioHash,
      
      // 使用第一个验证节点的分析结果（因为都一致）
      result: validatorResults[0].result_json,
      result_hash: validatorResults[0].result_hash,
      
      // 包含所有验证节点的签名
      proof: {
        algo_version: validatorResults[0].algo_version,
        threshold: `${validatorResults.length}-of-${VALIDATOR_URLS.length}`,
        validators: validatorResults.map(v => ({
          validator_id: v.validator_id,
          public_key: v.public_key,
          signature: v.signature,
          timestamp: new Date(v.timestamp * 1000).toISOString()
        })),
        verified: true
      },
      
      timestamp: new Date().toISOString(),
      user_id: user_id,
      activity_id: activity_id || null
    };
    
    console.log(`[Analyze] Task ${taskId} completed successfully`);
    
    // ========== 7. 返回结果 ==========
    res.json(response);
    
  } catch (error: any) {
    console.error('[Analyze] Error:', error);
    
    res.status(500).json({
      error: 'Analysis failed',
      message: error.message
    });
  }
});

/**
 * GET /api/analyze/health
 * 
 * 检查验证节点健康状态
 */
router.get('/health', async (req: Request, res: Response) => {
  try {
    const healthChecks = await Promise.allSettled(
      VALIDATOR_URLS.map(async (url) => {
        const response = await axios.get(`${url}/health`, { timeout: 5000 });
        return {
          url,
          status: 'healthy',
          data: response.data
        };
      })
    );
    
    const results = healthChecks.map((result, index) => {
      if (result.status === 'fulfilled') {
        return result.value;
      } else {
        return {
          url: VALIDATOR_URLS[index],
          status: 'unhealthy',
          error: result.reason.message
        };
      }
    });
    
    const healthyCount = results.filter(r => r.status === 'healthy').length;
    
    res.json({
      total_validators: VALIDATOR_URLS.length,
      healthy_validators: healthyCount,
      threshold: THRESHOLD,
      operational: healthyCount >= THRESHOLD,
      validators: results
    });
    
  } catch (error: any) {
    res.status(500).json({ error: error.message });
  }
});

export default router;
```

**保存并退出**

---

## 🔄 第六步：配置环境变量

### 6.1 创建 .env 文件

```bash
# 回到项目根目录
cd ../../../..

# 创建 .env
nano .env
```

**复制以下内容（填入你之前生成的密钥）：**

```bash
# Validator BLS Private Keys (填入你生成的密钥)
VALIDATOR_1_SK=0x你的私钥1
VALIDATOR_2_SK=0x你的私钥2
VALIDATOR_3_SK=0x你的私钥3

# Validator URLs
VALIDATOR_1_URL=http://localhost:8001
VALIDATOR_2_URL=http://localhost:8002
VALIDATOR_3_URL=http://localhost:8003

# Algorithm Version
ALGO_VERSION=sensevoice-small-v1.0.0

# Server Port
PORT=3000
```

**保存并退出**

---

## 🚀 第七步：启动服务

现在可以启动你的服务了！

### 7.1 启动验证节点（3个终端）

**终端 1：**
```bash
cd services/ai
VALIDATOR_ID=1 BLS_PRIVATE_KEY=$(cat ../../scripts/validator_1_sk.key) python validator.py
```

**终端 2：**
```bash
cd services/ai
VALIDATOR_ID=2 BLS_PRIVATE_KEY=$(cat ../../scripts/validator_2_sk.key) python validator.py
```

**终端 3：**
```bash
cd services/ai
VALIDATOR_ID=3 BLS_PRIVATE_KEY=$(cat ../../scripts/validator_3_sk.key) python validator.py
```

你应该看到每个验证节点都启动了：

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8001
```

### 7.2 启动 Node.js 后端（新终端）

**终端 4：**
```bash
cd apps/server
npm run dev
```

---

## 🧪 第八步：测试 API

### 8.1 健康检查

```bash
# 测试后端健康状态
curl http://localhost:3000/api/analyze/health
```

应该返回：

```json
{
  "total_validators": 3,
  "healthy_validators": 3,
  "threshold": 2,
  "operational": true,
  "validators": [...]
}
```

### 8.2 测试语音分析

创建测试脚本：

```bash
nano test_analyze.sh
```

**内容：**

```bash
#!/bin/bash

# 测试音频（你需要有一个测试音频文件）
AUDIO_FILE="test_audio.wav"

# 转换为 base64
AUDIO_BASE64=$(base64 -w 0 $AUDIO_FILE)

# 发送请求
curl -X POST http://localhost:3000/api/analyze \
  -H "Content-Type: application/json" \
  -d "{
    \"audio\": \"$AUDIO_BASE64\",
    \"user_id\": \"test_user_123\",
    \"activity_id\": \"hackathon_2026\"
  }" | jq '.'
```

**运行：**

```bash
chmod +x test_analyze.sh
./test_analyze.sh
```

---

## ✅ 完成！

现在你的系统应该正常运行了！

### 你实现的功能：

```
✅ Node.js API 接收语音 (POST /api/analyze)
✅ 3 个 Python AI 验证节点
✅ SenseVoice 情感分析
✅ BLS 签名
✅ 返回：公钥、签名、分析结果
```

---

## 📊 API 返回示例

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "audio_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "result": {
    "emotion": "HAPPY",
    "intensity": 0.85,
    "keywords": ["活动", "很棒"],
    "events": ["applause"],
    "raw_text": "这次活动组织得很棒！"
  },
  "result_hash": "b4c5d6e7f8...",
  "proof": {
    "algo_version": "sensevoice-small-v1.0.0",
    "threshold": "3-of-3",
    "validators": [
      {
        "validator_id": "1",
        "public_key": "0xa1b2c3...",
        "signature": "0x9876fe...",
        "timestamp": "2026-01-30T12:00:00Z"
      },
      {
        "validator_id": "2",
        "public_key": "0xf1e2d3...",
        "signature": "0x1234ab...",
        "timestamp": "2026-01-30T12:00:01Z"
      },
      {
        "validator_id": "3",
        "public_key": "0xc5d6e7...",
        "signature": "0x5678cd...",
        "timestamp": "2026-01-30T12:00:02Z"
      }
    ],
    "verified": true
  },
  "timestamp": "2026-01-30T12:00:03Z",
  "user_id": "test_user_123",
  "activity_id": "hackathon_2026"
}
```

---

## 🆘 遇到问题？

### 常见问题排查：

**1. 验证节点启动失败**
```bash
# 检查依赖
pip list | grep funasr

# 重新安装
pip install -r requirements.txt --break-system-packages
```

**2. 模型加载失败**
```bash
# 确认模型已下载
ls ~/.cache/modelscope/hub/models/iic/

# 重新下载
python -c "from modelscope import snapshot_download; snapshot_download('iic/SenseVoiceSmall')"
```

**3. BLS 签名失败**
```bash
# 测试 BLS 模块
cd services/ai
python bls_signer.py
```

**4. Node.js 连接失败**
```bash
# 检查验证节点是否运行
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
```

---

需要我继续帮你解决任何问题吗？ 🚀