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
        
        for idx, word_info in enumerate(deictic_words, 1):
            try:
                timestamp = word_info["time"]
                word = word_info["word"]
                context = word_info.get("context", "")
                
                # 轉換時間戳為秒數
                seconds = timestamp_to_seconds(timestamp)
                
                # 生成輸出檔名
                filename = timestamp.replace("[", "").replace("]", "").replace(":", "_") + ".jpg"
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
                    "path": str(output_path),  # 改為絕對路徑
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
            "frames": results
        }
        
        print(f"\n[FrameExtractor] 截幀完成: {len(results)}/{len(deictic_words)} 成功")
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


if __name__ == "__main__":
    print("請使用 tests/test_frame_extractor.py 來測試此模塊")
