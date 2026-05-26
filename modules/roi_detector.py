"""
ROI 偵測器 - 自動識別並裁切關鍵區域
支援 Vision API（可選）+ 全圖備選

流程：
  1. 嘗試 Vision API（如果可用）
  2. 失敗 → 返回全圖
  
所有情況下都返回有效的 ROI 坐標
"""

import cv2
import numpy as np
from pathlib import Path


class ROIDetector:
    """
    關鍵區域偵測器
    
    支援兩層降級策略：
    - 層級 1：Vision API（質量最佳，需要 API）
    - 層級 2：全圖備選（保證有輸出）
    """
    
    def __init__(self, use_vision_api=False, vision_api_key=None, verbose=True):
        """
        初始化 ROI 偵測器
        
        Args:
            use_vision_api (bool): 是否嘗試使用 Vision API
            vision_api_key (str): Gemini Vision API key（可選）
            verbose (bool): 是否在終端打印偵測方法
        """
        self.use_vision_api = use_vision_api
        self.vision_api_key = vision_api_key
        self.verbose = verbose
        self.last_method = None
    
    def detect_roi_with_vision_api(self, image_path, recall_info=None):
        """
        使用 Gemini Vision API 偵測 ROI
        
        Args:
            image_path (str): 圖片路徑
            recall_info (dict): Recall 信息（包含觸發詞等）
        
        Returns:
            dict or None: ROI 坐標或 None（失敗）
        """
        if not self.use_vision_api:
            return None
        
        try:
            import google.generativeai as genai
            
            if not self.vision_api_key:
                # 嘗試從環境變數讀取
                import os
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    return None
            else:
                api_key = self.vision_api_key
            
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-2.5-flash-preview")
            
            # 讀取圖片
            with open(image_path, "rb") as f:
                image_data = f.read()
            
            # 組織 prompt
            trigger_word = recall_info.get("recall_cue", "content") if recall_info else "content"
            prompt = f"""
請分析此圖片，找出關鍵區域（ROI）。
觸發詞："{trigger_word}"
請返回矩形框的相對坐標（0-1 範圍）：
格式：x_ratio, y_ratio, width_ratio, height_ratio

只返回四個數字，以逗號分隔，例如：0.1,0.2,0.8,0.6
"""
            
            # 調用 API
            response = model.generate_content([
                prompt,
                {"mime_type": "image/jpeg", "data": image_data}
            ])
            
            # 解析回應
            result_text = response.text.strip()
            coords = [float(x) for x in result_text.split(",")]
            
            if len(coords) == 4 and all(0 <= c <= 1 for c in coords):
                return {
                    "x_ratio": coords[0],
                    "y_ratio": coords[1],
                    "width_ratio": coords[2],
                    "height_ratio": coords[3],
                    "description": f"AI 偵測區域 ({trigger_word})"
                }
        
        except Exception as e:
            if self.verbose:
                pass  # 靜默失敗，稍後在降級中說明
        
        return None
    
    def detect_roi_simple(self, image_path):
        """
        啟發式 ROI 偵測 - 找圖片中最大的內容塊
        
        原理：
          1. 圖像二值化（轉黑白）
          2. 輪廓檢測
          3. 找最大的連通塊
          4. 返回外包矩形
        
        適用場景：講座、黑板、螢幕截圖
        
        Args:
            image_path (str): 圖片路徑
        
        Returns:
            dict: ROI 坐標（總是有效的）
        """
        try:
            # 讀取圖片
            img = cv2.imread(image_path)
            if img is None:
                return self._get_fallback_roi("圖片讀取失敗")
            
            height, width = img.shape[:2]
            
            # 轉灰度
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # 二值化 - 找黑色區域（反轉）
            # 閾值設為 127，低於 127 的像素變成白色（內容），高於的變成黑色（背景）
            _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV)
            
            # 輪廓檢測
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                return self._get_fallback_roi("未找到任何內容塊")
            
            # 找最大的輪廓
            largest_contour = max(contours, key=cv2.contourArea)
            area = cv2.contourArea(largest_contour)
            
            # 如果最大塊太小（面積 < 圖片面積的 5%），可能是噪音
            if area < (height * width * 0.05):
                return self._get_fallback_roi("最大內容塊太小，可能為噪音")
            
            # 外包矩形
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            # 轉為相對坐標（0-1）
            x_ratio = max(0, min(1, x / width))
            y_ratio = max(0, min(1, y / height))
            width_ratio = max(0, min(1, w / width))
            height_ratio = max(0, min(1, h / height))
            
            return {
                "x_ratio": x_ratio,
                "y_ratio": y_ratio,
                "width_ratio": width_ratio,
                "height_ratio": height_ratio,
                "description": f"啟發式偵測 (最大塊面積: {area:.0f}px²)"
            }
        
        except Exception as e:
            return self._get_fallback_roi(f"啟發式偵測失敗: {str(e)[:50]}")
    
    def _get_fallback_roi(self, reason=""):
        """
        返回備選方案 - 全圖
        
        Args:
            reason (str): 失敗原因（只用於內部日誌）
        
        Returns:
            dict: 全圖 ROI 坐標
        """
        return {
            "x_ratio": 0,
            "y_ratio": 0,
            "width_ratio": 1,
            "height_ratio": 1,
            "description": "完整圖片"
        }
    
    def detect_roi_with_fallback(self, image_path, recall_info=None):
        """
        多層降級 ROI 偵測
        
        優先級：
          1. Vision API（如果啟用且成功）
          2. 全圖備選（直接返回完整圖片）
        
        Args:
            image_path (str): 圖片路徑
            recall_info (dict): Recall 信息（包含觸發詞等）
        
        Returns:
            dict: 總是返回有效的 ROI 坐標
        """
        
        # 嘗試方案 1：Vision API
        if self.use_vision_api:
            roi = self.detect_roi_with_vision_api(image_path, recall_info)
            if roi:
                self.last_method = "Vision API"
                if self.verbose:
                    print(f"  ✓ ROI 偵測: Vision API")
                return roi
        
        # Vision API 未啟用或失敗 → 直接返回全圖
        self.last_method = "Full Image (Fallback)"
        if self.verbose:
            print(f"  ⊘ 直接輸出全圖")
        
        return self._get_fallback_roi("Vision API 不可用")
    
    def crop_image(self, image_path, roi_coords, output_path):
        """
        根據 ROI 坐標裁切並保存圖片
        
        Args:
            image_path (str): 原始圖片路徑
            roi_coords (dict): ROI 座標（相對形式）
            output_path (str): 輸出路徑
        
        Returns:
            dict: 裁切信息
        """
        try:
            # 讀取圖片
            img = cv2.imread(image_path)
            if img is None:
                return {"success": False, "error": "圖片讀取失敗"}
            
            height, width = img.shape[:2]
            
            # 相對坐標轉換為像素坐標
            x = int(roi_coords["x_ratio"] * width)
            y = int(roi_coords["y_ratio"] * height)
            w = int(roi_coords["width_ratio"] * width)
            h = int(roi_coords["height_ratio"] * height)
            
            # 邊界檢查
            x = max(0, min(x, width - 1))
            y = max(0, min(y, height - 1))
            w = max(1, min(w, width - x))
            h = max(1, min(h, height - y))
            
            # 裁切
            cropped = img[y:y+h, x:x+w]
            
            # 確保輸出目錄存在
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 保存
            cv2.imwrite(output_path, cropped)
            
            return {
                "success": True,
                "original_size": (width, height),
                "cropped_size": (w, h),
                "pixel_coords": (x, y, x + w, y + h)
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def detect_and_crop(self, image_path, output_cropped_path, recall_info=None):
        """
        主入口：偵測 ROI + 裁切 + 保存
        
        Args:
            image_path (str): 原始圖片路徑
            output_cropped_path (str): 裁切圖片輸出路徑
            recall_info (dict): Recall 信息（可選）
        
        Returns:
            dict: 包含 ROI 坐標和裁切結果
        """
        try:
            # Step 1：偵測 ROI（多層降級）
            roi_coords = self.detect_roi_with_fallback(image_path, recall_info)
            
            # Step 2：裁切圖片
            crop_result = self.crop_image(image_path, roi_coords, output_cropped_path)
            
            if not crop_result["success"]:
                if self.verbose:
                    print(f"  ✗ 裁切失敗: {crop_result.get('error', '未知錯誤')}")
                # 裁切失敗時，複製原始圖片作為裁切結果
                import shutil
                shutil.copy(image_path, output_cropped_path)
            
            # Step 3：組裝返回值
            return {
                "roi": roi_coords,
                "crop_result": crop_result
            }
        
        except Exception as e:
            if self.verbose:
                print(f"  ✗ ROI 偵測和裁切失敗: {str(e)}")
            # 最後的備選方案：複製原始圖片
            import shutil
            shutil.copy(image_path, output_cropped_path)
            
            return {
                "roi": self._get_fallback_roi(),
                "crop_result": {"success": False, "error": str(e)}
            }


def test_roi_detector():
    """
    簡單的測試函數（用於開發調試）
    """
    detector = ROIDetector(verbose=True)
    
    # 測試圖片路徑（需要實際存在的圖片）
    test_image = "outputs/results/frames/test.png"
    
    if Path(test_image).exists():
        roi = detector.detect_roi_with_fallback(test_image)
        print(f"\n偵測結果: {roi}")
        
        # 嘗試裁切
        result = detector.detect_and_crop(
            test_image,
            "outputs/results/frames/test_cropped.png"
        )
        print(f"裁切結果: {result}")
    else:
        print(f"測試圖片不存在: {test_image}")


if __name__ == "__main__":
    test_roi_detector()
