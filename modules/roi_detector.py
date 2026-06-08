"""
ROI 偵測器 - 自動識別並裁切關鍵區域
支援 Vision API（可選）+ 全圖備選

流程：
  1. 嘗試 Vision API（如果可用，支援 Rate Limit 重試）
  2. 失敗 → 返回全圖
  
所有情況下都返回有效的 ROI 坐標
"""

import cv2
import numpy as np
import time
from pathlib import Path


class ROIDetector:
    """
    關鍵區域偵測器
    
    支援兩層降級策略：
    - 層級 1：Vision API（質量最佳，需要 API）
    - 層級 2：全圖備選（保證有輸出）
    """
    
    def __init__(self, use_vision_api=False, vision_api_key=None, vision_model=None, verbose=True):
        """
        初始化 ROI 偵測器
        
        Args:
            use_vision_api (bool): 是否嘗試使用 Vision API
            vision_api_key (str): Gemini Vision API key（可選）
            vision_model (str): Gemini Vision 模型名稱（例如 gemini-2.5-flash-preview）
            verbose (bool): 是否在終端打印偵測方法
        """
        self.use_vision_api = use_vision_api
        self.vision_api_key = vision_api_key
        self.vision_model = vision_model
        self.verbose = verbose
        self.last_method = None
    
    def detect_roi_with_vision_api(self, image_path, recall_info=None):
        """
        使用 Gemini Vision API 偵測 ROI
        支援 Rate Limit 重試機制
        
        Args:
            image_path (str): 圖片路徑
            recall_info (dict): Recall 信息（包含觸發詞等）
        
        Returns:
            dict or None: ROI 坐標或 None（失敗）
        """
        if not self.use_vision_api:
            return None
        
        max_retries = 1
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                import google.generativeai as genai
                
                if not self.vision_api_key:
                    # 嘗試從環境變數讀取
                    import os
                    api_key = os.getenv("GEMINI_API_KEY")
                    if not api_key:
                        if self.verbose:
                            print(f"  ✗ Vision API: 未找到 API key")
                        return None
                else:
                    api_key = self.vision_api_key
                
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(self.vision_model)
                
                # 讀取圖片
                with open(image_path, "rb") as f:
                    image_data = f.read()
                
                # 組織 prompt
                # ← 改：加入完整的上下文信息
                trigger_cue = recall_info.get("recall_cue", "") if recall_info else ""
                trigger_text = recall_info.get("trigger_text", "") if recall_info else ""
                recalled_text = recall_info.get("recalled_text", "") if recall_info else ""
                
                prompt = f"""【影片 ROI 偵測】

                觸發詞彙："{trigger_cue}"

                觸發時刻的文本內容：
                "{trigger_text}"

                被回憶的概念完整文本：
                "{recalled_text}"

                任務：根據上述背景，在此圖片中找出關鍵區域（ROI）。

                指導原則：
                - 優先找出公式、方程式、定理、圖表、圖示說明、code、重要文字等
                - 公式或樹狀圖部分應完整截圖，避免只截取部分內容
                - 盡量避免邊框、光標、空白區、UI元素

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
                        "description": f"AI 偵測區域 ({trigger_cue})"
                    }
                else:
                    if self.verbose:
                        print(f"  ✗ Vision API 回應格式錯誤: {result_text[:50]}")
                    return None
            
            except Exception as e:
                error_msg = str(e).lower()
                
                # 檢查是否為 Rate Limit 錯誤
                is_rate_limit = ("rate limit" in error_msg or 
                                "quota" in error_msg or 
                                "429" in error_msg or
                                "too many requests" in error_msg or
                                "resource exhausted" in error_msg)
                
                if is_rate_limit and retry_count < max_retries - 1:
                    # Rate Limit 錯誤：等待後重試
                    retry_count += 1
                    wait_time = 60
                    if self.verbose:
                        print(f"  ⚠ Vision API Rate Limit，等待 {wait_time} 秒後重試... ({retry_count}/{max_retries-1})")
                    time.sleep(wait_time)
                    continue
                else:
                    # 其他錯誤或達到重試次數上限
                    if self.verbose:
                        error_brief = str(e)[:80]
                        print(f"  ✗ Vision API 失敗: {error_brief}")
                    return None
        
        return None
    
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
    
    def _snap_to_content_boundary(self, img, x, y, w, h):
        """
        以 AI ROI 為起點，向四個方向擴張至真實內容邊界。
        用行/列標準差判斷「背景 vs 內容」，門檻為相對值，適用任何背景色。
        """
        height, width = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 搜索範圍 = AI ROI + 各方向 12%
        MARGIN = 0.12
        s_y1 = max(0, y - int(MARGIN * height))
        s_y2 = min(height, y + h + int(MARGIN * height))
        s_x1 = max(0, x - int(MARGIN * width))
        s_x2 = min(width, x + w + int(MARGIN * width))

        row_stds = np.array([np.std(gray[r, s_x1:s_x2]) for r in range(s_y1, s_y2)])
        col_stds = np.array([np.std(gray[s_y1:s_y2, c]) for c in range(s_x1, s_x2)])

        if len(row_stds) == 0 or len(col_stds) == 0:
            return x, y, w, h

        # 背景門檻：標準差低於最大值 10% 視為純色背景
        row_bg = max(row_stds) * 0.10
        col_bg = max(col_stds) * 0.10

        r_top = y - s_y1
        r_bot = (y + h) - s_y1
        c_lft = x - s_x1
        c_rgt = (x + w) - s_x1

        # 向上擴張：從 AI ROI 頂部往上掃，遇背景列停下
        new_y1 = s_y1
        for r in range(r_top, -1, -1):
            if row_stds[r] < row_bg:
                new_y1 = s_y1 + r + 1
                break

        # 向下擴張
        new_y2 = s_y2
        for r in range(r_bot, len(row_stds)):
            if row_stds[r] < row_bg:
                new_y2 = s_y1 + r
                break

        # 向左擴張
        new_x1 = s_x1
        for c in range(c_lft, -1, -1):
            if col_stds[c] < col_bg:
                new_x1 = s_x1 + c + 1
                break

        # 向右擴張
        new_x2 = s_x2
        for c in range(c_rgt, len(col_stds)):
            if col_stds[c] < col_bg:
                new_x2 = s_x1 + c
                break

        # 確保不縮小 AI ROI
        new_x1 = min(new_x1, x)
        new_y1 = min(new_y1, y)
        new_x2 = max(new_x2, x + w)
        new_y2 = max(new_y2, y + h)

        return new_x1, new_y1, new_x2 - new_x1, new_y2 - new_y1

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

            # 用行/列標準差掃描自動擴展到真實內容邊界（不依賴背景色）
            x, y, w, h = self._snap_to_content_boundary(img, x, y, w, h)

            # 最終邊界檢查
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


if __name__ == "__main__":
    pass