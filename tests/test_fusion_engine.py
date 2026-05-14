"""
測試融合引擎模塊
"""
import sys
import json
from pathlib import Path

# 添加上級目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.fusion_engine import FusionEngine
from modules.transcriber import Transcriber
from modules.deictic_detector import DeicticDetector
from modules.frame_extractor import FrameExtractor
from modules.vision_analyzer import VisionAnalyzer


def test_fusion_engine(transcript_json_path, deictic_json_path=None, vision_json_path=None):
    """
    測試融合引擎
    
    Args:
        transcript_json_path (str): 逐字稿 JSON 路徑
        deictic_json_path (str, optional): 指示詞 JSON 路徑（若無則自動生成）
        vision_json_path (str, optional): 視覺分析 JSON 路徑（若無則自動生成）
    """
    
    print("=" * 60)
    print("測試: FusionEngine 模塊（方案A：簡單替換）")
    print("=" * 60)
    
    # 初始化融合引擎
    try:
        engine = FusionEngine()
        print("✓ FusionEngine 初始化成功")
    except Exception as e:
        print(f"✗ FusionEngine 初始化失敗: {e}")
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
        print(f"✗ 加載逐字稿失敗: {e}")
        return
    
    # 加載或生成指示詞數據
    if deictic_json_path is None:
        print("\n生成指示詞數據...")
        detector = DeicticDetector()
        deictic_data = detector.detect_from_transcript(transcript_json)
    else:
        deictic_json_path = Path(deictic_json_path)
        if not deictic_json_path.exists():
            print(f"✗ 指示詞 JSON 不存在: {deictic_json_path}")
            return
        
        with open(deictic_json_path, 'r', encoding='utf-8') as f:
            deictic_data = json.load(f)
        print(f"✓ 已加載指示詞數據: {deictic_json_path.name}")
    
    if deictic_data["total_deictic_words"] == 0:
        print("\n⚠️ 未找到指示詞，無法進行融合")
        return
    
    # 模擬視覺分析數據（簡單版本）
    print("\n準備視覺分析數據...")
    vision_data = {
        "analyses": []
    }
    
    for deictic_word in deictic_data.get("deictic_words", [])[:5]:  # 只示範前5個
        timestamp = deictic_word["time"]
        context = deictic_word["context"]
        
        # 生成虛擬描述（實際應來自 VisionAnalyzer）
        vision_data["analyses"].append({
            "image_path": f"outputs/frames/{timestamp.replace('[', '').replace(']', '').replace(':', '_')}.jpg",
            "description": f"【{context}】的視覺內容",
            "success": True
        })
    
    print(f"✓ 已準備 {len(vision_data['analyses'])} 條視覺描述")
    
    # 執行融合
    try:
        print("\n開始融合...")
        fused_data = engine.fuse(transcript_json, deictic_data, vision_data)
        
        # 顯示結果
        print("\n融合結果:")
        print("-" * 60)
        
        for segment in fused_data["segments"][:5]:
            if segment["modified"]:
                print(f"{segment['time']}")
                print(f"  原文: {segment['original_text'][:60]}...")
                print(f"  融合: {segment['text'][:80]}...")
                print()
        
        if len([s for s in fused_data["segments"] if s["modified"]]) > 5:
            print(f"... 共 {fused_data['modified_segments']} 個修改段落")
        
        print(f"\n✓ 融合完成!")
        print(f"  修改段落: {fused_data['modified_segments']}/{fused_data['total_segments']}")
        print(f"  總替換數: {fused_data['total_replacements']}")
        
        # 保存結果
        print("\n保存結果...")
        output_base = transcript_json_path.stem
        engine.save_fused_transcript(fused_data, output_base)
        engine.export_as_json(fused_data, f"{output_base}_fusion")
        
    except Exception as e:
        print(f"✗ 融合失敗: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("=" * 60)
        print("使用方法:")
        print("=" * 60)
        print(f"python tests/test_fusion_engine.py <逐字稿JSON路徑> [指示詞JSON] [視覺JSON]")
        print()
        print("範例:")
        print(f"  python tests/test_fusion_engine.py outputs/transcripts/video_demo1.json")
        print("=" * 60)
    else:
        transcript_file = sys.argv[1]
        deictic_file = sys.argv[2] if len(sys.argv) > 2 else None
        vision_file = sys.argv[3] if len(sys.argv) > 3 else None
        test_fusion_engine(
            transcript_json_path=transcript_file,
            deictic_json_path=deictic_file,
            vision_json_path=vision_file
        )
