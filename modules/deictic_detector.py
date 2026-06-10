"""
指示詞偵測模塊 - 從逐字稿中找出所有指示詞及其時間戳
"""
import json
from pathlib import Path
from typing import Dict, List

from utils import find_deictic_words, decide_vision_needed


class DeicticDetector:
    """指示詞偵測類"""
    
    def __init__(self):
        """初始化偵測器"""
        print("[DeicticDetector] 初始化完成")
    
    def detect_from_transcript(self, transcript_json: Dict) -> Dict:
        """
        從逐字稿 JSON 中偵測所有指示詞
        
        Args:
            transcript_json (dict): 逐字稿字典，包含 segments
                {
                    "filename": "demo.mp4",
                    "language": "zh",
                    "segments": [
                        {"time": "[0:00:05]", "text": "大家好，今天講這個..."},
                        ...
                    ]
                }
        
        Returns:
            dict: 
                {
                    "total_segments": 5,
                    "segments_with_deictic": 2,
                    "deictic_words": [
                        {
                            "word": "這個",
                            "time": "[0:00:05]",
                            "segment_text": "大家好，今天講這個...",
                            "position_in_segment": 6,
                            "context": "這個藍色的部分",
                            "need_vision": True
                        },
                        ...
                    ]
                }
        """
        print(f"\n[DeicticDetector] 開始偵測指示詞...")
        
        # 獲取語言（預設中文）
        language = transcript_json.get("language", "zh")
        
        deictic_words = []
        segments_with_deictic = set()
        seen_words = set()  # 追蹤已見過的 (timestamp, word) 組合
        
        for segment in transcript_json.get("segments", []):
            timestamp = segment["time"]
            text = segment["text"]
            
            # 偵測此段落中的指示詞
            words_found = find_deictic_words(text, language=language)
            
            for word_info in words_found:
                # 檢查是否已經處理過這個詞
                word_key = (timestamp, word_info["word"], word_info["pos"])
                if word_key in seen_words:
                    print(f"[DeicticDetector] 跳過重複: {timestamp} 「{word_info['word']}」")
                    continue
                seen_words.add(word_key)
                
                # 提取上下文
                context = self._extract_context(text, word_info["pos"], word_info["end"])
                context_before = text[max(0, word_info["pos"]-20):word_info["pos"]]
                context_after = text[word_info["end"]:min(len(text), word_info["end"]+20)]
                
                # 判斷是否需要視覺分析（三層法）
                need_vision = decide_vision_needed(
                    word_info["word"],
                    context_before,
                    context_after,
                    language=language
                )
                
                deictic_words.append({
                    "word": word_info["word"],
                    "time": timestamp,  # 保留原始 segment 時間（用於後向相容）
                    "start_seconds": segment.get("start", 0.0),  # ← 新增：segment 開始秒數
                    "end_seconds": segment.get("end", 0.0),      # ← 新增：segment 結束秒數
                    "position_in_segment": word_info["pos"],
                    "position_in_seconds": self._calculate_precise_time(  # ← 新增：精確秒數
                        segment.get("start", 0.0),
                        segment.get("end", 0.0),
                        word_info["pos"],
                        len(text)
                    ),
                    "segment_text": text,
                    "context": context,
                    "need_vision": need_vision
                })
                segments_with_deictic.add(timestamp)
        
        result = {
            "total_segments": len(transcript_json.get("segments", [])),
            "segments_with_deictic": len(segments_with_deictic),
            "total_deictic_words": len(deictic_words),
            "deictic_words": deictic_words
        }
        
        print(f"[DeicticDetector] 偵測完成:")
        print(f"  - 總段落數: {result['total_segments']}")
        print(f"  - 包含指示詞的段落: {result['segments_with_deictic']}")
        print(f"  - 總指示詞數: {result['total_deictic_words']}")
        
        return result
    
    def _extract_context(self, text: str, pos: int, end: int, context_length: int = 15) -> str:
        """
        提取指示詞前後的上下文
        
        Args:
            text (str): 完整文本
            pos (int): 指示詞開始位置
            end (int): 指示詞結束位置
            context_length (int): 前後各提取的字符數
        
        Returns:
            str: 包含指示詞的上下文，例如「這個藍色的部分」
        """
        start = max(0, pos - context_length)
        end_pos = min(len(text), end + context_length)
        context = text[start:end_pos].strip()
        return context
    
    def _calculate_precise_time(self, segment_start: float, segment_end: float, 
                                 position: int, text_length: int) -> float:
        """
        根據指示詞在 segment 中的相對位置計算精確秒數
        
        Args:
            segment_start (float): segment 開始秒數
            segment_end (float): segment 結束秒數
            position (int): 指示詞的字符位置（0-based）
            text_length (int): segment 文本長度
        
        Returns:
            float: 精確秒數
            
        例子：
            segment_start=5.0, segment_end=8.0, position=12, text_length=20
            → 5.0 + (12/20) * (8.0-5.0) = 5.0 + 0.6 * 3.0 = 6.8 秒
        """
        if text_length == 0:
            return segment_start
        
        # 計算指示詞在 segment 中的相對位置（0-1）
        relative_position = position / text_length
        
        # 計算精確秒數
        segment_duration = segment_end - segment_start
        precise_seconds = segment_start + (relative_position * segment_duration)
        
        return precise_seconds


if __name__ == "__main__":
    print("請使用 tests/test_deictic_detector.py 來測試此模塊")
