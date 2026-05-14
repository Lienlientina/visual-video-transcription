"""
指示詞偵測模塊 - 從逐字稿中找出所有指示詞及其時間戳
"""
import json
from pathlib import Path
from typing import Dict, List

from utils import find_deictic_words


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
                            "context": "這個藍色的部分"
                        },
                        ...
                    ]
                }
        """
        print(f"\n[DeicticDetector] 開始偵測指示詞...")
        
        deictic_words = []
        segments_with_deictic = set()
        
        for segment in transcript_json.get("segments", []):
            timestamp = segment["time"]
            text = segment["text"]
            
            # 偵測此段落中的指示詞
            words_found = find_deictic_words(text)
            
            for word_info in words_found:
                deictic_words.append({
                    "word": word_info["word"],
                    "time": timestamp,
                    "segment_text": text,
                    "position_in_segment": word_info["pos"],
                    "context": self._extract_context(text, word_info["pos"], word_info["end"])
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
    
    def filter_by_time(self, deictic_data: Dict, time_ranges: List[tuple] = None) -> Dict:
        """
        根據時間範圍篩選指示詞
        
        Args:
            deictic_data (dict): 偵測結果
            time_ranges (List[tuple], optional): 時間範圍列表，例如 [("0:00:00", "0:00:30"), ...]
        
        Returns:
            dict: 篩選後的結果
        """
        if time_ranges is None:
            return deictic_data
        
        filtered_words = []
        for word_info in deictic_data["deictic_words"]:
            time_str = word_info["time"]
            # 簡單比較 (實際應該轉為秒數)
            for time_range in time_ranges:
                if time_range[0] <= time_str <= time_range[1]:
                    filtered_words.append(word_info)
                    break
        
        return {
            "total_deictic_words": len(filtered_words),
            "deictic_words": filtered_words
        }


if __name__ == "__main__":
    print("請使用 tests/test_deictic_detector.py 來測試此模塊")
