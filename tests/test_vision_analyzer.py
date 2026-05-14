"""
測試畫面理解模塊
"""
import sys
import json
from pathlib import Path

# 添加上級目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.vision_analyzer import VisionAnalyzer
from modules.frame_extractor import FrameExtractor


def test_vision_analyzer(image_path):
    """
    測試單張圖片分析
    
    Args:
        image_path (str): 圖片路徑
    """
    
    print("=" * 60)
    print("測試: VisionAnalyzer 模塊 (單張圖片)")
    print("=" * 60)
    
    # 初始化分析器
    try:
        analyzer = VisionAnalyzer()
        print("✓ VisionAnalyzer 初始化成功\n")
    except Exception as e:
        print(f"✗ VisionAnalyzer 初始化失敗: {e}")
        return
    
    # 檢查圖片
    image_path = Path(image_path)
    if not image_path.exists():
        print(f"✗ 圖片不存在: {image_path}")
        return
    
    print(f"✓ 圖片: {image_path.name}\n")
    
    # 分析圖片
    try:
        print("開始分析...")
        result = analyzer.analyze_image(str(image_path))
        
        print("\n分析結果:")
        print("-" * 60)
        
        if result.get("success"):
            print(f"✓ 分析成功")
            print(f"\n描述:")
            print(result["description"])
        else:
            print(f"✗ 分析失敗")
            print(f"錯誤: {result.get('error', '未知錯誤')}")
        
    except Exception as e:
        print(f"✗ 分析出錯: {e}")
        import traceback
        traceback.print_exc()


def test_batch_analysis(frames_json_data):
    """
    測試批量圖片分析
    
    Args:
        frames_json_data (dict): 來自 FrameExtractor 的數據
    """
    
    print("=" * 60)
    print("測試: VisionAnalyzer 模塊 (批量分析)")
    print("=" * 60)
    
    # 初始化分析器
    try:
        analyzer = VisionAnalyzer()
        print("✓ VisionAnalyzer 初始化成功\n")
    except Exception as e:
        print(f"✗ VisionAnalyzer 初始化失敗: {e}")
        return
    
    # 批量分析
    try:
        print(f"開始批量分析...")
        result = analyzer.analyze_frames_batch(frames_json_data)
        
        print("\n分析結果:")
        print("-" * 60)
        
        for idx, analysis in enumerate(result["analyses"][:5], 1):
            image_name = Path(analysis["image_path"]).name
            print(f"\n[{idx}] {image_name}")
            
            if analysis.get("success"):
                print(f"  ✓ {analysis['description'][:80]}...")
            else:
                print(f"  ✗ 錯誤: {analysis.get('error', '未知錯誤')}")
        
        if len(result["analyses"]) > 5:
            print(f"\n... 共 {len(result['analyses'])} 張圖片")
        
        print(f"\n摘要: {result['success']}/{result['total']} 成功")
        
    except Exception as e:
        print(f"✗ 批量分析出錯: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("=" * 60)
        print("使用方法:")
        print("=" * 60)
        print(f"python tests/test_vision_analyzer.py <圖片路徑>")
        print()
        print("範例:")
        print(f"  python tests/test_vision_analyzer.py outputs/frames/0_00_05.jpg")
        print("=" * 60)
    else:
        image_file = sys.argv[1]
        test_vision_analyzer(image_path=image_file)
