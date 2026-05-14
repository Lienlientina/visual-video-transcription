"""
集中配置文件 - 所有配置在這裡，方便切換設備和模型
"""
import os
from pathlib import Path

# ============ 設備配置 ============
DEVICE = "cpu"  # 改為 "cuda" 如果有顯卡

# ============ 模型配置 ============
WHISPER_MODEL = "base"  # faster-whisper 模型尺寸: tiny, base, small, medium, large
LLAVA_MODEL = "llava:latest"   # Ollama LLaVA model
FUSION_MODEL = "mistral"  # Ollama 文本融合模型

# ============ Ollama API ============
OLLAMA_BASE_URL = "http://localhost:11434"

# ============ 路徑配置 ============
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "outputs"
FRAMES_DIR = OUTPUT_DIR / "frames"
TRANSCRIPTS_DIR = OUTPUT_DIR / "transcripts"
RESULTS_DIR = OUTPUT_DIR / "results"
DEMO_VIDEO_DIR = BASE_DIR / "demo_video"

# 建立輸出目錄（如果不存在）
for dir_path in [OUTPUT_DIR, FRAMES_DIR, TRANSCRIPTS_DIR, RESULTS_DIR, DEMO_VIDEO_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# ============ 時間戳格式 ============
TIMESTAMP_FORMAT = "[0:{m:02d}:{s:02d}]"  # [0:00:23] 格式

# ============ 指示詞配置 ============
DEICTIC_WORDS = [
    "這個", "那個", "這邊", "那邊", "這裡", "那裡",
    "這", "那", "它", "這些", "那些",
    "上面", "下面", "左邊", "右邊", "中間","前面", "後面", "上方", "下方", "旁邊"
]
