"""
測試語音轉逐字稿模塊
"""
import sys
from pathlib import Path

# 添加上級目錄到路徑，以便導入模塊
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.transcriber import Transcriber
from config import TRANSCRIPTS_DIR, DEMO_VIDEO_DIR


def test_transcriber(video_path):
    """
    測試轉錄器基本功能
    
    Args:
        video_path (str): 影片路徑 (必需)
    """
    
    print("=" * 60)
    print("測試: Transcriber 模塊")
    print("=" * 60)
    
    # 檢查檔案是否存在
    video_path = Path(video_path)
    if not video_path.exists():
        print(f"\n✗ 檔案不存在: {video_path}")
        return
    
    # 初始化轉錄器
    try:
        transcriber = Transcriber()
        print("✓ Transcriber 初始化成功")
    except Exception as e:
        print(f"✗ Transcriber 初始化失敗: {e}")
        return
    
    print(f"\n✓ 使用影片: {video_path.name}")
    
    # 執行轉錄
    try:
        print(f"\n開始轉錄...")
        result = transcriber.transcribe(str(video_path), language="zh")
        
        # 保存逐字稿
        output_path = transcriber.save_transcript(result)
        print(f"\n✓ 逐字稿已保存至: {output_path}")
        
        # 顯示前幾個片段
        print("\n前 5 個片段:")
        print("-" * 60)
        for segment in result["segments"][:5]:
            print(f"  {segment['time']} {segment['text']}")
        
        if len(result["segments"]) > 5:
            print(f"  ... 共 {len(result['segments'])} 個片段")
            
    except Exception as e:
        print(f"\n✗ 轉錄失敗: {e}")
        import traceback
        traceback.print_exc()


def demo_transcript_format():
    """展示輸出格式"""
    print("\n" + "=" * 60)
    print("預期輸出格式示例:")
    print("=" * 60)
    
    example = {
        "filename": "demo.mp4",
        "language": "zh",
        "segments": [
            {
                "time": "[0:00:05]",
                "text": "大家好，今天我們要講反向傳播",
                "start": 5.0,
                "end": 10.2
            },
            {
                "time": "[0:00:10]",
                "text": "它是深度學習中最重要的演算法",
                "start": 10.2,
                "end": 15.5
            }
        ]
    }
    
    import json
    print(json.dumps(example, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("=" * 60)
        print("使用方法:")
        print("=" * 60)
        print(f"python tests/test_transcriber.py <影片檔案路徑>")
        print()
        print("範例:")
        print(f"  python tests/test_transcriber.py demo_video/my_video.mp4")
        print(f"  python tests/test_transcriber.py C:\\path\\to\\video.mp4")
        print()
        print("支援的格式: .mp4, .mkv, .avi, .mov, .webm, .wav, .m4a")
        print("=" * 60)
        demo_transcript_format()
    else:
        video_file = sys.argv[1]
        test_transcriber(video_path=video_file)
