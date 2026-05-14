"""
通用工具函數 - 時間轉換、指示詞偵測等
"""
import re
from config import DEICTIC_WORDS, TIMESTAMP_FORMAT


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


def find_deictic_words(text):
    """
    在文本中找出所有指示詞及其位置
    
    Args:
        text (str): 文本內容
    
    Returns:
        list: [{"word": "這個", "pos": 5, "index": 0}, ...]
    
    Examples:
        >>> find_deictic_words("把這個公式代入那個方程式")
        [{'word': '這個', 'pos': 2}, {'word': '那個', 'pos': 8}]
    """
    results = []
    
    # 構建正則模式 - 匹配任何指示詞
    pattern = '|'.join(re.escape(word) for word in DEICTIC_WORDS)
    
    for match in re.finditer(pattern, text):
        results.append({
            'word': match.group(),
            'pos': match.start(),
            'end': match.end()
        })
    
    return results


def build_prompt_for_vision(image_path, context="", deictic_word=""):
    """
    為 LLaVA 構建圖片理解提示詞
    
    Args:
        image_path (str): 圖片路徑
        context (str): 額外上下文，例如前後的文字內容
        deictic_word (str): 指示詞，例如「這個」、「藍色的部分」
    
    Returns:
        str: 提示詞內容
    """
    if deictic_word:
        # 有指示詞時，只關注指示詞相關的部分
        prompt = f"""請只描述圖片中和「{deictic_word}」相關的部分。

要求：
1. 簡潔明了 - 2-3句話就夠
2. 只說「{deictic_word}」指的是什麼
3. 包含：顏色、位置、內容
4. 不要描述其他無關部分

例如如果「{deictic_word}」是「藍色的框」，就只說「藍色框內有什麼」

上下文：{context if context else '無'}

請用簡潔的中文回答。"""
    else:
        # 沒有指示詞時，全面描述
        prompt = f"""請詳細分析這張圖片。特別要提到：

1. 【文字和公式】任何可見的文字、算式、公式、代碼
2. 【顏色和標示】顏色、高亮、箭頭指向等強調
3. 【位置和布局】元素的位置（上/下/左/右/中間）
4. 【對象和內容】圖表、圖形、圖片、圖示的具體內容

上下文（逐字稿）：{context if context else '無'}

請用簡明的中文，逐一列出圖片中的關鍵內容。"""
    
    return prompt


def build_prompt_for_fusion(original_text, visual_descriptions):
    """
    為文本融合模型構建提示詞
    
    Args:
        original_text (str): 原始逐字稿，例如 "把這個公式代入"
        visual_descriptions (list): 視覺描述列表，例如 [{"word": "這個", "desc": "..."}]
    
    Returns:
        str: 融合提示詞
    """
    descriptions_str = "\n".join([
        f"- '{item['word']}' 指的是：{item['desc']}"
        for item in visual_descriptions
    ])
    
    prompt = f"""請根據視覺描述，將原始逐字稿中的指示詞替換為具體內容。

原始文本：
{original_text}

視覺描述：
{descriptions_str}

要求：
1. 替換指示詞，使用「〔畫面：視覺描述〕」的格式
2. 保持原文的流暢性和時間戳
3. 用中文回答

融合後的文本："""
    
    return prompt


# 測試用
if __name__ == "__main__":
    # 測試時間轉換
    print(seconds_to_timestamp(23))
    print(seconds_to_timestamp(125))
    print(timestamp_to_seconds("[0:02:05]"))
    
    # 測試指示詞檢測
    text = "把這個公式代入那個方程式，然後點擊這裡的按鈕"
    print(find_deictic_words(text))
