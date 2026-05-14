"""
融合引擎模塊 - 方案A：簡單替換融合
將指示詞替換為視覺描述
"""
import re
from typing import Dict, List
from pathlib import Path

from config import RESULTS_DIR


class FusionEngine:
    """融合引擎類 - 方案A：簡單替換"""
    
    def __init__(self):
        """初始化融合引擎"""
        print("[FusionEngine] 初始化完成（方案A：簡單替換）")
    
    def fuse(self, transcript_json: Dict, deictic_data: Dict, vision_data: Dict) -> Dict:
        """
        融合邏輯：將指示詞替換為視覺描述
        
        Args:
            transcript_json (dict): 原始逐字稿
                {
                    "segments": [
                        {"time": "[0:00:05]", "text": "把這個公式代入..."},
                        ...
                    ]
                }
            
            deictic_data (dict): 指示詞數據
                {
                    "deictic_words": [
                        {
                            "word": "這個",
                            "time": "[0:00:05]",
                            "segment_text": "把這個公式代入",
                            "position_in_segment": 2,
                            "context": "把這個公式代入"
                        },
                        ...
                    ]
                }
            
            vision_data (dict): 視覺分析數據
                {
                    "analyses": [
                        {
                            "image_path": "outputs/frames/0_00_05.jpg",
                            "description": "白板上有微分公式...",
                            "success": True
                        },
                        ...
                    ]
                }
        
        Returns:
            dict: 融合後的逐字稿
                {
                    "segments": [
                        {
                            "time": "[0:00:05]",
                            "text": "把〔畫面：白板上有微分公式...〕代入...",
                            "original_text": "把這個公式代入...",
                            "replacements": [
                                {"word": "這個", "description": "白板上有微分公式..."}
                            ]
                        },
                        ...
                    ]
                }
        """
        print(f"\n[FusionEngine] 開始融合...")
        print(f"  - 逐字稿段落: {len(transcript_json.get('segments', []))}")
        print(f"  - 指示詞數: {len(deictic_data.get('deictic_words', []))}")
        print(f"  - 視覺描述: {len(vision_data.get('analyses', []))}")
        
        # 建立時間戳 → 視覺描述的映射
        vision_map = {}
        for analysis in vision_data.get("analyses", []):
            if analysis.get("success"):
                # 從圖片名稱推斷時間戳
                # 例如 outputs/frames/0_00_05.jpg → [0:00:05]
                image_name = Path(analysis["image_path"]).stem
                timestamp = self._filename_to_timestamp(image_name)
                vision_map[timestamp] = analysis["description"]
        
        # 融合邏輯：逐段落替換指示詞
        fused_segments = []
        
        for segment in transcript_json.get("segments", []):
            segment_time = segment["time"]
            original_text = segment["text"]
            fused_text = original_text
            replacements = []
            
            # 找出此段落中的指示詞
            matching_deictic_words = [
                d for d in deictic_data.get("deictic_words", [])
                if d["time"] == segment_time
            ]
            
            # 逆序排列（從後往前替換，避免位置偏移）
            matching_deictic_words.sort(key=lambda x: x["position_in_segment"], reverse=True)
            
            for deictic_word in matching_deictic_words:
                word = deictic_word["word"]
                pos = deictic_word["position_in_segment"]
                end = deictic_word.get("position_in_segment") + len(word)
                
                # 查找視覺描述
                description = vision_map.get(segment_time, "")
                
                if description:
                    # 替換為「〔畫面：描述〕」格式
                    replacement_text = f"〔畫面：{description}〕"
                    fused_text = fused_text[:pos] + replacement_text + fused_text[end:]
                    
                    replacements.append({
                        "word": word,
                        "position": pos,
                        "description": description
                    })
            
            fused_segments.append({
                "time": segment_time,
                "text": fused_text,
                "original_text": original_text,
                "replacements": replacements,
                "modified": len(replacements) > 0
            })
        
        result = {
            "segments": fused_segments,
            "total_segments": len(fused_segments),
            "modified_segments": sum(1 for s in fused_segments if s["modified"]),
            "total_replacements": sum(len(s["replacements"]) for s in fused_segments)
        }
        
        print(f"\n[FusionEngine] 融合完成:")
        print(f"  - 修改段落: {result['modified_segments']}/{result['total_segments']}")
        print(f"  - 總替換數: {result['total_replacements']}")
        
        return result
    
    def _filename_to_timestamp(self, filename: str) -> str:
        """
        從檔名轉換回時間戳
        例如 0_00_05 → [0:00:05]
        
        Args:
            filename (str): 檔名（不含副檔名）
        
        Returns:
            str: 時間戳，例如 [0:00:05]
        """
        parts = filename.split("_")
        if len(parts) >= 3:
            return f"[{parts[0]}:{parts[1]}:{parts[2]}]"
        return ""
    
    def save_fused_transcript(self, fused_data: Dict, output_name: str = None) -> Path:
        """
        保存融合後的逐字稿
        
        Args:
            fused_data (dict): 融合結果
            output_name (str): 輸出檔名（不含副檔名）
        
        Returns:
            Path: 輸出檔案路徑
        """
        if output_name is None:
            output_name = "fused_transcript"
        
        output_path = RESULTS_DIR / f"{output_name}.txt"
        
        # 輸出為可讀的文本格式
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("===== 融合逐字稿 =====\n\n")
            
            for segment in fused_data["segments"]:
                f.write(f"{segment['time']} {segment['text']}\n")
                
                if segment["replacements"]:
                    for replacement in segment["replacements"]:
                        f.write(f"  [替換] 「{replacement['word']}」→ 「{replacement['description']}」\n")
                
                f.write("\n")
        
        print(f"[FusionEngine] 融合逐字稿已保存至: {output_path}")
        
        return output_path
    
    def export_as_json(self, fused_data: Dict, output_name: str = None) -> Path:
        """
        以 JSON 格式導出融合數據
        
        Args:
            fused_data (dict): 融合結果
            output_name (str): 輸出檔名
        
        Returns:
            Path: 輸出檔案路徑
        """
        import json
        
        if output_name is None:
            output_name = "fused_transcript"
        
        output_path = RESULTS_DIR / f"{output_name}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(fused_data, f, ensure_ascii=False, indent=2)
        
        print(f"[FusionEngine] 融合數據已保存至: {output_path}")
        
        return output_path


if __name__ == "__main__":
    print("請使用 tests/test_fusion_engine.py 來測試此模塊")
