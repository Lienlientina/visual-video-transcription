"""
語音轉逐字稿模塊 - 使用 faster-whisper
輸出帶時間戳的逐字稿
"""
import json
from pathlib import Path
from typing import List, Dict, Tuple
import warnings

try:
    from faster_whisper import WhisperModel
except ImportError:
    raise ImportError("faster-whisper 未安裝，請執行: pip install faster-whisper")

from config import WHISPER_MODEL, DEVICE, TRANSCRIPTS_DIR
from utils import seconds_to_timestamp


class Transcriber:
    """語音轉逐字稿類"""
    
    # 字幕單行最大字符數（超過自動分割）
    MAX_SEGMENT_LENGTH = 60
    
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
    
    def transcribe(self, video_path: str, language: str = None) -> Dict:
        """
        將影片轉錄為逐字稿
        
        Args:
            video_path: 影片檔路徑
            language: 語言代碼，預設 None（自動檢測）。可指定 "zh"、"en" 等強制使用特定語言
        
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
            vad_parameters=dict(
                min_silence_duration_ms=100, threshold=0.3, 
                min_speech_duration_ms=250)
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
        
        # ← 簡化：多層次語言檢測策略（只返回 en 或 zh）
        detected_lang = info.language if info else None
        print(f"[Transcriber] Whisper 檢測語言: {detected_lang}")
        
        content_lang = self._detect_content_language(result_segments)
        # print(f"[Transcriber] 內容分析語言: {content_lang}")
        
        result_lang = content_lang
        
        print(f"[Transcriber] 最終語言: {result_lang}")
        
        result = {
            "filename": video_path.name,
            "language": result_lang,
            "segments": result_segments
        }
        
        # 進行語義修正（修正錯字）
        result = self._correct_transcript(result, result["language"])
        
        print(f"[Transcriber] 轉錄完成，共 {len(result['segments'])} 個片段，語言: {result['language']}")
        
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
        
        # 統計各類字符
        # CJK 統一表意文字（中文）
        chinese_count = sum(1 for c in all_text if '\u4e00' <= c <= '\u9fff')
        
        # 英文字母（a-z, A-Z）
        english_letter_count = sum(1 for c in all_text if c.isalpha() and ord(c) < 128)
        
        print(f"[Transcriber] 字符統計: 中文={chinese_count}, 英文={english_letter_count}")
        
        # 計算英文比例
        meaningful_chars = chinese_count + english_letter_count
        
        if meaningful_chars == 0:
            print(f"[Transcriber] 無意義字符，返回默認語言: en")
            return "en"
        
        english_ratio = english_letter_count / meaningful_chars

        # 判斷主要語言（閾值：英文占 > 50% 則判為英文；反之為中文）
        if english_ratio > 0.5:
            print(f"[Transcriber] 判定為: 英文 (ratio={english_ratio:.2f})")
            return "en"
        else:
            print(f"[Transcriber] 判定為: 中文 (ratio={english_ratio:.2f})")
            return "zh"
    

    def _correct_transcript(self, transcript_json: Dict, language: str) -> Dict:
        """
        使用 Gemini 進行語義修正（修正錯字、同音字等）
        只修改 "text" 字段，完全保留其他欄位格式
        
        Args:
            transcript_json: 轉錄結果 dict
            language: 語言代碼 ("zh" 或 "en")
        
        Returns:
            dict: 修正後的 transcript_json
        """
        try:
            import google.generativeai as genai
            from config import GEMINI_API_KEY
            
            if not GEMINI_API_KEY:
                print("[Transcriber] ⚠️  跳過語義修正（未設置 GEMINI_API_KEY）")
                return transcript_json
            
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel("gemini-3.1-flash-lite")
            
            segments = transcript_json.get("segments", [])
            if not segments:
                return transcript_json
            
            # 判斷是中文還是英文
            is_chinese = language.startswith('zh')
            
            print(f"[Transcriber] 開始進行語義修正（語言: {language}）...")
            
            # ← 改進：使用 JSON 格式確保結構完整性
            segments_dict = {str(i): seg['text'] for i, seg in enumerate(segments)}
            segments_json = json.dumps(segments_dict, ensure_ascii=False, indent=2)
            
            # ← 一次性發給 Gemini，要求以 JSON 格式返回
            if language == "zh":
                prompt = f"""請修正以下繁體中文語音轉錄的錯字，修正以下幾種情況：
                1. 同音字錯誤（例如「咋」→「這」、「再」→「在」）
                2. 專有名詞誤認（例如「派森」→「Python」）
                3. 明顯的語法或文法錯誤

                輸出格式：JSON 對象，鍵為索引字符串（"0", "1"...），值為修正後的文本。
                只輸出 JSON，不要包含任何說明或 Markdown 標記。

                原文：
                {segments_json}

                修正後（必須是有效的 JSON）："""
            else:
                prompt = f"""Please correct the following English speech transcription errors. Fix:
                1. Homophone errors (e.g., "its" → "it's", "there" → "their")
                2. Proper noun misrecognition (e.g., "centre" → "center" if context suggests US English)
                3. Obvious grammar or spelling errors

                Output format: JSON object with string keys ("0", "1"...) mapping to corrected text.
                Output only valid JSON, no explanations or markdown.

                Original text:
                {segments_json}

                Corrected text (must be valid JSON):"""
            
            response = model.generate_content(prompt)
            corrected_all = response.text.strip()
            
            # ← 移除可能的 Markdown 標記（```json ... ```）
            if corrected_all.startswith("```"):
                corrected_all = corrected_all.split("```")[1]
                if corrected_all.startswith("json"):
                    corrected_all = corrected_all[4:]
            if corrected_all.endswith("```"):
                corrected_all = corrected_all[:-3]
            corrected_all = corrected_all.strip()
            
            # ← 解析 JSON
            corrected_dict = json.loads(corrected_all)
            corrected_segments = []
            
            # ← 逐個 segment 應用修正（安全地處理缺失的鍵）
            for i, seg in enumerate(segments):
                corrected_seg = seg.copy()
                str_idx = str(i)
                
                if str_idx in corrected_dict:
                    corrected_text = corrected_dict[str_idx]
                    if isinstance(corrected_text, str):
                        corrected_seg["text"] = corrected_text
                    else:
                        print(f"[Transcriber] ⚠️  段落 {i} 修正格式錯誤（非字符串），保持原文")
                else:
                    print(f"[Transcriber] ⚠️  段落 {i} 在 Gemini 返回中缺失，保持原文")
                
                corrected_segments.append(corrected_seg)
            
            # 修改 segments，其他欄位（filename, language）完全不動
            transcript_json["segments"] = corrected_segments
            
            print(f"[Transcriber] 語義修正完成，共 {len(corrected_segments)} 個片段")
        
        except json.JSONDecodeError as e:
            print(f"[Transcriber] ⚠️  Gemini 返回無效 JSON: {e}")
            print(f"[Transcriber] 原始返回: {corrected_all[:200]}...")
            print(f"[Transcriber] 保留原文")
        except Exception as e:
            print(f"[Transcriber] ⚠️  語義修正失敗: {e}，保留原文")
        
        return transcript_json
    

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
