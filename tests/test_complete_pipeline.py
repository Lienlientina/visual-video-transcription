"""
完整流程集成測試
逐字稿 → 指示詞偵測 → 截幀 → 視覺分析 → 融合
"""
import sys
import json
from pathlib import Path

# 添加上級目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from modules.transcriber import Transcriber
from modules.deictic_detector import DeicticDetector
from modules.frame_extractor import FrameExtractor
from modules.vision_analyzer import VisionAnalyzer
from modules.fusion_engine import FusionEngine


def run_complete_pipeline(video_path, transcript_json_path=None):
    """
    運行完整的視頻轉錄 + 融合管線
    
    Args:
        video_path (str): 影片路徑
        transcript_json_path (str, optional): 逐字稿 JSON 路徑（若無則自動轉錄）
    """
    
    print("=" * 70)
    print("完整管線：逐字稿 → 指示詞 → 截幀 → 視覺分析 → 融合")
    print("=" * 70)
    
    video_path = Path(video_path)
    if not video_path.exists():
        print(f"✗ 影片不存在: {video_path}")
        return
    
    print(f"\n📹 影片: {video_path.name}\n")
    
    # ========== 步驟 1: 語音轉逐字稿 ==========
    print("\n" + "="*70)
    print("【步驟1】語音轉逐字稿")
    print("="*70)
    
    if transcript_json_path is None:
        print("⏳ 正在轉錄...")
        try:
            transcriber = Transcriber()
            # ← 改進：不硬編碼語言，讓 Whisper 自動偵測
            transcript_json = transcriber.transcribe(str(video_path))
        except Exception as e:
            print(f"✗ 轉錄失敗: {e}")
            return
    else:
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
    
    # ========== 步驟 2: 偵測指示詞 ==========
    print("\n" + "="*70)
    print("【步驟2】偵測指示詞")
    print("="*70)
    
    try:
        detector = DeicticDetector()
        deictic_data = detector.detect_from_transcript(transcript_json)
        
        if deictic_data["total_deictic_words"] == 0:
            print("\n⚠️ 未找到指示詞，流程終止")
            return
    except Exception as e:
        print(f"✗ 偵測失敗: {e}")
        return
    
    # ========== 步驟 3: 根據指示詞截幀 ==========
    print("\n" + "="*70)
    print("【步驟3】根據指示詞截幀")
    print("="*70)
    
    try:
        extractor = FrameExtractor()
        frames_result = extractor.extract_frames_from_deictic(str(video_path), deictic_data)
        
        if frames_result["success_frames"] == 0:
            print("\n⚠️ 截幀失敗，流程終止")
            return
        
        print(f"✓ 成功截取 {frames_result['success_frames']} 幀")
    except Exception as e:
        print(f"✗ 截幀失敗: {e}")
        return
    
    # ========== 步驟 4: 視覺分析 ==========
    print("\n" + "="*70)
    print("【步驟4】用 LLaVA/Qwen 分析截幀視覺內容")
    print("="*70)
    print("⏳ 正在分析（可能需要1-2分鐘）...\n")
    
    try:
        analyzer = VisionAnalyzer()
        vision_data = analyzer.analyze_frames_batch(frames_result)
        
        success_count = vision_data["success"]
        if success_count == 0:
            print("\n✗ 視覺分析全部失敗")
            print("\n失敗詳情：")
            for idx, analysis in enumerate(vision_data["analyses"][:3], 1):
                print(f"  [{idx}] {Path(analysis['image_path']).name}")
                print(f"      錯誤: {analysis.get('error', '未知錯誤')}")
            print("\n⚠️ 流程終止")
            return
        
        print(f"\n✓ 成功分析 {success_count} 張圖片")
        
        if vision_data["failed"] > 0:
            print(f"⚠️ 有 {vision_data['failed']} 張圖片分析失敗")
    except Exception as e:
        print(f"✗ 視覺分析失敗: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # ========== 步驟 5: 融合 ==========
    print("\n" + "="*70)
    print("【步驟5】融合：將指示詞替換為視覺描述")
    print("="*70)
    
    try:
        engine = FusionEngine()
        fused_data = engine.fuse(transcript_json, deictic_data, vision_data)
        
        print(f"\n✓ 融合完成")
        print(f"  - 修改段落: {fused_data['modified_segments']}/{fused_data['total_segments']}")
        print(f"  - 總替換數: {fused_data['total_replacements']}")
    except Exception as e:
        print(f"✗ 融合失敗: {e}")
        return
    
    # ========== 輸出結果 ==========
    print("\n" + "="*70)
    print("【結果】保存融合逐字稿")
    print("="*70)
    
    try:
        output_base = video_path.stem
        engine.save_fused_transcript(fused_data, output_base)
        engine.export_as_json(fused_data, f"{output_base}_fusion")
        
        print(f"\n✓ 輸出文件：")
        print(f"  - 文本版: outputs/results/{output_base}.txt")
        print(f"  - JSON版: outputs/results/{output_base}_fusion.json")
    except Exception as e:
        print(f"✗ 保存失敗: {e}")
        return
    
    # ========== 顯示樣本結果 ==========
    print("\n" + "="*70)
    print("【樣本】融合後的逐字稿（前3個修改段落）")
    print("="*70 + "\n")
    
    modified_segments = [s for s in fused_data["segments"] if s["modified"]]
    for idx, segment in enumerate(modified_segments[:3], 1):
        print(f"[{idx}] {segment['time']}")
        print(f"    原文: {segment['original_text'][:70]}...")
        print(f"\n    融合: {segment['text'][:100]}...")
        
        if segment["replacements"]:
            print(f"\n    補充詳情:")
            for repl in segment["replacements"][:2]:
                print(f"      • 「{repl['word']}」← 「{repl['supplement'][:50]}...」")
        
        print()
    
    print("=" * 70)
    print("✓ 完整流程執行完成！")
    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("=" * 70)
        print("完整管線：影片 → 逐字稿 → 指示詞 → 截幀 → 視覺分析 → 融合")
        print("=" * 70)
        print("\n使用方法:")
        print(f"  python tests/test_complete_pipeline.py <影片路徑> [逐字稿JSON]")
        print("\n範例:")
        print(f"  python tests/test_complete_pipeline.py demo_video/video_demo1.mp4")
        print(f"  python tests/test_complete_pipeline.py demo_video/video_demo1.mp4 outputs/transcripts/video_demo1.json")
        print("\n⚠️  首次運行會較慢（需下載模型、分析多張圖片）")
        print("=" * 70)
    else:
        video_file = sys.argv[1]
        transcript_file = sys.argv[2] if len(sys.argv) > 2 else None
        run_complete_pipeline(video_path=video_file, transcript_json_path=transcript_file)
