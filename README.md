# 🎬 Visual Video Transcription

自動將視頻內容轉換為文字檔，包括語音辨識和視覺內容分析。系統能夠識別指示詞（如「這個」、「藍色部分」）並提取相應時刻的畫面，用視覺分析補充文字說明。

**語言**: 中文 | **Python**: 3.10+

---

## 🎯 功能概述

### 完整管線（5 個集成模塊）

```
影片 
  ↓
【步驟1】語音轉逐字稿 (Faster-Whisper)
  ↓
【步驟2】偵測指示詞 (Regex 配對)
  ↓
【步驟3】根據指示詞截幀 (FFmpeg)
  ↓
【步驟4】視覺分析 (Ollama LLaVA/Qwen)
  ↓
【步驟5】融合 (字符串替換)
  ↓
融合逐字稿 + JSON 數據
```

### 核心功能

| 模塊 | 功能 | 狀態 |
|------|------|------|
| **Transcriber** | 語音轉文字，添加時間戳 `[0:MM:SS]` | ✅ 完成 |
| **DeicticDetector** | 檢測指示詞（這、那、藍色、前面等） | ✅ 完成 |
| **FrameExtractor** | 在指示詞時刻提取視頻幀 | ✅ 完成 |
| **VisionAnalyzer** | 用 Ollama 分析圖片內容 | ✅ 完成 |
| **FusionEngine** | 用視覺描述替換指示詞 | ✅ 完成 |

---

## 📋 系統要求

### 軟體依賴

- **Python** 3.10+
- **FFmpeg** - 視頻幀提取
  - Windows: `choco install ffmpeg`
  - Mac: `brew install ffmpeg`
  - Linux: `apt install ffmpeg`
- **Ollama** - 多模態視覺分析
  - 下載: https://ollama.ai
  - 啟動: `ollama serve`
  - 拉取模型: `ollama pull qwen2.5vl:7b` 或 `ollama pull llava:latest`

### Python Kit

`requirements.txt`:
```
faster-whisper>=1.0.0
ffmpeg-python==0.2.0
requests>=2.31.0
ollama>=0.1.0
pydantic>=2.0.0
```

---

## 🚀 快速開始

### 1️⃣ 安裝

```bash
# Clone Repository
git clone https://github.com/Lienlientina/visual-video-transcription.git
cd visual-video-transcription

# Create Vitrual Environment
python -m venv .venv_videotrans

# Activate Vitual Environment（Windows）
.\.venv_videotrans\Scripts\Activate.ps1
# Activate Vitual Environment（Mac/Linux）
source .venv_videotrans/bin/activate

# Install Dependency
pip install -r requirements.txt
```

### 2️⃣ 配置

編輯 `config.py`：

```python
# 模型配置
DEVICE = "cpu"  # 或 "cuda"
WHISPER_MODEL = "base"  # "tiny", "small", "base", "medium", "large"
LLAVA_MODEL = "qwen2.5vl:7b"  # 或 "llava:latest"

# Ollama 設置
OLLAMA_BASE_URL = "http://localhost:11434"

# 指示詞列表（可自訂）
DEICTIC_WORDS = ["這", "那", "這個", "藍色", "前面", "後面", ...]
```

### 3️⃣ 運行完整管線

```bash
python tests/test_complete_pipeline.py <Video path> <逐字稿JSON path>

# 範例
python tests/test_complete_pipeline.py demo_video/video_demo1.mp4 outputs/transcripts/video_demo1.json
```

### 📤 輸出文件

```
outputs/
├── transcripts/
│   └── video_demo1.json          # 原始逐字稿（時間戳+文字）
├── frames/
│   ├── 0_00_00.jpg
│   ├── 0_00_34.jpg
│   └── ...                        # 截取的畫面(幀)
└── results/
    ├── video_demo1.txt            # 融合後的可讀逐字稿
    ├── video_demo1_fusion.json     # 融合詳細數據
    └── video_demo1_deictic.json    # 指示詞檢測結果
```

---

## 📁 項目結構

```
visual-video-transcription/
├── README.md                      # 本檔案
├── requirements.txt               # Python dependency
├── config.py                      # Configuration
├── utils.py                       # 工具函數
│   ├── seconds_to_timestamp()     # 轉換秒數為 [0:MM:SS] 格式
│   ├── find_deictic_words()       # 尋找指示詞
│   └── build_prompt_for_vision()  # 為視覺分析生成提示詞
│
├── modules/
│   ├── transcriber.py             # 語音轉文字
│   │   └── Transcriber class: transcribe(), save_transcript()
│   ├── deictic_detector.py        # 指示詞偵測
│   │   └── DeicticDetector class: detect_from_transcript()
│   ├── frame_extractor.py         # 影片畫面幀提取（FFmpeg）
│   │   └── FrameExtractor class: extract_frames_from_deictic()
│   ├── vision_analyzer.py         # 視覺分析
│   │   └── VisionAnalyzer class: analyze_image(), analyze_frames_batch()
│   └── fusion_engine.py           # 融合引擎
│       └── FusionEngine class: fuse()
│
├── tests/
│   ├── test_complete_pipeline.py  # 完整 pipeline 測試
│   └── test_vision_concise.py     # 簡潔視覺分析測試
│
├── outputs/                       # （不上傳到 Git）
│   ├── transcripts/               # 原始逐字稿
│   ├── frames/                    # 提取的視頻幀
│   └── results/                   # 融合結果
│
└── demo_video/                    # （不上傳到 Git）
    └── video_demo1.mp4            # 示例視頻
```

---

## 🔄 Data Flow Example

### 輸入：影片檔案 + 逐字稿

**原始逐字稿** (`video_demo1.json`):
```json
{
  "segments": [
    {
      "time": "[0:00:00]",
      "text": "各位同學好,這一節我們要介紹多變數函數...",
      "start": 0.0,
      "end": 5.2
    }
  ]
}
```

### 中間：指示詞偵測

```json
{
  "deictic_words": [
    {
      "timestamp": "[0:00:00]",
      "word": "這",
      "position": 6,
      "context_before": "各位同學好,",
      "context_after": "一節我們要介紹多變數函數..."
    }
  ]
}
```

### 中間：視覺分析

```json
{
  "analyses": [
    {
      "image_path": "outputs/frames/0_00_00.jpg",
      "description": "圖片顯示了一個數學教學投影片，標題是 The Chain Rule...",
      "success": true
    }
  ]
}
```

### 輸出：融合逐字稿

**文本版** (`video_demo1.txt`):
```
[0:00:00] 各位同學好,〔畫面：圖片顯示了一個數學教學投影片，標題是 The Chain Rule，展示了鏈式法則的定義和應用例子。〕一節我們要介紹多變數函數...
```

**JSON 版** (`video_demo1_fusion.json`):
```json
{
  "segments": [
    {
      "time": "[0:00:00]",
      "text": "各位同學好,〔畫面：...〕一節我們要介紹多變數函數...",
      "replacements": [
        {
          "word": "這",
          "description": "圖片顯示了一個數學教學投影片..."
        }
      ]
    }
  ]
}
```

---

## 🎨 視覺分析提示詞優化

### 改進策略

系統根據是否有指示詞生成不同的提示詞：

**有指示詞時** （簡潔模式）:
```
請只描述圖片中和「這個」相關的部分。
要求：
1. 簡潔明了 - 2-3句話就夠
2. 只說「這個」指的是什麼
3. 包含：顏色、位置、內容
4. 不要描述其他無關部分
```

**無指示詞時** （完整模式）:
```
請詳細分析這張圖片。特別要提到：
1. 【文字和公式】...
2. 【顏色和標示】...
3. 【位置和布局】...
4. 【對象和內容】...
```

### 輸出改進效果

| 場景 | 之前 | 之後 |
|------|------|------|
| 有指示詞「藍色部分」 | ~300 字（5 點詳細分析） | ~80 字（1-2 句簡潔說明） |
| 重複指示詞 | 重複完整分析 | 短小精悍 |
| 文本可讀性 | ❌ 冗長臃腫 | ✅ 清晰簡潔 |

---

## 📊 目前進度

### ✅ 已完成
- [x] 核心模塊架構設計（5 個模塊）
- [x] 語音轉文字 (Faster-Whisper)
- [x] 指示詞檢測 (Regex 配對)
- [x] 視頻幀提取 (FFmpeg)
- [x] 視覺分析集成 (Ollama)
- [x] 融合引擎（字符串替換）
- [x] 完整管線測試
- [x] 視覺提示詞優化（簡潔化）
- [x] 配置中心化
- [x] 工具函數模塊化

### 🚧 進行中 / 計劃中

- [ ] API 串聯 Gemini (Gemini 3.1 - flash lite)
- [ ] 提高畫面辨識能力
- [ ] 簡短說明畫面
- [ ] LLM 語義融合（更自然的文本流暢度）
- [ ] 相同時刻多個指示詞多個描述
- [ ] 輸出格式優化（Markdown, HTML）
- [ ] 支持多語言（英文、日文等）
- [ ] 性能優化（並行幀分析）
- [ ] UI / Web 介面
- [ ] 單元測試覆蓋
- [ ] 文檔完善

### ⚠️ 已知問題

1. **FFmpeg 依賴** - 需要系統級安裝，不在 Python dependency 中
2. **Ollama 推理速度** - 大模型推理較慢，GPU 加速需要 CUDA 支持
3. **記憶體占用** - LLaVA/Qwen 模型較大（7B 參數）
4. **多個指示詞時間重疊** - 目前不做自動去重
5. **非中文內容** - 主要針對中文優化

---

## 🛠️ 開發指南

### 運行個別模塊測試

```bash
# 只測試視覺分析
python test_vision_concise.py

# 運行完整管線
python tests/test_complete_pipeline.py <video_path> <transcript_path>
```

### 修改配置

編輯 `config.py` 調整：
- 模型大小 (`WHISPER_MODEL`)
- 計算設備 (`DEVICE = "cpu"` 或 `"cuda"`)
- 視覺模型 (`LLAVA_MODEL`)
- 指示詞列表 (`DEICTIC_WORDS`)

### 擴展指示詞

在 `config.py` 中修改 `DEICTIC_WORDS`:

```python
DEICTIC_WORDS = [
    "這", "那", "這個", "那個",
    "這裡", "那裡",
    "前面", "後面", "左邊", "右邊", "上面", "下面", "中間",
    "藍色", "紅色", "綠色",  # 可加入顏色
    # ... 自訂指示詞
]
```

---

## 📝 使用範例

### 完整流程

```bash
# 1. 確保 Ollama 正在運行
ollama serve

# 2. 新開終端，啟動虛擬環境
cd visual-video-transcription
.\.venv_videotrans\Scripts\Activate.ps1

# 3. 運行 pipeline
python tests/test_complete_pipeline.py my_video.mp4 my_transcript.json

# 4. 查看結果
type outputs/results/my_video.txt
```

### 自訂逐字稿

如果沒有現成的 JSON 逐字稿，可以：

```python
from modules.transcriber import Transcriber

transcriber = Transcriber()
result = transcriber.transcribe("my_video.mp4")
transcriber.save_transcript("my_transcript.json")
```

---
## Version History


### v0.1.0 (2026-05-14)
  - ✅ 5 個核心模塊完成
  - ✅ 完整管線集成
  - ✅ 視覺提示詞優化
  - 🚧 LLM 融合逐字稿
  - 🚧 提高畫面辨識能力

---

## 🎓 參考資料

- [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) - 語音辨識
- [Ollama](https://ollama.ai) - 本地 LLM 運行
- [FFmpeg](https://ffmpeg.org) - 影片處理
- [LLaVA](https://github.com/haotian-liu/LLaVA) - 視覺語言模型
- [Qwen2.5-VL](https://github.com/QwenLM/Qwen2.5-VL) - 多模態視覺模型

---

**最後更新**: 2026-05-14  
**狀態**: 🚀 主要功能完成，持續優化中
