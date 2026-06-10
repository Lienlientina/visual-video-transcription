"""
最終 JSON 生成模塊 - 從 fusion.json 提取數據用於播放器
Purpose: 為 web/player.html 提供標準化的 JSON 格式
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class FinalJsonGenerator:
    """
    最終 JSON 生成器類
    
    功能：
    - 讀取 fusion.json
    - 提取 segments 和 recalls 部分
    - 驗證必要字段
    - 調整路徑為相對路徑
    - 寫出 final.json
    """
    
    def __init__(self, verbose: bool = True):
        """
        初始化最終 JSON 生成器
        
        Args:
            verbose (bool): 是否輸出詳細日誌
        """
        self.verbose = verbose
        if self.verbose:
            print("[FinalJsonGenerator] 初始化完成")
    
    def generate(self, 
                video_name: str,
                fusion_json_path: str,
                video_path: str,
                output_dir: str = None) -> Optional[Path]:
        """
        從 fusion.json 生成 final.json
        
        Args:
            video_name (str): 視頻名稱（不含副檔名）
            fusion_json_path (str): fusion.json 的路徑
            video_path (str): 原始影片路徑
            output_dir (str): 輸出目錄（預設為 outputs/results）
        
        Returns:
            Path: 生成的 final.json 路徑，失敗時返回 None
        
        Example:
            generator = FinalJsonGenerator()
            final_path = generator.generate(
                video_name="demo_video",
                fusion_json_path="outputs/results/demo_video_fusion.json",
                video_path="videos/demo_video.mp4",
                output_dir="outputs/results"
            )
        """
        from config import RESULTS_DIR
        
        fusion_json_path = Path(fusion_json_path)
        if not fusion_json_path.exists():
            print(f"✗ [FinalJsonGenerator] fusion.json 不存在: {fusion_json_path}")
            return None
        
        if output_dir is None:
            output_dir = RESULTS_DIR
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Step 1: 讀取 fusion.json
            with open(fusion_json_path, 'r', encoding='utf-8') as f:
                fusion_data = json.load(f)
            
            if self.verbose:
                print(f"\n[FinalJsonGenerator] 開始生成 final.json...")
                print(f"  - 來源: {fusion_json_path.name}")
            
            # Step 2: 構建 final.json 結構
            final_data = self._build_final_json(
                video_name=video_name,
                fusion_data=fusion_data,
                video_path=video_path
            )
            
            # Step 3: 驗證和清理
            final_data = self._validate_and_clean(final_data)
            
            # Step 4: 寫出 final.json
            output_path = output_dir / f"{video_name}_final.json"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(final_data, f, ensure_ascii=False, indent=2)
            
            if self.verbose:
                print(f"\n[FinalJsonGenerator] final.json 已生成")
                print(f"  ✓ 輸出路徑: {output_path}")
                print(f"  - 總段落: {len(final_data.get('segments', []))}")
                print(f"  - 回想數: {len(final_data.get('recalls', []))}")
            
            return output_path
        
        except Exception as e:
            print(f"✗ [FinalJsonGenerator] 生成失敗: {e}")
            return None
    
    def _build_final_json(self, video_name: str, fusion_data: Dict, 
                         video_path: str) -> Dict:
        """
        構建最終 JSON 結構
        
        Args:
            video_name (str): 視頻名稱
            fusion_data (dict): fusion.json 的數據
            video_path (str): 原始影片路徑
        
        Returns:
            dict: final.json 的結構
        """
        # 提取 segments
        segments = fusion_data.get("segments", [])
        
        # 簡化 segments 格式（只保留播放器需要的字段）
        simplified_segments = []
        for seg in segments:
            simplified_segments.append({
                "segment_idx": len(simplified_segments),
                "start": seg.get("start", 0.0),
                "end": seg.get("end", 0.0),
                "text": seg.get("text", ""),
                "time": seg.get("time", "")
            })
        
        # 提取並處理 recalls
        recalls = fusion_data.get("recalls", [])
        processed_recalls = []
        
        for idx, recall in enumerate(recalls):
            processed_recall = self._process_recall(recall, idx, fusion_data)
            if processed_recall:
                processed_recalls.append(processed_recall)
        
        # 計算影片路徑和字幕路徑（相對於 final.json 的位置）
        video_rel_path = self._compute_relative_path(video_path)
        subtitle_path = self._compute_subtitle_path(video_path)
        
        # 構建最終結構
        final_json = {
            # 元數據
            "video_name": video_name,
            "video_path": video_rel_path,
            "subtitle_path": subtitle_path,
            
            # 統計
            "total_segments": len(simplified_segments),
            "total_recalls": len(processed_recalls),
            
            # 內容
            "segments": simplified_segments,
            "recalls": processed_recalls
        }
        
        return final_json
    
    def _process_recall(self, recall: Dict, idx: int, fusion_data: Dict) -> Optional[Dict]:
        """
        處理單個 recall，確保必要字段存在
        
        Args:
            recall (dict): recall 數據
            idx (int): recall 索引
            fusion_data (dict): 完整的 fusion 數據（用於補充信息）
        
        Returns:
            dict: 處理後的 recall，或 None（如果字段不完整）
        """
        # 必要字段檢查
        required_fields = ["recall_type", "segment_idx", "confidence"]
        
        # 驗證必要字段
        for field in required_fields:
            if field not in recall:
                if self.verbose:
                    print(f"⚠ [FinalJsonGenerator] recall #{idx} 缺少必要字段: {field}")
                return None
        
        # 取得 recall_cue 或使用備選
        recall_cue = recall.get("recall_cue", "")
        
        # 取得 recalled_text 或使用備選
        recalled_text = recall.get("recalled_text", "")
        if not recalled_text and "recalled_segment_idx" in recall:
            # 嘗試從 segments 中補充
            recalled_segment_idx = recall.get("recalled_segment_idx")
            segments_list = fusion_data.get("segments", [])
            if recalled_segment_idx is not None and recalled_segment_idx < len(segments_list):
                recalled_text = segments_list[recalled_segment_idx].get("text", "")
        
        # 計算 precise_time_seconds（播放器同步關鍵）
        precise_time_seconds = self._get_precise_time(recall, fusion_data)
        
        # 處理圖片路徑
        frame_info = self._process_frame_paths(recall)
        
        # 計算被回想 segment 的起始秒數（供 player 點擊跳轉用）
        recalled_start_seconds = 0.0
        recalled_segment_idx = recall.get("recalled_segment_idx")
        segments_list = fusion_data.get("segments", [])
        if recalled_segment_idx is not None and recalled_segment_idx < len(segments_list):
            recalled_start_seconds = segments_list[recalled_segment_idx].get("start", 0.0)

        # 構建處理後的 recall
        processed_recall = {
            "segment_idx": recall.get("segment_idx"),
            "precise_time_seconds": precise_time_seconds,
            "recalled_start_seconds": recalled_start_seconds,
            "recall_cue": recall_cue,
            "recalled_concept": recall.get("recalled_concept", ""),
            "recalled_text": recalled_text,
            "recall_type": recall.get("recall_type", "direct"),
            "confidence": recall.get("confidence", 0.0),
            "frame_original": frame_info.get("frame_original", ""),
            "frame_cropped": frame_info.get("frame_cropped", "")
        }
        
        return processed_recall
    
    def _get_precise_time(self, recall: Dict, fusion_data: Dict) -> float:
        """
        計算 recall 的精確時刻（秒數）
        用於 player.html 的時間同步
        
        重要：這是「回想發生的時刻」，NOT「被回想內容的時刻」
        
        優先級：
        1. recall["segment_start_seconds"] （若存在）
        2. 從 segment_idx 計算
        
        Args:
            recall (dict): recall 數據
            fusion_data (dict): 完整的 fusion 數據
        
        Returns:
            float: 精確時刻（秒數）
        """
        # 優先級 1: segment_start_seconds（若存在）
        if "segment_start_seconds" in recall:
            return recall.get("segment_start_seconds", 0.0)
        
        # 優先級 2: 從 segment_idx 計算（回想發生的地點）
        segment_idx = recall.get("segment_idx")
        segments_list = fusion_data.get("segments", [])
        
        if segment_idx is not None and segment_idx < len(segments_list):
            segment = segments_list[segment_idx]
            # 使用該 segment 的 start 時間
            return segment.get("start", 0.0)
        
        # 備選：返回 0
        return 0.0
    
    def _process_frame_paths(self, recall: Dict) -> Dict:
        """
        處理圖片路徑（確保存在並且格式正確）
        轉換為相對於 web/player.html 的路徑
        
        Args:
            recall (dict): recall 數據
        
        Returns:
            dict: {"frame_original": "../../outputs/results/frames/...", ...}
        """
        frame_original = ""
        frame_cropped = ""
        
        # 新格式: recall.frames.original / recall.frames.cropped
        if "frames" in recall and isinstance(recall["frames"], dict):
            frame_original = recall["frames"].get("original", "")
            frame_cropped = recall["frames"].get("cropped", "")
        # 舊格式: recall.frame_original / recall.frame_cropped
        elif "frame_original" in recall:
            frame_original = recall.get("frame_original", "")
            frame_cropped = recall.get("frame_cropped", "")
        
        # 轉換為相對於 player.html 的路徑
        # frames/ → ../../outputs/results/frames/
        if frame_original and not frame_original.startswith(".."):
            frame_original = "../../outputs/results/" + frame_original
        if frame_cropped and not frame_cropped.startswith(".."):
            frame_cropped = "../../outputs/results/" + frame_cropped
        
        return {
            "frame_original": frame_original,
            "frame_cropped": frame_cropped
        }
    
    def _compute_relative_path(self, absolute_path: str) -> str:
        """
        將路徑轉換為相對於 player.html 的相對路徑
        player.html 在 web/ 目錄
        
        Args:
            absolute_path (str): 路徑（如 "demo_video/video.mp4" 或絕對路徑）
        
        Returns:
            str: 相對於 web/player.html 的相對路徑（如 "../demo_video/video.mp4"）
        """
        try:
            path = Path(absolute_path)
            
            # 移除驅動符（Windows）
            if path.drive:
                path = Path(*path.parts[1:])
            
            # 如果是絕對路徑，轉為相對於根目錄
            if path.is_absolute():
                path = Path(*path.parts[1:]) if len(path.parts) > 1 else path
            
            # 現在計算相對路徑：從 web/ → .. → 根 → target
            # 簡單方式：在路徑前面加上 "../"
            return "../" + str(path).replace("\\", "/")
        
        except Exception as e:
            if self.verbose:
                print(f"⚠ [FinalJsonGenerator] 計算相對路徑失敗: {e}")
            return absolute_path
    
    def _compute_subtitle_path(self, video_path: str) -> str:
        """
        計算字幕檔案路徑
        字幕在 outputs/results/ 目錄，返回相對於 player.html 的路徑
        
        Args:
            video_path (str): 影片路徑
        
        Returns:
            str: 字幕檔案的相對路徑（相對於 web/player.html）
        """
        try:
            from config import RESULTS_DIR
            
            video_stem = Path(video_path).stem
            srt_file = RESULTS_DIR / f"{video_stem}.srt"
            
            # 計算相對於 web/player.html 的路徑
            # outputs/results/ 相對於 web/ 是 ../outputs/results/
            if srt_file.exists():
                return f"../outputs/results/{video_stem}.srt"
            else:
                return ""
        
        except Exception as e:
            if self.verbose:
                print(f"⚠ [FinalJsonGenerator] 計算字幕路徑失敗: {e}")
            return ""
    
    def _validate_and_clean(self, final_data: Dict) -> Dict:
        """
        驗證和清理 final.json 數據
        
        Args:
            final_data (dict): final.json 數據
        
        Returns:
            dict: 清理後的數據
        """
        # 保留所有 recalls（即使沒有圖片）
        # 因為回想本身就是有價值的信息，可以在播放器中显示為文本
        valid_recalls = []
        recalls_without_images = 0
        
        for recall in final_data.get("recalls", []):
            # 檢查是否有最基本的字段
            if recall.get("recall_type") and recall.get("confidence") is not None:
                valid_recalls.append(recall)
                
                # 統計沒有圖片的 recalls
                if not (recall.get("frame_cropped") or recall.get("frame_original")):
                    recalls_without_images += 1
        
        final_data["recalls"] = valid_recalls
        final_data["total_recalls"] = len(valid_recalls)
        
        if self.verbose and recalls_without_images > 0:
            print(f"⚠ [FinalJsonGenerator] {recalls_without_images} 個 recalls 無圖片，將以文字顯示")
        
        return final_data
