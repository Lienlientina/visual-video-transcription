"""
通用工具函數 - 時間轉換、指示詞偵測等
"""
import re
from config import (
    DEICTIC_WORDS_MAP, SKIP_PATTERNS_MAP,
    DEICTIC_DECISION_MODEL, GEMINI_API_KEY,
    TIMESTAMP_FORMAT
)


# ============ 三層法：判斷是否需要視覺分析 ============

def check_skip_pattern(sentence, deictic_word, language="zh"):
    """
    第一層：語法過濾
    檢查指示詞前後是否有跳過模式
    
    Args:
        sentence (str): 完整句子
        deictic_word (str): 指示詞
        language (str): 語言 ("zh" 或 "en")
    
    Returns:
        bool: True 應該跳過，False 繼續判斷
    """
    skip_patterns = SKIP_PATTERNS_MAP.get(language, SKIP_PATTERNS_MAP.get("zh"))
    
    for pattern in skip_patterns:
        if pattern in sentence:
            return True
    
    return False


# ← 新增：緩存指示詞判斷結果，避免重複調用 API
_VISION_DECISION_CACHE = {}

def ask_vision_decision(deictic_word, context_before, context_after, language="zh"):
    """
    第二層：輕量 AI 判斷
    用 Gemini Flash 判斷指示詞是否指代畫面內容
    
    Args:
        deictic_word (str): 指示詞
        context_before (str): 前文
        context_after (str): 後文
        language (str): 語言
    
    Returns:
        bool: True 需要視覺，False 不需要
    """
    # ← 新增：檢查緩存
    cache_key = (deictic_word, language)
    if cache_key in _VISION_DECISION_CACHE:
        return _VISION_DECISION_CACHE[cache_key]
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel(DEICTIC_DECISION_MODEL)
        
        full_context = f"{context_before}{deictic_word}{context_after}"
        
        if language == "zh":
            prompt = f"""在這個句子中：「{full_context}」

            「{deictic_word}」是指畫面上的具體物體/位置，還是語言上的概念/抽象參考？

            只回答「畫面」或「概念」："""
        else:  # English
            prompt = f"""In this sentence: "{full_context}"

            Does "{deictic_word}" refer to something visible on screen/in the image, or is it an abstract concept?

            Answer only "visual" or "abstract":"""
        
        response = model.generate_content(prompt)
        answer = response.text.strip().lower()
        
        # 檢查回答
        if language == "zh":
            result = "畫面" in answer
        else:
            result = "visual" in answer
        
        # ← 新增：儲存到緩存
        _VISION_DECISION_CACHE[cache_key] = result
        return result
    
    except Exception as e:
        print(f"[Warning] 判斷指示詞『{deictic_word}』失敗: {e}")
        # ← 新增：失敗時也緩存結果（預設 False），避免重複出錯
        _VISION_DECISION_CACHE[cache_key] = False
        return False


def decide_vision_needed(deictic_word, context_before, context_after, language="zh"):
    """
    三層法主函數：判斷是否需要視覺分析
    
    層次：
    1️⃣ 第一層：語法過濾 - 快速排除不需要看畫面的情況
    2️⃣ 第二層：AI 輕量判斷 - 判斷是畫面還是概念
    3️⃣ 第三層：視覺分析 - 只在前兩層都通過時調用
    
    Args:
        deictic_word (str): 指示詞
        context_before (str): 前文（前20字）
        context_after (str): 後文（後20字）
        language (str): 語言 ("zh" 或 "en")
    
    Returns:
        bool: True 需要視覺分析，False 不需要
    """
    full_context = f"{context_before}{deictic_word}{context_after}"
    
    # ❌ 第一層：語法過濾 - 快速排除
    if check_skip_pattern(full_context, deictic_word, language):
        return False
    
    # ❓ 第二層：AI 輕量判斷
    return ask_vision_decision(deictic_word, context_before, context_after, language)


def seconds_to_timestamp(seconds):
    """
    將秒數轉換為時間戳格式 [0:MM:SS]
    
    Args:
        seconds (float): 秒數，例如 23.5
    
    Returns:
        str: 格式化時間戳，例如 "[0:00:23]"
    
    Examples:
        >>> seconds_to_timestamp(23)
        '[0:00:23]'
        >>> seconds_to_timestamp(125)
        '[0:02:05]'
    """
    total_seconds = int(seconds)
    minutes = total_seconds // 60
    secs = total_seconds % 60
    return f"[0:{minutes:02d}:{secs:02d}]"


def timestamp_to_seconds(timestamp_str):
    """
    將時間戳 [0:MM:SS] 轉回秒數
    
    Args:
        timestamp_str (str): 時間戳，例如 "[0:00:23]"
    
    Returns:
        int: 秒數，例如 23
    """
    # 提取 [0:MM:SS] 中的分秒
    match = re.search(r'\[0:(\d+):(\d+)\]', timestamp_str)
    if match:
        minutes = int(match.group(1))
        seconds = int(match.group(2))
        return minutes * 60 + seconds
    return 0


def find_deictic_words(text, language="zh"):
    """
    在文本中找出所有指示詞及其位置
    
    Args:
        text (str): 文本內容
        language (str): 語言 ("zh" 或 "en")
    
    Returns:
        list: [{"word": "這個", "pos": 5, "end": 7}, ...]
    
    Examples:
        >>> find_deictic_words("把這個公式代入那個方程式")
        [{'word': '這個', 'pos': 2, 'end': 4}, {'word': '那個', 'pos': 8, 'end': 10}]
    """
    results = []
    
    # 獲取對應語言的詞表
    deictic_words = DEICTIC_WORDS_MAP.get(language, DEICTIC_WORDS_MAP.get("zh"))
    
    # 構建正則模式 - 匹配任何指示詞
    pattern = '|'.join(re.escape(word) for word in deictic_words)
    
    for match in re.finditer(pattern, text):
        results.append({
            'word': match.group(),
            'pos': match.start(),
            'end': match.end()
        })
    
    return results


def build_prompt_for_vision(image_path, context="", deictic_word="", language="en"):
    """
    為 Gemini 構建圖片理解提示詞
    
    Args:
        image_path (str): 圖片路徑
        context (str): 額外上下文，例如前後的文字內容
        deictic_word (str): 指示詞，例如「這個」、「藍色的部分」、"this"、"that part"
        language (str): 語言代碼，"en" 或 "zh"（預設"en"）
    
    Returns:
        str: 提示詞內容
    """
    if language == "en":
        # 英文提示詞
        if deictic_word:
            # 有指示詞時，提取簡潔的內容補充
            prompt = f"""Look at this image and find what "{deictic_word}" refers to.

            If you see:
            - Formula/equation → write only that math expression
            - Text/code → write only that content
            - Image/object → simple 1-2 word description

            Just write the content, no explanation."""
        else:
            # 沒有指示詞時，簡潔描述
            prompt = """Briefly describe the main content in this image (max 2 sentences)."""
    else:
        # 中文提示詞
        if deictic_word:
            # 有指示詞時，提取簡潔的內容補充
            prompt = f"""看這張圖片，找出「{deictic_word}」指向的內容。

            如果看到：
            - 公式、算式 → 只寫該部分的數學式
            - 文字、代碼 → 只寫該部分的內容
            - 圖形、物體 → 簡單描述該部分（1-2詞）

            不要解釋，直接寫內容。"""
        else:
            # 沒有指示詞時，簡潔描述
            prompt = """簡潔描述這張圖片的主要內容（不超過2句話）。"""
    
    return prompt
