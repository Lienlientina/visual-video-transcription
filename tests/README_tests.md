# 🧪 測試文件指南

## ⭐ 推薦：完整 pipeline 測試

**run the whole program (for complete demo)**

```bash
# 基本用法：transcript + detect deictic + 截幀 + vision analyze + 融合逐字稿與畫面解析
python tests/test_complete_pipeline.py "your_video.mp4"

# 進階用法：使用已經存在的逐字稿
python tests/test_complete_pipeline.py "your_video.mp4" "your_video_transcript.json"

```

**輸出內容**
- ✅ `outputs/results/{video_name}.txt` - 融合後的文本版逐字稿
- ✅ `outputs/results/{video_name}_fusion.json` - 完整融合 data

---

## 🔧 Unit Test (用於開發/驗證 module)

### 1️⃣ 語音轉逐字稿測試
```bash
python tests/test_transcriber.py "your_video.mp4"
```
**用途**：驗證 Whisper 轉錄、自動語言偵測（修正混合語言）

**輸出**：`outputs/transcripts/<transcript_name>.json`

---

### 2️⃣ Deictic Detect Test
```bash
python tests/test_deictic_detector.py "your_video_transcript.json"
```
**用途**：驗證三層法過濾系統
- 第一層：語法規則過濾
- 第二層：AI 判斷是否需要 vision analyze
- 第三層：完整視覺分析（僅需要時）

**輸出**：
- 指示詞列表（含精確秒數、need_vision tag）
- API 調用統計

---

### 3️⃣ Frame Extract Test
```bash
python tests/test_frame_extractor.py "your_video.mp4" "your_video_transcript.json"
```
**用途**：驗證 FFmpeg 在精確秒數處截圖

**輸出**：`outputs/frames/<frame_files>.jpg`

---

### 4️⃣ Vision Analysis Test
```bash
# 測試單張圖片
python tests/test_vision_analyzer.py "your_frames.jpg"

# 或測試整個幀目錄（批量分析）
python tests/test_vision_analyzer.py "outputs/frames"
```
**用途**：驗證 Gemini 3.1 Flash Lite 視覺分析

**輸出**：圖片描述和 API 成功/失敗統計

---

### 5️⃣ Fusion Test
```bash
python tests/test_fusion_engine.py "your_video_transcript.json"
```
**用途**：驗證指示詞補充融合邏輯

**選項**：可提供 deictic_data.json 和 vision_data.json 進行完整融合

---

## 🐛 故障排除

**問題：API Key 錯誤**
```
解決：檢查 .env 文件中的 GEMINI_API_KEY
python -c "import os; print(os.getenv('GEMINI_API_KEY'))"
```

**問題：FFmpeg 不存在**
```
Windows: choco install ffmpeg
Mac: brew install ffmpeg
Linux: apt install ffmpeg
```

**問題：VirtualEnv 錯誤**
```
# 重新激活虛擬環境
source .venv_videotrans/bin/activate     # Mac/Linux
.venv_videotrans\Scripts\Activate.ps1    # Windows
```

---

## 📝 輸出文件說明

| 文件位置 | 內容 | 用途 |
|---------|------|------|
| `outputs/transcripts/*.json` | 原始逐字稿 | 數據記錄 |
| `outputs/frames/*.jpg` | 截取的影片幀 | 視覺分析輸入 |
| `outputs/results/*.txt` | 融合後的文本 | 最終可讀結果 |
| `outputs/results/*_fusion.json` | 完整融合數據 | 結構化數據 |