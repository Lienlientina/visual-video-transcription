"""
影片截幀模塊 - 使用 ffmpeg 在指定時間戳處截取畫面
"""
import subprocess
import json
from pathlib import Path
from typing import List, Dict
import shutil

from config import FRAMES_DIR
from utils import timestamp_to_seconds


class FrameExtractor:
    """影片截幀類"""
    
    def __init__(self):
        """初始化截幀器，檢查 ffmpeg 是否可用"""
        # 檢查 ffmpeg 是否已安裝
        result = shutil.which("ffmpeg")
        if result is None:
            raise RuntimeError(
                "ffmpeg 未安裝。請執行: choco install ffmpeg (Windows) 或 brew install ffmpeg (Mac) 或 apt install ffmpeg (Linux)"
            )
        print("[FrameExtractor] ffmpeg 檢查完成 ✓")
    
    def extract_frames(self, video_path: str, timestamps: List[str], output_quality: int = 2) -> Dict:
        """
        在指定時間戳處截取影片畫面
        
        Args:
            video_path (str): 影片檔路徑
            timestamps (List[str]): 時間戳列表，例如 ["[0:00:05]", "[0:00:10]"]
            output_quality (int): 圖片質量 (1-5，越高越好，但文件越大)
        
        Returns:
            dict: 
                {
                    "video": "video_demo1.mp4",
                    "total_frames": 2,
                    "frames": [
                        {"timestamp": "[0:00:05]", "path": "outputs/frames/0_00_05.jpg"},
                        {"timestamp": "[0:00:10]", "path": "outputs/frames/0_00_10.jpg"}
                    ]
                }
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"影片檔不存在: {video_path}")
        
        print(f"\n[FrameExtractor] 開始截幀: {video_path.name}")
        print(f"[FrameExtractor] 共需截取 {len(timestamps)} 幀")
        
        results = []
        failed_timestamps = []
        
        for idx, timestamp in enumerate(timestamps, 1):
            try:
                # 轉換時間戳為秒數
                seconds = timestamp_to_seconds(timestamp)
                
                # 生成輸出檔名（不使用 [ ] 字符，改用 _ 分隔）
                # [0:00:05] → 0_00_05.jpg
                filename = timestamp.replace("[", "").replace("]", "").replace(":", "_") + ".jpg"
                output_path = FRAMES_DIR / filename
                
                # 使用 ffmpeg 截幀
                cmd = [
                    "ffmpeg",
                    "-ss", str(seconds),  # 指定時間位置
                    "-i", str(video_path),
                    "-vframes", "1",  # 只提取1幀
                    "-q:v", str(output_quality),  # 圖片質量
                    "-y",  # 覆蓋輸出檔
                    str(output_path)
                ]
                
                # 執行 ffmpeg，隱藏輸出
                subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                results.append({
                    "timestamp": timestamp,
                    "path": str(output_path.relative_to(FRAMES_DIR.parent))
                })
                
                print(f"  [{idx}/{len(timestamps)}] ✓ {timestamp} → {filename}")
                
            except subprocess.CalledProcessError as e:
                print(f"  [{idx}/{len(timestamps)}] ✗ {timestamp} 截幀失敗")
                print(f"      錯誤: {e.stderr}")
                failed_timestamps.append(timestamp)
            except Exception as e:
                print(f"  [{idx}/{len(timestamps)}] ✗ {timestamp} 錯誤: {e}")
                failed_timestamps.append(timestamp)
        
        result = {
            "video": video_path.name,
            "total_frames": len(timestamps),
            "success_frames": len(results),
            "failed_frames": len(failed_timestamps),
            "frames": results
        }
        
        print(f"\n[FrameExtractor] 截幀完成: {len(results)}/{len(timestamps)} 成功")
        if failed_timestamps:
            print(f"[FrameExtractor] 失敗時間戳: {failed_timestamps}")
        
        return result
    
    def extract_frames_from_deictic(self, video_path: str, deictic_data: Dict, output_quality: int = 2) -> Dict:
        """
        根據指示詞偵測結果截幀（只在指示詞出現的時間點截幀）
        
        Args:
            video_path (str): 影片檔路徑
            deictic_data (dict): DeicticDetector 的輸出
                {
                    "deictic_words": [
                        {
                            "word": "這個",
                            "time": "[0:00:05]",
                            "context": "把這個公式代入"
                        },
                        ...
                    ]
                }
            output_quality (int): 圖片質量
        
        Returns:
            dict: 截幀結果（包含指示詞信息）
                {
                    "video": "video_demo1.mp4",
                    "total_deictic_words": 4,
                    "success_frames": 4,
                    "frames": [
                        {
                            "timestamp": "[0:00:05]",
                            "path": "outputs/frames/0_00_05.jpg",
                            "word": "這個",
                            "context": "把這個公式代入"
                        },
                        ...
                    ]
                }
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"影片檔不存在: {video_path}")
        
        deictic_words = deictic_data.get("deictic_words", [])
        
        print(f"\n[FrameExtractor] 開始根據指示詞截幀: {video_path.name}")
        print(f"[FrameExtractor] 共需截取 {len(deictic_words)} 幀（在指示詞位置）")
        
        results = []
        failed_words = []
        skipped_words = []  # ← 新增：記錄跳過的詞
        
        for idx, word_info in enumerate(deictic_words, 1):
            # ← 新增：檢查是否需要視覺分析
            if not word_info.get("need_vision", True):
                skipped_words.append(word_info)
                print(f"  [{idx}/{len(deictic_words)}] ⊘ {word_info['time']} 「{word_info['word']}」跳過（不需要視覺分析）")
                continue
            
            try:
                timestamp = word_info["time"]
                word = word_info["word"]
                context = word_info.get("context", "")
                
                # ← 改進：優先使用精確秒數，否則轉換時間戳
                if "position_in_seconds" in word_info:
                    seconds = word_info["position_in_seconds"]  # 精確秒數
                    print(f"  [{idx}/{len(deictic_words)}] 使用精確秒數: {seconds:.2f}s")
                else:
                    seconds = timestamp_to_seconds(timestamp)  # 回退到 segment 開始時間
                
                # ← 改進：生成更精確的檔名，包含秒數（浮點）
                video_stem = video_path.stem
                time_part = timestamp.replace("[", "").replace("]", "").replace(":", "_")
                
                # 如果有精確秒數，添加到檔名中
                if "position_in_seconds" in word_info:
                    precise_time = f"{seconds:.2f}".replace(".", "_")  # "6.85" → "6_85"
                    filename = f"{video_stem}_{time_part}_precise_{precise_time}.jpg"
                else:
                    filename = f"{video_stem}_{time_part}.jpg"
                
                output_path = FRAMES_DIR / filename
                
                # 使用 ffmpeg 截幀
                cmd = [
                    "ffmpeg",
                    "-ss", str(seconds),
                    "-i", str(video_path),
                    "-vframes", "1",
                    "-q:v", str(output_quality),
                    "-y",
                    str(output_path)
                ]
                
                # 執行 ffmpeg，隱藏輸出
                subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                results.append({
                    "timestamp": timestamp,
                    "precise_seconds": word_info.get("position_in_seconds", seconds),  # ← 新增
                    "path": str(output_path),
                    "word": word,
                    "context": context
                })
                
                print(f"  [{idx}/{len(deictic_words)}] ✓ {timestamp} 「{word}」→ {filename}")
                
            except subprocess.CalledProcessError as e:
                print(f"  [{idx}/{len(deictic_words)}] ✗ {timestamp} 「{word}」截幀失敗")
                failed_words.append(word_info)
            except Exception as e:
                print(f"  [{idx}/{len(deictic_words)}] ✗ {timestamp} 「{word}」錯誤: {e}")
                failed_words.append(word_info)
        
        result = {
            "video": video_path.name,
            "total_deictic_words": len(deictic_words),
            "success_frames": len(results),
            "failed_frames": len(failed_words),
            "skipped_frames": len(skipped_words),  # ← 新增
            "frames": results
        }
        
        print(f"\n[FrameExtractor] 截幀完成: {len(results)} 成功 / {len(skipped_words)} 跳過 / {len(failed_words)} 失敗（共 {len(deictic_words)}）")
        if skipped_words:
            print(f"[FrameExtractor] 跳過指示詞: {[w['word'] for w in skipped_words]}")
        if failed_words:
            print(f"[FrameExtractor] 失敗指示詞: {[w['word'] for w in failed_words]}")
        
        return result
    
        """
        直接從逐字稿 JSON 提取所有段落的開始時間戳處的畫面
        
        Args:
            video_path (str): 影片檔路徑
            transcript_json (dict): 逐字稿字典 (from transcriber.py 輸出)
            output_quality (int): 圖片質量
        
        Returns:
            dict: 截幀結果 + 對應的逐字稿信息
        """
        # 提取所有時間戳
        timestamps = [seg["time"] for seg in transcript_json["segments"]]
        
        # 執行截幀
        frames_result = self.extract_frames(video_path, timestamps, output_quality)
        
        # 將截幀結果與逐字稿段落配對
        frames_with_text = []
        for frame_info in frames_result["frames"]:
            # 找對應的逐字稿段落
            matching_segment = next(
                (seg for seg in transcript_json["segments"] if seg["time"] == frame_info["timestamp"]),
                None
            )
            if matching_segment:
                frames_with_text.append({
                    "timestamp": frame_info["timestamp"],
                    "path": frame_info["path"],
                    "text": matching_segment["text"]
                })
        
        frames_result["frames"] = frames_with_text
        
        return frames_result
    
    def extract_frame_at_time(self, video_path: str, seconds: float, output_path: str, 
                             output_quality: int = 2) -> Dict:
        """
        在指定秒數處截取單個幀
        
        用途：為單個 Recall 或其他目的快速截取一幀
        
        Args:
            video_path (str): 影片檔路徑
            seconds (float): 秒數（例如 45.2）
            output_path (str): 輸出檔案路徑
            output_quality (int): 圖片質量 (1-5，越高越好)
        
        Returns:
            dict:
                {
                    "success": True/False,
                    "seconds": 45.2,
                    "path": "outputs/results/frames/recall_0_original.png",
                    "error": "..."  (if success=False)
                }
        """
        try:
            video_path = Path(video_path)
            output_path = Path(output_path)
            
            if not video_path.exists():
                return {
                    "success": False,
                    "seconds": seconds,
                    "path": str(output_path),
                    "error": f"影片檔不存在: {video_path}"
                }
            
            # 確保輸出目錄存在
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 使用 ffmpeg 截幀
            cmd = [
                "ffmpeg",
                "-ss", str(seconds),
                "-i", str(video_path),
                "-vframes", "1",
                "-q:v", str(output_quality),
                "-y",
                str(output_path)
            ]
            
            # 執行 ffmpeg，隱藏輸出
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                return {
                    "success": False,
                    "seconds": seconds,
                    "path": str(output_path),
                    "error": f"ffmpeg 錯誤: {result.stderr[:100]}"
                }
            
            return {
                "success": True,
                "seconds": seconds,
                "path": str(output_path)
            }
        
        except Exception as e:
            return {
                "success": False,
                "seconds": seconds,
                "path": str(output_path),
                "error": str(e)
            }


if __name__ == "__main__":
    print("請使用 tests/test_frame_extractor.py 來測試此模塊")
