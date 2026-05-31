# 🎬 Multi-Language Video Transcription with Visual Insights

自動將影片內容轉換為文字檔，包括語音辨識和視覺內容分析。系統能夠識別指示詞（如「這個」、「藍色部分」、「this function」）並提取相應時刻的畫面，用 AI 視覺分析補充文字說明。支援中英文自動偵測。目標是讓使用者可以單看文字檔就理解影片內容。

**語言**: 中文 | English | **Python**: 3.10+

---

## 🎯 功能概述

### 完整管線（5 個集成模塊）

```
影片 
  ↓
【步驟1】語音轉逐字稿 + 語言自動偵測 (Faster-Whisper)
  ↓
【步驟2】多語言指示詞檢測 + 三層智能過濾
  • 第一層：規則檢測 (語法模式)
  • 第二層：AI 判斷 (Gemini 決策)
  • 第三層：視覺分析 (完整分析)
  ↓
【步驟3】精確秒數截幀 (FFmpeg ± 0.1秒)
  ↓
【步驟4】視覺分析 (Gemini 3.1 Flash Lite)
  ↓
【步驟4.5】回想檢測 (Recall Detection)
  • 純 LLM 語義分析（Gemini 3.1 Flash Lite）
  ↓
【步驟5b】回想截圖提取 + ROI 裁切
  • Vision API ROI 偵測 (失敗時直接輸出完整圖片)
  • 保存原始截圖 + 裁切版本
  ↓
【步驟5】補充式融合 + 句子合併 (保留原文)
  ↓
融合逐字稿 + JSON 詳細數據 + 可讀性優化
```

### 核心功能

| 模塊 | 功能 | 狀態 |
|------|------|------|
| **Transcriber** | 語音轉文字 + 語言自動偵測 + 時間戳 | ✅ 完成 |
| **DeicticDetector** | 多語言指示詞檢測 + 三層智能過濾 | ✅ 完成 |
| **FrameExtractor** | 精確秒數截幀（±0.1秒） | ✅ 完成 |
| **VisionAnalyzer** | Gemini 3.1 Flash Lite 視覺分析 | ✅ 完成 |
| **FusionEngine** | 補充式融合 + 句子合併 | ✅ 完成 |
| **ROIDetector** | Recall 截圖 ROI 偵測 + 裁切 | ✅ 完成 |

---

## 📋 系統要求

### 軟體依賴

- **Python** 3.10+
- **FFmpeg** - 影片幀提取
  - Windows: `choco install ffmpeg`
  - Mac: `brew install ffmpeg`
  - Linux: `apt install ffmpeg`
- **Gemini API** - 多模態視覺分析
  - 申請 API Key: https://aistudio.google.com
  - 設置環境變數或 `.env` 文件

### Python Kit

`requirements.txt`:
```
faster-whisper>=1.0.0
ffmpeg-python==0.2.0
requests>=2.31.0
google-generativeai>=0.3.0
python-dotenv>=0.19.0
nltk>=3.8.0
opencv-python>=4.5.0
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

**使用 `.env` 文件（推薦）**

複製 `.env.example` 為 `.env` 並填入：
```ini
GEMINI_API_KEY=your-api-key-here
```

**編輯 `config.py`**

```python
# 模型配置
DEVICE = "cpu"  # 或 "cuda"
WHISPER_MODEL = "base"  # "tiny", "small", "base", "medium", "large"
GEMINI_MODEL = "gemini-3.1-flash-lite"  # 多模態視覺分析 text-out models

# Gemini API（從 .env 讀取）
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
```

### 3️⃣ 運行完整管線

```bash
# 基本用法：自動轉錄 + 偵測 + 截幀 + 分析 + 融合
python tests/test_complete_pipeline.py "your_video"

# 進階用法：使用已經存在的的逐字稿
python tests/test_complete_pipeline.py "your_video" "your_video_transcript_json"
```

詳見 [tests/README_tests.md](tests/README_tests.md) 了解各個單元測試

### 📤 輸出文件

```
outputs/
├── transcripts/
│   └── <video_name>.json          # 原始逐字稿（時間戳+文字+語言+精確秒數）
├── frames/
│   └── <video_name>_MM_SS_precise_X_XX.jpg           # 指示詞截幀
└── results/
    ├── frames/
    │   ├── <video_name>_recall_<id>_original.png     # Recall 原始截圖（完整圖片）
    │   └── <video_name>_recall_<id>_cropped.png      # Recall 裁切圖片（ROI 檢測後的相關區域）
    ├── <video_name>.txt            # 融合後的可讀逐字稿
    ├── <video_name>_fusion.json    # 融合詳細數據（包括 Recall 標注）
    └── <video_name>.srt            # SRT caption file
```

### 🎞️ 使用字幕

生成的 `.srt` 檔案可與影片搭配：

**VLC 播放器 (推薦)**
1. 在 VLC 中打開影片
2. 字幕 → 添加字幕檔案 → 選擇 `<video_name>.srt`
3. 按 `V` 快速開/關字幕

**Windows 媒體播放器**
1. 將 `.srt` 檔案放在與影片相同的目錄
2. 檔名須與影片相同，如 `demo.mp4` 對應 `demo.srt`
3. 打開影片時自動載入字幕

**其他支援 SRT 的播放器**
- YouTube（上傳為內嵌字幕）
- OBS（直播用）
- Shotcut、DaVinci Resolve（剪輯用）
---

## 📁 項目結構

```
visual-video-transcription/
├── README.md
├── requirements.txt
├── config.py                      # model, 詞表, dir
├── .env.example
├── .gitignore
├── utils.py                       # tool functions
│   ├── seconds_to_timestamp()     # 轉換秒數為 [H:MM:SS] 格式
│   ├── timestamp_to_seconds()     # 轉換時間戳為秒數
│   ├── find_deictic_words()       # 多語言 deictic words 尋找
│   ├── check_skip_pattern()       # 第一層：語法過濾
│   ├── ask_vision_decision()      # 第二層：AI 輕量判斷
│   └── decide_vision_needed()     # 三層法 main
│
├── modules/
│   ├── transcriber.py             # 語音轉文字 + 語言自動偵測
│   │   └── Transcriber class: transcribe(), save_transcript()
│   ├── deictic_detector.py        # 多語言指示詞偵測 + 精確時間
│   │   └── DeicticDetector class: detect_from_transcript()
│   ├── recall_detector.py         # 回想(Recall)檢測 + 語義比對
│   │   └── RecallDetector class: detect_recalls()
│   ├── frame_extractor.py         # 精確秒數截幀 (FFmpeg)
│   │   └── FrameExtractor class: extract_frames_from_deictic()
│   ├── vision_analyzer.py         # Gemini 視覺分析
│   │   └── VisionAnalyzer class: analyze_image(), analyze_frames_batch()
│   ├── fusion_engine.py           # 補充式融合 + 句子合併
│   │   └── FusionEngine class: fuse(), generate_recall_frames()
│   ├── roi_detector.py            # Recall 截圖 ROI 偵測與裁切
│   │   └── ROIDetector class: detect_and_crop()
│   └── subtitle_converter.py      # Generate SRT caption
│       └── SubtitleConverter class: fused_json_to_srt()
│
├── tests/
│   ├── README_tests.md            # 測試使用說明
│   ├── test_complete_pipeline.py  # 完整 pipeline 測試（推薦）
│   ├── test_transcriber.py        # 語音轉文字測試
│   ├── test_deictic_detector.py   # 指示詞檢測測試
│   ├── test_frame_extractor.py    # 截幀測試
│   ├── test_vision_analyzer.py    # 視覺分析測試
│   ├── test_fusion_engine.py      # 融合測試
│   └── test_subtitle_converter.py # 字幕轉換測試
│
├── outputs/                       # （不上傳 Git）
│   ├── transcripts/               # 原始逐字稿
│   ├── frames/                    # 截幀
│   └── results/                   # 融合結果
│
└── demo_video/                    # （不上傳 Git）
    └── <sample_video.mp4>
```

---

## 🔄 Data Flow Example

### 輸入：影片檔案 + 自動逐字稿

**原始逐字稿** (自動生成或提供):
```json
{
  "filename": "tutorial_math.mp4",
  "language": "zh",
  "segments": [
    {
      "time": "[0:00:15]",
      "text": "各位同學好，這個公式展示了鏈式法則...",
      "start": 15.0,
      "end": 22.5
    }
  ]
}
```

### 中間：三層過濾決策

**Layer 1 結果** (規則檢測):
```
"這個公式展示了" → 規則不匹配 → 繼續 Layer 2
```

**Layer 2 結果** (AI 輕量判斷):
```
Gemini: "Is '這個' referring to visual content?"
Response: YES → 需要視覺分析
```

**Layer 3 結果** (完整視覺分析):
```json
{
  "image": "tutorial_math_0_00_15_precise_3_42.jpg",
  "description": "白板上的藍色公式，展示了 Chain Rule 的定義"
}
```

### 輸出：融合逐字稿（可讀 + 結構化）

**文本版** (`tutorial_math.txt`):
```
[0:00:15] 各位同學好，這個[白板上的藍色公式，展示了鏈式法則的定義]公式展示了鏈式法則...
```

**JSON 版** (`tutorial_math_fusion.json`):
```json
{
  "filename": "tutorial_math.mp4",
  "language": "zh",
  "segments": [
    {
      "time": "[0:01:06]",
      "text": "然後在乘上,裡面這[\\sin(x^2)]一層就是Sine X是平方的圍分,接下來我們在對這個[\\sin(x^2)]藍色的部分進行圍分,因此前面的部分照超,那後面Sine的圍分就變成Cosine,取值在X是平方,",
      "original_text": "然後在乘上,裡面這一層就是Sine X是平方的圍分,接下來我們在對這個藍色的部分進行圍分,因此前面的部分照超,那後面Sine的圍分就變成Cosine,取值在X是平方,",
      "replacements": [
        {
          "word": "這個",
          "position": 33,
          "supplement": "\\sin(x^2)"
        },
        {
          "word": "這",
          "position": 8,
          "supplement": "\\sin(x^2)"
        }
      ],
      "modified": true,
      "precise_times": [
        {
          "word": "這個",
          "precise_seconds": 75.3655421686747
        },
        {
          "word": "這",
          "precise_seconds": 68.80831325301205
        }
      ]
    }
  ]
}
```

---

## 三層過濾系統詳解

為提高效率，系統採用漸進式過濾策略，避免對所有指示詞進行完整視覺分析

完整分析每個指示詞的視覺內容成本高（大量 API 調用），但許多指示詞實際上不需要視覺補充（如「這就是」、"there is"）-> **三層漸進式過濾**

```
┌─────────────────────────────────────────┐
│ 第一層：規則檢測                         │
│ SKIP_PATTERNS 匹配                      │
│ ✅ "這就是" → 跳過                      │
│ ✅ "那表示" → 跳過                      │
│ ✅ "that is why" → 跳過                │
└─────────────────────────────────────────┘
                    ↓ (未匹配)
┌─────────────────────────────────────────┐
│ 第二層：AI 輕量決策                      │
│ Gemini Flash 二元問題                   │
│ Prompt: "是物理還是概念？"               │
│ Response: YES/NO                        │
└─────────────────────────────────────────┘
                    ↓ (YES)
┌─────────────────────────────────────────┐
│ 第三層：完整視覺分析                      │
│ 提取幀 + 詳細分析                        │
│ 返回精細的視覺描述                       │
└─────────────────────────────────────────┘
```

**成本效益**: 假設 1000 個指示詞
- 第一層（規則）篩除 ~30%
- 第二層（AI 輕量判斷）篩除 ~50%
- 第三層（完整視覺分析）處理 ~20%
- **成本相比完整分析降低 80%**

---

## 📊 目前進度

### ✅ 已完成
- [x] 核心 module 架構設計（5 modules）
- [x] 語音轉文字 + 語言自動偵測 (Faster-Whisper)
- [x] 多語言指示詞檢測（中英文）
- [x] LLM 語義修正及錯字修改（Gemini JSON 格式）
- [x] 三層智能過濾系統（規則 + AI + 視覺）
- [x] 精確秒數定位（±0.1秒）
- [x] 影片幀提取 (FFmpeg)
- [x] Gemini 3.1 Flash Lite 視覺分析集成
- [x] 句子合併優化（保留原文及可讀性）
- [x] 影片加字幕功能（SRT 軟字幕）
- [x] Pipeline Test
- [x] Unit Test
- [x] 回想內容識別（Recall detection）— 純 LLM 方式，語義分析，信心度過濾
- [x] 有效分段 / 句子合併優化 — 修復語言偵測誤判
- [x] Recall 截圖提取 + ROI 裁切 — Vision API + 完整圖片備選
- [x] 並行截圖生成 — 為每個 Recall 生成原始+裁切圖

### 🚧 進行中 / 計劃中

- [x] 影片加字幕功能（軟字幕）
  - 將融合逐字稿渲染為 SRT 字幕
  - 時間軸精確同步

- [x] 回想內容識別與時間戳
  - 偵測「剛剛提到的」、「前面說過」等回想型指示詞，以LLM判斷回想段落
  - 已能將回想標注融合到輸出（JSON/TXT/SRT）
  - 融合到逐字稿中

- [x] 智能截圖相關內容
  - ✅ Recall frame 提取時間修復：使用被回想段落的時間而非 trigger segment start
  - ✅ ROI 偵測 Prompt 增強：包含 trigger text、recall text 的完整上下文
  - ✅ 錯誤處理改進：顯示實際 API 錯誤信息

- [ ] 字幕+圖片鑲嵌回影片
  - 使用 FFmpeg overlay 或 OpenCV
  - 或轉出 WebVTT + 副本集合格式

- [ ] 滑鼠/指標偵測
- [ ] 相同時刻多個指示詞多個描述自動去重
- [ ] 輸出格式優化（Markdown, HTML, SRT 字幕）
- [ ] 性能優化（並行幀分析）

---

## 🛠️ 開發指南

### 運行個別 module 測試

詳見 [tests/README_tests.md](tests/README_tests.md)：

```bash
# 運行完整 pipeline （推薦）
python tests/test_complete_pipeline.py <video_file>

# 或測試單個 moudule
python tests/test_transcriber.py <video_file>
python tests/test_deictic_detector.py <transcript_json>
python tests/test_frame_extractor.py <video_file> <transcript_json>
python tests/test_vision_analyzer.py <frame_file>
python tests/test_fusion_engine.py <transcript_json>
```

### 修改配置

編輯 `config.py` 調整：
- 模型大小 (`WHISPER_MODEL`)
- 計算設備 (`DEVICE = "cpu"` 或 `"cuda"`)
- Gemini 模型 (`DEICTIC_DECISION_MODEL`, `VISION_ANALYSIS_MODEL`)
- 指示詞列表 (`DEICTIC_WORDS_ZH`, `DEICTIC_WORDS_EN`)
- 過濾規則 (`SKIP_PATTERNS_ZH`, `SKIP_PATTERNS_EN`)

### 擴展指示詞

在 `config.py` 中修改對應語言的詞表：

```python
# 中文
DEICTIC_WORDS_ZH = [
    "這", "那", "這個", "那個",
    "這裡", "那裡",
    "前面", "後面", "左邊", "右邊", "上面", "下面", "中間",
    "藍色", "紅色", "綠色",  # 可加入顏色
    # ... 自訂指示詞
]

# 英文
DEICTIC_WORDS_EN = [
    "this", "that", "here", "there",
    "left", "right", "top", "bottom", "middle",
    # ... 自訂指示詞
]
```

### 在 Python 專案中引用 module

```python
from modules.transcriber import Transcriber
from modules.deictic_detector import DeicticDetector
from modules.frame_extractor import FrameExtractor
from modules.vision_analyzer import VisionAnalyzer
from modules.fusion_engine import FusionEngine

# 1. 轉錄
transcriber = Transcriber()
transcript = transcriber.transcribe("my_video.mp4")
transcriber.save_transcript("my_transcript.json")

# 2. 檢測指示詞
detector = DeicticDetector()
deictic_data = detector.detect_from_transcript("my_transcript.json")

# 3. 提取幀
extractor = FrameExtractor("my_video.mp4")
frames = extractor.extract_frames_from_deictic(deictic_data)

# 4. 視覺分析
analyzer = VisionAnalyzer()
analyses = analyzer.analyze_frames_batch(frames)

# 5. 融合結果
fusion = FusionEngine()
result = fusion.fuse(transcript, analyses)
```

---
## Version History

### v1.2.3 (2026-05-31)
  - ✅ **Recall Frame 時間修復**：使用被回想段落及內容的畫面而非 trigger segment time
  - ✅ **ROI 偵測 Prompt 增強**：Vision API 現包含完整語境
    - 包含：trigger_cue（觸發詞）+ trigger_text（觸發句子）+ recalled_text（被回想內容）
    - 提高 ROI 偵測精度，減少截圖內容重複或錯誤
  - ✅ **錯誤處理改進**：Vision API 失敗時顯示實際錯誤信息

### v1.2.2 (2026-05-26)
  - ✅ ROI 偵測系統改進：Vision API 優先 → 完整圖片備選
  - ✅ Recall 截圖生成：為每個 Recall 自動提取幀 + 裁切
  - ✅ 終端輸出改進：顯示時間戳+觸發詞+檔案路徑
  - ✅ 支援 PPT/圖片/彩色背景內容

### v1.2.1 (2026-05-26)
  - ✅ Recall Detection 從 Embedding 方法改成純 LLM（Gemini 3.1 Flash Lite）
  - ✅ 英文模式優化：信心度過濾 ≥0.75 + 擴展跳過模式
  - ✅ 修復英文 "there/this" 誤判（減少 ~60%）
  - ✅ 修復語言自動偵測強制中文問題

### v1.2.0 (2026-05-21)
  - ✅ 新增內容回想功能並標註在 output (.json, .txt, .srt)
  - ✅ 修復 segment 過長且包含其他 segment text 的問題
  - ✅ 修復語義修正語言錯誤問題

### v1.1.0 (2026-05-20)
  - ✅ 修復 Gemini API Rate Limit 問題（批量語義修正：32 → 1 API call）
  - ✅ 自動分割過長字幕 (Transriber)
  - ✅ SRT 字幕

### v1.0.0 (2026-05-15)
  - ✅ 多語言支持（中英文自動偵測）
  - ✅ 三層智能過濾系統（規則 + AI + 視覺）
  - ✅ 精確秒數定位（±0.1秒）
  - ✅ Gemini 3.1 Flash Lite 集成
  - ✅ 句子合併（可讀性優化）
  - ✅ 完整測試文檔和使用指南

### v0.1.0 (2026-05-14)
  - ✅ 5 個核心 module 完成
  - ✅ 完整管線集成
  - ✅ 視覺提示詞優化
  - 🚧 LLM 融合逐字稿
  - 🚧 提高畫面辨識能力

---

## 🎓 參考資料

- [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) - 快速語音辨識引擎
- [Gemini API](https://ai.google.dev/) - Google 多模態 AI 服務
- [FFmpeg](https://ffmpeg.org) - 多功能媒體框架

---

**最後更新**: 2026-05-26  
**版本**: v1.2.1  
**狀態**: 功能完整，已驗證，持續優化
