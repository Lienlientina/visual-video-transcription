"""
畫面理解模塊 - 使用 Ollama LLaVA 進行多模態分析
"""
import base64
import requests
from pathlib import Path
from typing import Dict

from config import OLLAMA_BASE_URL, LLAVA_MODEL
from utils import build_prompt_for_vision


class VisionAnalyzer:
    """畫面理解類"""
    
    def __init__(self, model_name: str = LLAVA_MODEL):
        """
        初始化視覺分析器
        
        Args:
            model_name (str): Ollama 模型名稱，預設為 LLAVA_MODEL
        """
        self.model_name = model_name
        self.base_url = OLLAMA_BASE_URL
        
        print(f"[VisionAnalyzer] 初始化 {model_name} 模型")
        print(f"[VisionAnalyzer] Ollama API: {self.base_url}")
        
        # 驗證連接
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name") for m in models]
                
                if self.model_name not in model_names:
                    raise RuntimeError(
                        f"模型 '{self.model_name}' 未找到。\n"
                        f"可用模型: {model_names}\n"
                        f"請執行: ollama pull {self.model_name}"
                    )
                
                print(f"✓ 模型 '{self.model_name}' 可用")
            else:
                raise RuntimeError(f"無法連接 Ollama API: {response.status_code}")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                f"無法連接 Ollama (地址: {self.base_url})\n"
                "請確保 Ollama 已啟動: ollama serve"
            )
    
    def analyze_image(self, image_path: str, context: str = "", deictic_word: str = "") -> Dict:
        """
        分析單張圖片
        
        Args:
            image_path (str): 圖片檔路徑
            context (str): 上下文信息，例如前後的文字
            deictic_word (str): 指示詞，例如「這個」、「藍色的部分」
        
        Returns:
            dict:
                {
                    "image_path": "outputs/frames/0_00_05.jpg",
                    "description": "白板上有一個微分公式...",
                    "model": "llava",
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
            
            # 構建提示詞（包含指示詞）
            prompt = build_prompt_for_vision(str(image_path), context, deictic_word)
            
            print(f"[VisionAnalyzer] 分析圖片: {image_path.name}")
            
            # 調用 Ollama API
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "images": [image_data],
                    "stream": False,
                    "temperature": 0.7
                },
                timeout=120  # LLaVA 推理可能比較慢
            )
            
            if response.status_code != 200:
                return {
                    "image_path": str(image_path),
                    "description": "",
                    "error": f"API 返回錯誤: {response.status_code}",
                    "success": False
                }
            
            result_json = response.json()
            description = result_json.get("response", "").strip()
            
            print(f"✓ 分析完成")
            
            return {
                "image_path": str(image_path),
                "description": description,
                "model": self.model_name,
                "success": True
            }
        
        except requests.exceptions.Timeout:
            return {
                "image_path": str(image_path),
                "description": "",
                "error": "API 請求超時（模型推理過慢）",
                "success": False
            }
        except Exception as e:
            return {
                "image_path": str(image_path),
                "description": "",
                "error": str(e),
                "success": False
            }
    
    def analyze_frames_batch(self, frames_data: Dict) -> Dict:
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
        
        print(f"\n[VisionAnalyzer] 開始批量分析 {len(frames)} 張圖片")
        
        analyses = []
        success_count = 0
        
        for idx, frame_info in enumerate(frames, 1):
            image_path = frame_info.get("path")
            context = frame_info.get("text", "")
            deictic_word = frame_info.get("word", "")  # 提取指示詞
            
            print(f"  [{idx}/{len(frames)}] 分析: {Path(image_path).name}")
            
            result = self.analyze_image(image_path, context, deictic_word)
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
