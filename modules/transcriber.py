"""
語音轉逐字稿模塊 - 使用 faster-whisper
輸出帶時間戳的逐字稿
"""
import json
from pathlib import Path
from typing import List, Dict
import warnings

try:
    from faster_whisper import WhisperModel
except ImportError:
    raise ImportError("faster-whisper 未安裝，請執行: pip install faster-whisper")

from config import WHISPER_MODEL, DEVICE, TRANSCRIPTS_DIR
from utils import seconds_to_timestamp


class Transcriber:
    """語音轉逐字稿類"""
    
    def __init__(self, model_size: str = WHISPER_MODEL, device: str = DEVICE):
        """
        初始化轉錄器
        
        Args:
            model_size: whisper 模型大小 (tiny, base, small, medium, large)
            device: 運行設備 (cpu, cuda, auto)
        """
        self.model_size = model_size
        self.device = device
        
        print(f"[Transcriber] 正在加載 faster-whisper {model_size} 模型...")
        print(f"[Transcriber] 使用設備: {device}")
        
        # 忽略不必要的警告
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type="int8" if device == "cpu" else "float16"
            )
        
        print("[Transcriber] 模型加載完成")
    
    def transcribe(self, video_path: str, language: str = "zh") -> Dict:
        """
        將影片轉錄為逐字稿
        
        Args:
            video_path: 影片檔路徑
            language: 語言代碼，預設中文 "zh"
        
        Returns:
            dict: 包含segments的字典
                {
                    "segments": [
                        {"time": "[0:00:05]", "text": "大家好"},
                        ...
                    ],
                    "language": "zh"
                }
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"影片檔不存在: {video_path}")
        
        print(f"\n[Transcriber] 開始轉錄: {video_path.name}")
        
        # 使用 faster-whisper 轉錄
        segments, info = self.model.transcribe(
            str(video_path),
            language=language,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500)
        )
        
        # 將 segments 轉換為列表並格式化
        result_segments = []
        for segment in segments:
            # segment 有 start, end, text 屬性
            timestamp = seconds_to_timestamp(segment.start)
            result_segments.append({
                "time": timestamp,
                "text": segment.text.strip(),
                "start": segment.start,
                "end": segment.end
            })
        
        result = {
            "filename": video_path.name,
            "language": info.language,
            "segments": result_segments
        }
        
        # ← 新增：根據實際文本內容修正語言判斷
        detected_language = self._detect_content_language(result_segments)
        if detected_language != info.language:
            print(f"[Transcriber] ⚠️  語言修正: {info.language} → {detected_language}")
            result["language"] = detected_language
        
        print(f"[Transcriber] 轉錄完成，共 {len(result_segments)} 個片段，語言: {result['language']}")
        
        return result
    
    def _detect_content_language(self, segments: List[Dict]) -> str:
        """
        根據實際文本內容的英文/中文字符比例來判斷主要語言
        
        Args:
            segments: 轉錄片段列表
        
        Returns:
            str: 語言代碼 ("zh" 或 "en")
        """
        # 合併所有文本
        all_text = " ".join([seg["text"] for seg in segments])
        
        # 統計中文字符（CJK 統一表意文字）
        chinese_count = sum(1 for c in all_text if '\u4e00' <= c <= '\u9fff')
        
        # 統計英文字母
        english_count = sum(1 for c in all_text if c.isalpha() and ord(c) < 128)
        
        # 判斷主要語言（閾值：英文占 > 60% 則判為英文）
        total_chars = chinese_count + english_count
        if total_chars == 0:
            return "en"  # 預設英文（通常是沒有字符的情況）
        
        english_ratio = english_count / total_chars
        
        print(f"[Transcriber] 語言分析: 中文 {chinese_count}, 英文 {english_count}, 英文比例 {english_ratio:.1%}")
        
        if english_ratio > 0.6:
            return "en"
        else:
            return "zh"
    
    def save_transcript(self, transcript: Dict, output_name: str = None) -> Path:
        """
        將逐字稿保存為 JSON
        
        Args:
            transcript: 轉錄結果
            output_name: 輸出檔名（不含副檔名），若為None則用影片名
        
        Returns:
            Path: 輸出檔案路徑
        """
        if output_name is None:
            # 從影片名生成輸出名
            output_name = Path(transcript["filename"]).stem
        
        output_path = TRANSCRIPTS_DIR / f"{output_name}.json"
        
        # 保存為帶格式的 JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transcript, f, ensure_ascii=False, indent=2)
        
        print(f"[Transcriber] 逐字稿已保存至: {output_path}")
        
        return output_path
    
    def load_transcript(self, json_path: str) -> Dict:
        """
        加載已保存的逐字稿 JSON
        
        Args:
            json_path: JSON 檔案路徑
        
        Returns:
            dict: 逐字稿內容
        """
        json_path = Path(json_path)
        
        if not json_path.exists():
            raise FileNotFoundError(f"檔案不存在: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            transcript = json.load(f)
        
        print(f"[Transcriber] 已加載逐字稿: {json_path}")
        
        return transcript


# 主程序示例
if __name__ == "__main__":
    # 這裡會在 test_transcriber.py 中真正測試
    print("請使用 tests/test_transcriber.py 來測試此模塊")
