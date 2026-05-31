"""
融合引擎模塊 - 方案A：簡單替換融合
將指示詞替換為視覺描述
"""
import re
from typing import Dict, List
from pathlib import Path

from config import RESULTS_DIR
from modules.subtitle_converter import SubtitleConverter


class FusionEngine:
    """融合引擎類 - 方案A：簡單替換"""
    
    def __init__(self):
        """初始化融合引擎"""
        print("[FusionEngine] 初始化完成")
    
    def fuse(self, transcript_json: Dict, deictic_data: Dict, vision_data: Dict, 
             recall_data: Dict = None) -> Dict:
        """
        融合邏輯：將指示詞替換為視覺描述 + 將回想詞標注到過去內容
        
        Args:
            transcript_json (dict): 原始逐字稿
            deictic_data (dict): 指示詞數據
            vision_data (dict): 視覺分析數據
            recall_data (dict): 回想內容數據（新增）
                {
                    "total_recalls": 2,
                    "recalls": [
                        {
                            "segment_idx": 15,
                            "recall_word": "as I mentioned",
                            "recall_type": "direct" 或 "contrast",
                            "recalled_segment_idx": 3,
                            "recalled_text": "...",
                            "recalled_time": "[0:00:18]",
                            "similarity_score": 0.82,
                            "contrast_marker": "↔" (optional)
                        }
                    ]
                }
        
        Returns:
            dict: 融合後的逐字稿
        """
        print(f"\n[FusionEngine] 開始融合...")
        print(f"  - 逐字稿段落: {len(transcript_json.get('segments', []))}")
        print(f"  - 指示詞數: {len(deictic_data.get('deictic_words', []))}")
        print(f"  - 視覺描述: {len(vision_data.get('analyses', []))}")
        if recall_data:
            print(f"  - 回想內容: {len(recall_data.get('recalls', []))}")
        
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
                "start": segment.get("start", 0),  # ← 新增：保留原始時間段
                "end": segment.get("end", 0),      # ← 新增：保留原始時間段
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
            "total_replacements": sum(len(s["replacements"]) for s in fused_segments),
            "recalls": []  # ← 新增：保存 recall 數據
        }
        
        # ← 新增：融合回想標注
        if recall_data:
            for recall in recall_data.get("recalls", []):
                segment_idx = recall.get("segment_idx")
                recall_cue = recall.get("recall_cue", "")
                recalled_segment_idx = recall.get("recalled_segment_idx")
                recalled_text = recall.get("recalled_text", "")
                recall_type = recall.get("recall_type", "direct")
                confidence = recall.get("confidence", 0.0)
                
                if segment_idx is not None and 0 <= segment_idx < len(fused_segments):
                    segment = fused_segments[segment_idx]
                    segment["modified"] = True
                    
                    # ← 新增：從 fused_segments 中補充 recalled_time
                    recalled_time = ""
                    if recalled_segment_idx is not None and 0 <= recalled_segment_idx < len(fused_segments):
                        recalled_time = fused_segments[recalled_segment_idx].get("time", "")
                    
                    # 保存 recall 信息到 result
                    result["recalls"].append({
                        "segment_idx": segment_idx,
                        "recall_cue": recall_cue,
                        "recalled_segment_idx": recalled_segment_idx,
                        "recalled_text": recalled_text,
                        "recall_type": recall_type,
                        "confidence": confidence,
                        "reasoning": recall.get("reasoning", ""),
                        "recalled_time": recalled_time  # ← 新增
                    })
            
            result["total_recalls"] = len(recall_data.get("recalls", []))
            print(f"  - 回想標注: {result['total_recalls']} 個")
        
        print(f"\n[FusionEngine] 融合完成:")
        print(f"  - 修改段落: {result['modified_segments']}/{result['total_segments']}")
        print(f"  - 總替換數: {result['total_replacements']}")
        
        # ← 新增：生成字幕
        try:
            subtitle_converter = SubtitleConverter()
            
            # 為 result 添加 fused_text 字段（從 text 複製）
            for seg in result["segments"]:
                if "fused_text" not in seg:
                    seg["fused_text"] = seg["text"]
            
            srt_content = subtitle_converter.fused_json_to_srt(result)
            
            if srt_content:
                # 保存 SRT 檔案
                video_stem = Path(transcript_json["filename"]).stem
                srt_path = RESULTS_DIR / f"{video_stem}.srt"
                subtitle_converter.save_srt(srt_content, srt_path)
                print(f"[FusionEngine] 字幕已生成: {srt_path}")
            else:
                print("[FusionEngine] ⚠️  字幕內容為空，跳過生成")
                
        except Exception as e:
            print(f"[FusionEngine] ⚠️  字幕生成失敗: {e}")
        
        return result
    
    def save_fused_transcript(self, fused_data: Dict, transcript_json: Dict, 
                             recall_data: Dict = None, output_name: str = None) -> Path:
        """
        保存融合後的逐字稿
        
        Args:
            fused_data (dict): 融合結果（包含 recalls）
            transcript_json (dict): 原始逐字稿（含語言和文件名信息）
            recall_data (dict): 回想內容數據（向後兼容，可選）
            output_name (str): 輸出檔名（不含副檔名）
        
        Returns:
            Path: 輸出檔案路徑
        """
        if output_name is None:
            output_name = "fused_transcript"
        
        output_path = RESULTS_DIR / f"{output_name}.txt"
        
        # ← 新增：合併短句子成完整段落
        merged_segments = self._merge_short_segments(fused_data["segments"])
        
        # ← 新增：建立 recall 映射 (segment_idx → recall_list)
        # 並從 segments 中補充 time 信息
        recall_map = {}
        recalls = fused_data.get("recalls", []) or recall_data.get("recalls", []) if recall_data else []
        segments_list = fused_data.get("segments", [])
        
        for recall in recalls:
            segment_idx = recall.get("segment_idx")
            if segment_idx not in recall_map:
                recall_map[segment_idx] = []
            
            # ← 新增：補充被回想的時間
            recalled_segment_idx = recall.get("recalled_segment_idx")
            if recalled_segment_idx is not None and recalled_segment_idx < len(segments_list):
                recall["recalled_time"] = segments_list[recalled_segment_idx].get("time", "")
            
            recall_map[segment_idx].append(recall)
        
        # 輸出為可讀的文本格式
        with open(output_path, 'w', encoding='utf-8') as f:
            # f.write("===== 融合逐字稿 =====\n\n")
            
            # ← 新增：語言過濾 - 只輸出符合目標語言的 segments
            target_language = transcript_json.get("language", "en")
            is_target_english = target_language.startswith("en")
            
            for segment_idx, segment in enumerate(merged_segments):
                text = segment.get('text', '').strip()
                
                # ← 語言過濾：如果目標是英文，移除純中文 segments
                if is_target_english:
                    # 檢查是否包含大量中文字符
                    chinese_count = sum(1 for c in text if ord(c) > 0x4E00 and ord(c) < 0x9FFF)
                    english_count = sum(1 for c in text if c.isalpha())
                    
                    # 如果中文比例 > 50%，跳過此 segment
                    if chinese_count > english_count:
                        continue
                
                # ← 新增：輸出 recall 標注（如果有）
                if segment_idx in recall_map:
                    for recall in recall_map[segment_idx]:
                        recall_time = recall.get("recalled_time", "")
                        recall_text = recall.get("recalled_text", "")[:50]  # 前 50 字
                        confidence = recall.get("confidence", 0)
                        recall_type = recall.get("recall_type", "direct")
                        
                        if recall_type == "contrast":
                            marker = f"[↔ {recall_time} '{recall_text}...' (信心:{confidence:.1%})]"
                        else:
                            marker = f"[↑ {recall_time} '{recall_text}...' (信心:{confidence:.1%})]"
                        
                        f.write(f"{marker}\n")
                
                # 輸出 segment 時間
                f.write(f"{segment['time']}")
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
        import numpy as np
        
        class NumpyEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, np.integer):
                    return int(obj)
                elif isinstance(obj, np.floating):
                    return float(obj)
                return super().default(obj)
        
        if output_name is None:
            output_name = "fused_transcript"
        
        # ← 新增：為每個 recall 添加 recalled_time（被回想的段落時間）
        segments_list = fused_data.get("segments", [])
        recalls_with_time = []
        
        for recall in fused_data.get("recalls", []):
            # 複製 recall 以避免修改原始數據
            recall_copy = recall.copy()
            
            # ← 新增：補充被回想的時間
            recalled_segment_idx = recall.get("recalled_segment_idx")
            if recalled_segment_idx is not None and recalled_segment_idx < len(segments_list):
                recall_copy["recalled_time"] = segments_list[recalled_segment_idx].get("time", "")
            else:
                recall_copy["recalled_time"] = ""
            
            # ← 新增：確保使用新字段名，舊名稱應轉換
            # 如果只有similarity_score沒有confidence，則轉換
            if "confidence" not in recall_copy and "similarity_score" in recall_copy:
                recall_copy["confidence"] = recall_copy.pop("similarity_score")
            
            recalls_with_time.append(recall_copy)
        
        # 更新 fused_data 中的 recalls
        fused_data_to_save = fused_data.copy()
        fused_data_to_save["recalls"] = recalls_with_time
        
        # 添加格式化 recall 文本到每個 segment
        recall_map = {}
        for recall in recalls_with_time:
            segment_idx = recall.get("segment_idx")
            if segment_idx not in recall_map:
                recall_map[segment_idx] = []
            recall_map[segment_idx].append(recall)
        
        for idx, segment in enumerate(fused_data_to_save.get("segments", [])):
            if idx in recall_map:
                recalls_text = []
                for recall in recall_map[idx]:
                    recall_time = recall.get("recalled_time", "")
                    recall_text = recall.get("recalled_text", "")[:50]
                    confidence = recall.get("confidence", 0)
                    recall_type = recall.get("recall_type", "direct")
                    
                    if recall_type == "contrast":
                        formatted = f"[↔ {recall_time} {recall_text}... (信心:{confidence:.1%})]"
                    else:
                        formatted = f"[↑ {recall_time} {recall_text}... (信心:{confidence:.1%})]"
                    
                    recalls_text.append(formatted)
                
                segment["recalls_text"] = " ".join(recalls_text)
        
        output_path = RESULTS_DIR / f"{output_name}.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(fused_data_to_save, f, ensure_ascii=False, indent=2, cls=NumpyEncoder)
        
        print(f"[FusionEngine] 融合數據已保存至: {output_path}")
        
        return output_path
    
    def generate_recall_frames(self, video_path: str, recall_data: Dict, 
                              fused_data: Dict = None) -> Dict:
        """
        為每個 Recall 生成原始截圖和裁切截圖
        
        流程：
          1. 為每個 recall 提取對應時刻的幀（原始截圖）
          2. 使用 ROI 偵測器識別關鍵區域
          3. 裁切關鍵區域（ROI 截圖）
          4. 在 recall 記錄中添加圖片路徑和 ROI 座標
        
        Args:
            video_path (str): 影片路徑
            recall_data (dict): Recall 數據（包含所有回想紀錄）
            fused_data (dict): 融合數據（可選，用於 segment 信息）
        
        Returns:
            dict: 更新後的 recall_data（包含圖片路徑和 ROI 座標）
        """
        from modules.roi_detector import ROIDetector
        from modules.frame_extractor import FrameExtractor
        from config import GEMINI_API_KEY, ROI_VISION_MODEL, USE_ROI_VISION_API
        
        print("\n[FusionEngine] 開始生成 Recall 幀...")
        
        # ← 改：從 config 讀取配置，啟用或禁用 ROI Vision API
        roi_detector = ROIDetector(
            use_vision_api=USE_ROI_VISION_API,
            vision_api_key=GEMINI_API_KEY,
            vision_model=ROI_VISION_MODEL,
            verbose=True
        )
        frame_extractor = FrameExtractor()
        
        # 確保輸出目錄存在
        frames_dir = RESULTS_DIR / "frames"
        frames_dir.mkdir(parents=True, exist_ok=True)
        
        video_name = Path(video_path).stem  # 例如 "video_demo1" 而非 "video_demo1.mp4"
        
        # 獲取 segments list
        segments_list = fused_data.get("segments", []) if fused_data else []
        
        processed_count = 0
        failed_count = 0
        
        for recall in recall_data.get("recalls", []):
            recall_id = recall.get("recall_id", processed_count + failed_count)
            segment_idx = recall.get("segment_idx")
            
            try:
                # Step 1：取得該 Recall 時刻的幀
                segment_time = recall.get("segment_start_seconds")
                
                # ← 新增：從 recall_data 中直接獲得 recalled_end_time
                if "recalled_end_time" in recall:
                    segment_time = recall.get("recalled_end_time")
                elif "recalled_segment_idx" in recall:
                    # 從 segments_list 中計算
                    recalled_segment_idx = recall.get("recalled_segment_idx")
                    if recalled_segment_idx is not None and recalled_segment_idx < len(segments_list):
                        segment_time = segments_list[recalled_segment_idx].get("end", 0)
                elif segment_time is None and segment_idx is not None and segment_idx < len(segments_list):
                    # 備選：如果 recall 中沒有 segment_start_seconds，則嘗試從 segments_list 中獲取 start 時間
                    segment_time = segments_list[segment_idx].get("start", 0)
                
                if segment_time is None:
                    segment_time = 0  # 備選：使用 0 秒
                
                # 原始截圖路徑加上 video_name 前綴
                original_frame_path = frames_dir / f"{video_name}_recall_{recall_id}_original.png"
                
                # Step 2：提取幀
                frame_result = frame_extractor.extract_frame_at_time(
                    video_path,
                    segment_time,
                    str(original_frame_path)
                )
                
                if not frame_result.get("success", True):
                    # 提取失敗
                    time_display = f"[0:{int(segment_time)//60:02d}:{int(segment_time)%60:02d}]"
                    error_msg = frame_result.get('error', '未知錯誤')
                    print(f"  ⚠ {time_display} 『{recall['recall_cue']}』 - 幀提取失敗")
                    print(f"      ✗ {error_msg}")
                    failed_count += 1
                    continue
                
                # Step 3：ROI 偵測 + 裁切 ← 改：加上 video_name 前綴
                cropped_frame_path = frames_dir / f"{video_name}_recall_{recall_id}_cropped.png"
                
                roi_result = roi_detector.detect_and_crop(
                    str(original_frame_path),
                    str(cropped_frame_path),
                    recall_info=recall
                )
                
                # Step 4：更新 Recall 記錄 ← 改：加上 video_name 前綴
                recall["frames"] = {
                    "original": f"frames/{video_name}_recall_{recall_id}_original.png",
                    "cropped": f"frames/{video_name}_recall_{recall_id}_cropped.png"
                }
                
                recall["roi"] = roi_result["roi"]
                
                # 格式化秒數為時間戳顯示 ← 改：加上 video_name 前綴
                time_display = f"[0:{int(segment_time)//60:02d}:{int(segment_time)%60:02d}]"
                original_rel_path = f"frames/{video_name}_recall_{recall_id}_original.png"
                cropped_rel_path = f"frames/{video_name}_recall_{recall_id}_cropped.png"
                print(f"  ✓ [{recall_id}] {time_display} 『{recall['recall_cue']}』")
                print(f"      → 原始: {original_rel_path}")
                print(f"      → 裁切: {cropped_rel_path}")
                processed_count += 1
            
            except Exception as e:
                # 異常時，嘗試從 recall 獲取時間信息
                segment_start_seconds = recall.get('segment_start_seconds', 0)
                time_display = f"[0:{int(segment_start_seconds)//60:02d}:{int(segment_start_seconds)%60:02d}]"
                recall_cue = recall.get('recall_cue', '?')
                error_brief = str(e)[:100]
                print(f"  ✗ {time_display} 『{recall_cue}』 - 處理失敗")
                print(f"      ✗ 錯誤: {error_brief}")
                failed_count += 1
        
        print(f"\n[FusionEngine] Recall 幀生成完成")
        print(f"  ✓ 成功: {processed_count}")
        if failed_count > 0:
            print(f"  ✗ 失敗: {failed_count}")
        print(f"  📁 輸出目錄: {frames_dir.absolute()}")
        
        # 列舉已保存的文件
        if frames_dir.exists():
            saved_files = list(frames_dir.glob("*.png"))
            if saved_files:
                print(f"  📸 已保存 {len(saved_files)} 個截圖文件:")
                for i, file in enumerate(sorted(saved_files), 1):
                    file_size = file.stat().st_size / 1024  # KB
                    print(f"      {i}. {file.name} ({file_size:.1f} KB)")
        
        return recall_data


if __name__ == "__main__":
    print("請使用 tests/test_fusion_engine.py 來測試此模塊")
