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
        
        # 建立時間戳 → 視覺描述的映射（直接用 timestamp，不依賴檔名）
        vision_map = {}
        for analysis in vision_data.get("analyses", []):
            if analysis.get("success"):
                timestamp = analysis.get("timestamp")  # ← 直接取得時間戳
                if timestamp:
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
                
                # ← 新增：檢查是否需要視覺分析
                if not deictic_word.get("need_vision", True):
                    continue
                
                # 查找視覺描述
                description = vision_map.get(segment_time, "")
                
                if description:
                    # ← 改動：在指示詞後面插入括號補充，而非替換
                    # 例如：「這個藍色部分」→ 「這個藍色部分(sin(x^2))」
                    supplement_text = f"[{description}]"
                    fused_text = fused_text[:end] + supplement_text + fused_text[end:]
                    
                    replacements.append({
                        "word": word,
                        "position": pos,
                        "supplement": description  # ← 改名：補充而非描述
                    })
            
            fused_segments.append({
                "time": segment_time,  # 保留原始 segment 時間
                "text": fused_text,
                "original_text": original_text,
                "replacements": replacements,
                "modified": len(replacements) > 0,
                "precise_times": [  # ← 新增：記錄此段落中所有指示詞的精確秒數
                    {
                        "word": d["word"],
                        "precise_seconds": d.get("position_in_seconds", d.get("start_seconds", 0.0))
                    }
                    for d in matching_deictic_words if d.get("need_vision", True)
                ]
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
        
        # ← 新增：合併短句子成完整段落
        merged_segments = self._merge_short_segments(fused_data["segments"])
        
        # 輸出為可讀的文本格式
        with open(output_path, 'w', encoding='utf-8') as f:
            # f.write("===== 融合逐字稿 =====\n\n")
            
            for segment in merged_segments:
                # 輸出 segment 時間
                f.write(f"{segment['time']}")
                
                
                # # ← 改進：如果有精確秒數或視覺補充，顯示詳情
                # metadata = []
                # if segment.get("precise_times"):
                #     precise_info = ", ".join([
                #         f"{item['word']}@{item['precise_seconds']:.2f}s"
                #         for item in segment["precise_times"][:3]
                #     ])
                #     metadata.append(f"精確: {precise_info}")
                
                # # ← 新增：顯示視覺補充信息
                # if segment.get("replacements"):
                #     replacement_info = ", ".join([
                #         f"{r['word']}→視覺"
                #         for r in segment["replacements"][:2]
                #     ])
                #     metadata.append(f"補充: {replacement_info}")
                
                # if metadata:
                #     f.write(f" [{', '.join(metadata)}]")
                
                f.write(f"\n{segment['text']}\n\n")
        
        print(f"[FusionEngine] 融合逐字稿已保存至: {output_path}")
        
        return output_path
    
    def _merge_short_segments(self, segments: list, min_length: int = 50) -> list:
        """
        合併短句子成完整段落（避免文字碎片化）
        
        Args:
            segments (list): 原始 segments
            min_length (int): 最小段落長度，低於此值會與下一個合併
        
        Returns:
            list: 合併後的 segments
        """
        if not segments:
            return []
        
        merged = []
        current_segment = None
        
        for segment in segments:
            text = segment.get("text", "").strip()
            
            # 如果當前文本為空或只有標點符號，跳過
            if not text or len(text) < 2:
                continue
            
            # 如果是第一個 segment 或前一個已經夠長，開始新段落
            if current_segment is None or len(current_segment.get("text", "")) >= min_length:
                current_segment = segment.copy()
                merged.append(current_segment)
            else:
                # 合併到前一個 segment
                current_segment["text"] += " " + text
                
                # ← 新增：合併 replacements（保留視覺補充信息）
                if segment.get("replacements"):
                    current_segment.setdefault("replacements", []).extend(segment["replacements"])
                
                # 合併 precise_times（精確秒數）
                if segment.get("precise_times"):
                    current_segment.setdefault("precise_times", []).extend(segment["precise_times"])
                
                # 標記為已修改
                current_segment["modified"] = current_segment["modified"] or segment.get("modified", False)
        
        return merged
    
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
