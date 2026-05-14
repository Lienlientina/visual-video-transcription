#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試改進的簡潔視覺分析
"""

import json
from pathlib import Path
from modules.vision_analyzer import VisionAnalyzer

def test_concise_vision():
    """測試簡潔的視覺分析"""
    
    # 初始化分析器
    analyzer = VisionAnalyzer()
    
    # 讀取融合結果中的指示詞信息
    fusion_data_path = Path("outputs/results/video_demo1_fusion.json")
    
    if not fusion_data_path.exists():
        print("❌ 未找到融合數據，請先運行完整管線")
        return
    
    with open(fusion_data_path, 'r', encoding='utf-8') as f:
        fusion_data = json.load(f)
    
    print("\n" + "=" * 70)
    print("【改進視覺分析測試】- 專注於指示詞的簡潔描述")
    print("=" * 70)
    
    frames_dir = Path("outputs/frames")
    test_count = 0
    
    # 遍歷所有段落，找出有指示詞的部分
    for segment in fusion_data.get("segments", []):
        replacements = segment.get("replacements", [])
        if not replacements:
            continue
        
        timestamp = segment.get("time", "")
        
        # 轉換時間戳為文件名格式 [0:MM:SS] -> 0_MM_SS.jpg
        timestamp_clean = timestamp.strip("[]").replace(":", "_")
        frame_path = frames_dir / f"{timestamp_clean}.jpg"
        
        if not frame_path.exists():
            continue
        
        for replacement in replacements:
            test_count += 1
            word = replacement.get("word", "")
            context = segment.get("original_text", "")[:60]  # 簡短上下文
            
            print(f"\n【測試 {test_count}】")
            print(f"  時間: {timestamp}")
            print(f"  指示詞: 「{word}」")
            print(f"  上下文: {context}...")
            print(f"  圖片: {frame_path.name}")
            print("-" * 70)
            
            result = analyzer.analyze_image(str(frame_path), context, word)
            
            if result.get("success"):
                desc = result.get("description", "")
                # 顯示前 200 個字符
                display_desc = desc[:200] + "..." if len(desc) > 200 else desc
                print(f"✓ 分析結果 ({len(desc)} 字):")
                print(display_desc)
            else:
                print(f"❌ 分析失敗: {result.get('error', '未知錯誤')}")
    
    print("\n" + "=" * 70)
    print(f"✓ 測試完成: 共分析 {test_count} 個指示詞")
    print("=" * 70)
    print("\n💡 預期改進:")
    print("  • 描述應該很簡潔 (1-3 句)")
    print("  • 只提及指示詞相關的部分")
    print("  • 不應該有詳細的 5 點分析格式")

if __name__ == "__main__":
    test_concise_vision()

