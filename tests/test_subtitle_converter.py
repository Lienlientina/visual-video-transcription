"""
字幕轉換模塊測試
"""
import sys
from pathlib import Path

# 添加父目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.subtitle_converter import SubtitleConverter


def test_srt_generation():
    """測試 SRT 格式生成"""
    
    converter = SubtitleConverter()
    
    # 模擬融合逐字稿數據
    fused_json = {
        "segments": [
            {
                "time": "[0:00:05]",
                "text": "各位同學好",
                "fused_text": "各位同學好[視覺補充: 教室黑板]",
                "start": 5.0,
                "end": 8.5
            },
            {
                "time": "[0:00:08]",
                "text": "這個公式很重要",
                "fused_text": "這個[視覺補充: 白板上的藍色公式]公式很重要",
                "start": 8.5,
                "end": 12.0
            },
            {
                "time": "[0:00:12]",
                "text": "讓我們代入一個值",
                "fused_text": "讓我們代入一個值",
                "start": 12.0,
                "end": 15.0
            }
        ]
    }
    
    # 生成 SRT
    srt_content = converter.fused_json_to_srt(fused_json)
    
    # 驗證
    assert "00:00:05,000 --> 00:00:08,500" in srt_content, "時間格式錯誤"
    assert "各位同學好[視覺補充: 教室黑板]" in srt_content, "字幕文本遺失"
    assert "這個[視覺補充: 白板上的藍色公式]公式很重要" in srt_content, "融合文本遺失"
    
    print("[✓] SRT 生成測試通過")
    print("\n===== SRT 預覽 =====")
    print(srt_content)
    print("====================\n")


def test_seconds_to_srt():
    """測試秒數轉 SRT 時間格式"""
    
    converter = SubtitleConverter()
    
    # 測試各種時間轉換
    test_cases = [
        (0, "00:00:00,000"),
        (5, "00:00:05,000"),
        (65, "00:01:05,000"),
        (3661, "01:01:01,000"),
        (3661.5, "01:01:01,500"),
        (123.456, "00:02:03,456"),
    ]
    
    for seconds, expected in test_cases:
        result = converter._seconds_to_srt(seconds)
        assert result == expected, f"轉換失敗: {seconds}s -> {result}（期望 {expected}）"
        print(f"✓ {seconds}s -> {result}")
    
    print("[✓] 時間轉換測試通過\n")


def test_empty_subtitle():
    """測試空字幕處理"""
    
    converter = SubtitleConverter()
    
    fused_json = {
        "segments": [
            {
                "time": "[0:00:05]",
                "text": "",  # 空字幕
                "fused_text": "",
                "start": 5.0,
                "end": 8.5
            }
        ]
    }
    
    srt_content = converter.fused_json_to_srt(fused_json)
    
    # 空字幕應該被跳過
    assert srt_content.strip() == "", "空字幕應該被跳過"
    print("[✓] 空字幕處理測試通過\n")


# 主程序
if __name__ == "__main__":
    print("========== 字幕轉換模塊測試 ==========\n")
    
    try:
        test_seconds_to_srt()
        test_empty_subtitle()
        test_srt_generation()
        
        print("========== 所有測試通過 ✓ ==========")
        
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
