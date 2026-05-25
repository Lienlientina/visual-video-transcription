"""
字幕轉換模塊 - 將融合逐字稿轉為 SRT 格式
"""
from typing import Dict
from pathlib import Path


class SubtitleConverter:
    """字幕轉換類 - SRT 生成"""
    
    def __init__(self):
        """初始化字幕轉換器"""
        pass
    
    def fused_json_to_srt(self, fused_json: Dict) -> str:
        """
        將融合逐字稿轉為 SRT 格式
        
        Args:
            fused_json (dict): 融合逐字稿 JSON
                {
                    "segments": [...],
                    "recalls": [
                        {
                            "segment_idx": 5,
                            "recalled_time": "[0:01:40]",
                            "recalled_text": "...",
                            "recall_type": "direct|contrast",
                            "similarity_score": 0.82
                        }
                    ]
                }
        
        Returns:
            str: SRT 格式的字幕文本
        """
        if not fused_json.get("segments"):
            print("[SubtitleConverter] ⚠️  沒有 segments，無法生成字幕")
            return ""
        
        segments = fused_json["segments"]
        
        # ← 新增：建立 recall 映射
        recall_map = {}
        for recall in fused_json.get("recalls", []):
            segment_idx = recall.get("segment_idx")
            if segment_idx not in recall_map:
                recall_map[segment_idx] = []
            recall_map[segment_idx].append(recall)
        
        srt_lines = []
        
        for i, seg in enumerate(segments):
            # 提取信息
            start_time = self._seconds_to_srt(seg.get("start", 0))
            
            # 計算結束時間（用下一個 segment 的開始時間，或當前 segment 的結束時間）
            if i + 1 < len(segments):
                end_time = self._seconds_to_srt(segments[i + 1].get("start", seg.get("end", 0)))
            else:
                end_time = self._seconds_to_srt(seg.get("end", seg.get("start", 0) + 3))
            
            # 提取字幕文本（優先用 fused_text，否則用 text）
            subtitle_text = seg.get("fused_text", seg.get("text", ""))
            
            # 跳過空字幕
            if not subtitle_text.strip():
                continue
            
            # ← 新增：添加 recall 標注（如果有）
            if i in recall_map:
                for recall in recall_map[i]:
                    recall_time = recall.get("recalled_time", "")
                    recall_text = recall.get("recalled_text", "")[:30]  # 前 30 字
                    recall_type = recall.get("recall_type", "direct")
                    
                    if recall_type == "contrast":
                        annotation = f"[↔ {recall_time} {recall_text}...]"
                    else:
                        annotation = f"[↑ {recall_time} {recall_text}...]"
                    
                    subtitle_text = f"{annotation}\n{subtitle_text}"
            
            # 組合 SRT 格式
            index = len(srt_lines) // 4 + 1  # 每個字幕塊占 4 行（序號、時間、文本、空行）
            srt_lines.append(str(index))
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(subtitle_text.strip())
            srt_lines.append("")  # 空行分隔
        
        srt_content = "\n".join(srt_lines)
        return srt_content
    
    def _seconds_to_srt(self, seconds: float) -> str:
        """
        將秒數轉換為 SRT 時間格式 (HH:MM:SS,mmm)
        
        Args:
            seconds (float): 秒數
        
        Returns:
            str: SRT 時間格式，例如 "00:01:23,456"
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    def save_srt(self, srt_content: str, output_path: Path) -> Path:
        """
        保存 SRT 檔案
        
        Args:
            srt_content (str): SRT 格式的字幕內容
            output_path (Path): 輸出檔案路徑
        
        Returns:
            Path: 保存的檔案路徑
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        print(f"[SubtitleConverter] 字幕已保存: {output_path}")
        
        return output_path


if __name__ == "__main__":
    print("請使用 tests/test_subtitle_converter.py 來測試此模塊")
