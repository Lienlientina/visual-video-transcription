"""
測試指示詞偵測模塊
"""
import sys
import json
from pathlib import Path

# 添加上級目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.deictic_detector import DeicticDetector
from modules.transcriber import Transcriber


def test_deictic_detector(transcript_json_path):
    """
    測試指示詞偵測器
    
    Args:
        transcript_json_path (str): 逐字稿 JSON 路徑
    """
    
    print("=" * 60)
    print("測試: DeicticDetector 模塊")
    print("=" * 60)
    
    # 初始化偵測器
    try:
        detector = DeicticDetector()
        print("✓ DeicticDetector 初始化成功")
    except Exception as e:
        print(f"✗ DeicticDetector 初始化失敗: {e}")
        return
    
    # 加載逐字稿
    transcript_json_path = Path(transcript_json_path)
    if not transcript_json_path.exists():
        print(f"✗ 逐字稿 JSON 不存在: {transcript_json_path}")
        return
    
    try:
        with open(transcript_json_path, 'r', encoding='utf-8') as f:
            transcript_json = json.load(f)
        print(f"✓ 已加載逐字稿: {transcript_json_path.name}")
    except Exception as e:
        print(f"✗ 加載失敗: {e}")
        return
    
    # 執行偵測
    try:
        result = detector.detect_from_transcript(transcript_json)
        
        # 顯示結果
        print("\n偵測結果:")
        print("-" * 60)
        
        if result["total_deictic_words"] == 0:
            print("  (未找到指示詞)")
        else:
            for idx, word_info in enumerate(result["deictic_words"][:10], 1):
                print(f"  [{idx}] {word_info['time']}")
                print(f"      詞: 「{word_info['word']}」")
                print(f"      上下文: 「{word_info['context']}」")
                print()
            
            if len(result["deictic_words"]) > 10:
                print(f"  ... 共 {len(result['deictic_words'])} 個指示詞")
        
        print("\n✓ 偵測完成!")
        
    except Exception as e:
        print(f"✗ 偵測失敗: {e}")
        import traceback
        traceback.print_exc()


def demo_output():
    """展示預期輸出格式"""
    print("\n" + "=" * 60)
    print("預期輸出格式示例:")
    print("=" * 60)
    
    example = {
        "total_segments": 6,
        "segments_with_deictic": 3,
        "total_deictic_words": 4,
        "deictic_words": [
            {
                "word": "這個",
                "time": "[0:00:05]",
                "segment_text": "把這個公式代入下面的方程式",
                "position_in_segment": 2,
                "context": "把這個公式代入"
            },
            {
                "word": "下面",
                "time": "[0:00:05]",
                "segment_text": "把這個公式代入下面的方程式",
                "position_in_segment": 7,
                "context": "入下面的方程式"
            }
        ]
    }
    
    print(json.dumps(example, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("=" * 60)
        print("使用方法:")
        print("=" * 60)
        print(f"python tests/test_deictic_detector.py <逐字稿JSON路徑>")
        print()
        print("範例:")
        print(f"  python tests/test_deictic_detector.py outputs/transcripts/video_demo1.json")
        print("=" * 60)
        demo_output()
    else:
        json_file = sys.argv[1]
        test_deictic_detector(transcript_json_path=json_file)
