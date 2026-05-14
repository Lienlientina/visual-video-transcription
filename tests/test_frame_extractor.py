"""
測試影片截幀模塊
"""
import sys
import json
from pathlib import Path

# 添加上級目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.frame_extractor import FrameExtractor
from modules.deictic_detector import DeicticDetector
from modules.transcriber import Transcriber


def test_frame_extractor(video_path, transcript_json_path=None):
    """
    測試幀提取器（新工作流程：基於指示詞截幀）
    
    Args:
        video_path (str): 影片路徑
        transcript_json_path (str, optional): 逐字稿 JSON 路徑，若為 None 則自動轉錄
    """
    
    print("=" * 60)
    print("測試: FrameExtractor 模塊（基於指示詞截幀）")
    print("=" * 60)
    
    # 初始化幀提取器
    try:
        extractor = FrameExtractor()
        print("✓ FrameExtractor 初始化成功")
    except Exception as e:
        print(f"✗ FrameExtractor 初始化失敗: {e}")
        return
    
    # 初始化指示詞偵測器
    try:
        detector = DeicticDetector()
        print("✓ DeicticDetector 初始化成功")
    except Exception as e:
        print(f"✗ DeicticDetector 初始化失敗: {e}")
        return
    
    # 檢查影片
    video_path = Path(video_path)
    if not video_path.exists():
        print(f"✗ 影片不存在: {video_path}")
        return
    
    print(f"✓ 影片: {video_path.name}")
    
    # 加載或生成逐字稿
    if transcript_json_path is None:
        # 自動轉錄
        print("\n開始生成逐字稿...")
        transcriber = Transcriber()
        transcript_json = transcriber.transcribe(str(video_path), language="zh")
    else:
        # 加載現有的 JSON
        transcript_json_path = Path(transcript_json_path)
        if not transcript_json_path.exists():
            print(f"✗ 逐字稿 JSON 不存在: {transcript_json_path}")
            return
        
        with open(transcript_json_path, 'r', encoding='utf-8') as f:
            transcript_json = json.load(f)
        
        print(f"✓ 已加載逐字稿: {transcript_json_path.name}")
    
    # 偵測指示詞
    print("\n開始偵測指示詞...")
    deictic_data = detector.detect_from_transcript(transcript_json)
    
    if deictic_data["total_deictic_words"] == 0:
        print("\n⚠️ 未找到指示詞，沒有幀需要截取")
        return
    
    # 根據指示詞截幀
    try:
        print("\n開始截幀...")
        frames_result = extractor.extract_frames_from_deictic(str(video_path), deictic_data)
        
        # 顯示結果
        print("\n截幀結果:")
        print("-" * 60)
        for frame_info in frames_result["frames"][:5]:
            print(f"  {frame_info['timestamp']} 「{frame_info['word']}」")
            print(f"    路徑: {frame_info['path']}")
            print(f"    上下文: {frame_info['context']}")
            print()
        
        if len(frames_result["frames"]) > 5:
            print(f"  ... 共 {len(frames_result['frames'])} 幀")
        
        print(f"\n✓ 截幀完成!")
        print(f"  成功: {frames_result['success_frames']}/{frames_result['total_deictic_words']}")
        
    except Exception as e:
        print(f"✗ 截幀失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("=" * 60)
        print("使用方法:")
        print("=" * 60)
        print(f"python tests/test_frame_extractor.py <影片檔案路徑> [逐字稿JSON路徑]")
        print()
        print("範例:")
        print(f"  # 自動轉錄並根據指示詞截幀")
        print(f"  python tests/test_frame_extractor.py demo_video/my_video.mp4")
        print()
        print(f"  # 使用已有的逐字稿 JSON")
        print(f"  python tests/test_frame_extractor.py demo_video/my_video.mp4 outputs/transcripts/my_video.json")
        print("=" * 60)
    else:
        video_file = sys.argv[1]
        transcript_file = sys.argv[2] if len(sys.argv) > 2 else None
        test_frame_extractor(video_path=video_file, transcript_json_path=transcript_file)
