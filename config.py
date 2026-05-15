"""
集中配置文件 - 所有配置在這裡，方便切換設備和模型
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# ============ 設備配置 ============
DEVICE = "cpu"  # 改為 "cuda" 如果有顯卡

# ============ 模型配置 ============
WHISPER_MODEL = "base"  # faster-whisper 模型尺寸: tiny, base, small, medium, large

# ============ Gemini API ============
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-3.1-flash-lite"  # 視覺分析模型

# 指示詞判斷和視覺分析都用同一模型
DEICTIC_DECISION_MODEL = "gemini-3.1-flash-lite"  # 第二層：判斷是否需要視覺
VISION_ANALYSIS_MODEL = "gemini-3.1-flash-lite"    # 第三層：分析視覺內容

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

# ============ 指示詞配置（多語言） ============

# 中文指示詞
DEICTIC_WORDS_ZH = [
    "這個", "那個", "這邊", "那邊", "這裡", "那裡",
    "這", "那", "它", "這些", "那些",
    "上面", "下面", "左邊", "右邊", "中間", "前面", "後面", "上方", "下方", "旁邊"
]

# 英文指示詞
DEICTIC_WORDS_EN = [
    "this", "that", "here", "there",
    "this one", "that one", "this area", "that area",
    "front", "back", "left", "right", "top", "bottom", "middle", "side",
    "above", "below", "beside", "around", "between"
]

# 預設用中文
DEICTIC_WORDS = DEICTIC_WORDS_ZH

# 語言詞表映射
DEICTIC_WORDS_MAP = {
    "zh": DEICTIC_WORDS_ZH,
    "en": DEICTIC_WORDS_EN,
}


# ============ 第一層：語法過濾模式 ============
# 這些模式前後出現的指示詞，99% 不需要視覺補充

SKIP_PATTERNS_ZH = [
    "這就是",      # 「這就是為什麼」
    "這表示",      # 「這表示我們」
    "這意味著",    # 抽象結論
    "這個概念",    # 直接說「概念」
    "這個想法",    # 直接說「想法」
    "這個問題",    # 直接說「問題」
    "這是因為",    # 因果解釋
    "這說明了",    # 抽象說明
    "那就是",
    "那表示",
]

SKIP_PATTERNS_EN = [
    "that is",         # 「that is why」
    "that means",
    "this is why",
    "this concept",
    "this idea",
    "this means",
    "this explains",
    "this shows",
    "this is because",
    "that explains",
]

# 語言模式映射
SKIP_PATTERNS_MAP = {
    "zh": SKIP_PATTERNS_ZH,
    "en": SKIP_PATTERNS_EN,
}
