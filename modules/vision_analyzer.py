"""
畫面理解模塊 - 使用 Gemini API 進行多模態分析
"""
import base64
from pathlib import Path
from typing import Dict
import google.generativeai as genai

from config import GEMINI_API_KEY, VISION_ANALYSIS_MODEL
from utils import build_prompt_for_vision


class VisionAnalyzer:
    """畫面理解類 - 使用 Gemini API"""
    
    def __init__(self, model_name: str = VISION_ANALYSIS_MODEL):
        """
        初始化視覺分析器
        
        Args:
            model_name (str): Gemini 模型名稱，預設為 VISION_ANALYSIS_MODEL
        """
        if not GEMINI_API_KEY:
            raise RuntimeError(
                "❌ 缺少 GEMINI_API_KEY\n"
                "請設置環境變數: set GEMINI_API_KEY=your-api-key\n"
                "或在 config.py 中直接填入 API Key"
            )
        
        self.model_name = model_name
        genai.configure(api_key=GEMINI_API_KEY)
        
        print(f"[VisionAnalyzer] 初始化 {model_name} 模型")
        print(f"[VisionAnalyzer] 使用 Gemini API")
        print(f"✓ Gemini 已就緒")
    
    def analyze_image(self, image_path: str, context: str = "", deictic_word: str = "", language: str = "en") -> Dict:
        """
        分析單張圖片
        
        Args:
            image_path (str): 圖片檔路徑
            context (str): 上下文信息，例如前後的文字
            deictic_word (str): 指示詞，例如「這個」、「藍色的部分」
            language (str): 語言代碼，"en" 或 "zh"（預設"en"）
        
        Returns:
            dict:
                {
                    "image_path": "outputs/frames/0_00_05.jpg",
                    "description": "白板上有一個微分公式...",
                    "model": "gemini-3.1-flash-lite",
                    "success": True
                }
        """
        image_path = Path(image_path)
        
        if not image_path.exists():
            return {
                "image_path": str(image_path),
                "description": "",
                "error": f"圖片不存在: {image_path}",
                "success": False
            }
        
        try:
            # 讀取圖片並轉為 base64
            with open(image_path, 'rb') as f:
                image_data = base64.standard_b64encode(f.read()).decode('utf-8')
            
            # 構建提示詞（根據語言參數）
            prompt = build_prompt_for_vision(str(image_path), context, deictic_word, language=language)
            
            print(f"[VisionAnalyzer] 分析圖片: {image_path.name}")
            
            # 調用 Gemini API
            model = genai.GenerativeModel(self.model_name)
            
            # 從文件副檔名判斷 MIME 類型
            suffix = image_path.suffix.lower()
            mime_types = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp"
            }
            mime_type = mime_types.get(suffix, "image/jpeg")
            
            # 構建請求內容
            contents = [
                prompt,
                {
                    "mime_type": mime_type,
                    "data": image_data
                }
            ]
            
            # 調用 Gemini
            response = model.generate_content(contents)
            description = response.text.strip()
            
            print(f"✓ 分析完成")
            
            return {
                "image_path": str(image_path),
                "description": description,
                "model": self.model_name,
                "success": True
            }
        
        except Exception as e:
            error_msg = str(e)
            return {
                "image_path": str(image_path),
                "description": "",
                "error": error_msg,
                "success": False
            }
    
    def analyze_frames_batch(self, frames_data: Dict, language: str = "en") -> Dict:
        """
        批量分析多個截幀
        
        Args:
            frames_data (dict): 來自 FrameExtractor 的輸出
                {
                    "frames": [
                        {"path": "outputs/frames/0_00_05.jpg", "text": "這個公式..."},
                        ...
                    ]
                }
            language (str): 語言代碼，"en" 或 "zh"（預設"en"）
        
        Returns:
            dict: 分析結果集合
                {
                    "total": 5,
                    "success": 4,
                    "analyses": [
                        {"path": "...", "description": "..."},
                        ...
                    ]
                }
        """
        frames = frames_data.get("frames", [])
        
        print(f"\n[VisionAnalyzer] 開始批量分析 {len(frames)} 張圖片 (語言: {language})")
        
        analyses = []
        success_count = 0
        
        for idx, frame_info in enumerate(frames, 1):
            image_path = frame_info.get("path")
            timestamp = frame_info.get("timestamp")
            precise_seconds = frame_info.get("precise_seconds")  # ← 新增：精確秒數
            context = frame_info.get("text", "")
            deictic_word = frame_info.get("word", "")
            
            print(f"  [{idx}/{len(frames)}] 分析: {Path(image_path).name}")
            
            result = self.analyze_image(image_path, context, deictic_word, language=language)
            result["timestamp"] = timestamp
            result["precise_seconds"] = precise_seconds  # ← 新增：保存精確秒數
            analyses.append(result)
            
            if result.get("success"):
                success_count += 1
        
        result_summary = {
            "total": len(frames),
            "success": success_count,
            "failed": len(frames) - success_count,
            "analyses": analyses
        }
        
        print(f"\n[VisionAnalyzer] 批量分析完成: {success_count}/{len(frames)} 成功")
        
        return result_summary


if __name__ == "__main__":
    print("請使用 tests/test_vision_analyzer.py 來測試此模塊")
