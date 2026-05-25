"""
回想內容識別模塊 - 使用 Gemini LLM 進行語義分析
支持直接提及和對比提及兩種類型

改用純 LLM 方法的優勢：
- 可以理解隱含的內容（例如「不像之前」時，LLM 知道「之前」是什麼）
- 對比回想不依賴向量相似度，而是依賴語義理解
- 一次性分析全部逐字稿，更準確的上下文
"""

from typing import Dict, List
import json
import google.generativeai as genai


class RecallDetector:
    """回想內容識別類 - 使用 Gemini 3.1 Flash Lite 的純 LLM 分析"""

    def __init__(self):
        """初始化回想偵測器"""
        print("[RecallDetector] 初始化 Gemini API...")
        self.model_name = "gemini-3.1-flash-lite"
        print(f"[RecallDetector] 使用模型: {self.model_name}")


    def detect_recalls(
        self,
        transcript_json: Dict,
        language: str = "en"
    ) -> Dict:
        """
        使用 Gemini LLM 進行回想檢測
        
        Args:
            transcript_json: 逐字稿 JSON，結構應包含 segments 列表
                每個 segment 有: text, start, end, time 等字段
            language: "zh" 或 "en"
        
        Returns:
            dict: 
                {
                    "recalls": [
                        {
                            "segment_idx": int,
                            "recall_type": "direct" | "contrast",
                            "recall_cue": str,
                            "current_text": str,
                            "recalled_segment_idx": int,
                            "recalled_text": str,
                            "position_in_segment_ratio": float (0.0-1.0),
                            "confidence": float (0-1),
                            "reasoning": str
                        },
                        ...
                    ]
                }
        """
        segments = transcript_json.get("segments", [])
        
        if not segments:
            print("[RecallDetector] 沒有 segments，返回空結果")
            return {"recalls": []}
        
        print(f"\n[RecallDetector] 開始分析 {len(segments)} 個段落的回想內容...")
        
        # 建立逐字稿字符串供 LLM 分析
        transcript_text = self._build_transcript_for_analysis(segments)
        
        # 調用 LLM
        recalls = self._analyze_with_llm(
            transcript_text=transcript_text,
            segments=segments,
            language=language
        )
        
        print(f"[RecallDetector] 分析完成，共找到 {len(recalls)} 個回想內容")
        return {"recalls": recalls}

    
    def _build_transcript_for_analysis(self, segments: List[Dict]) -> str:
        """
        建立適合 LLM 分析的逐字稿格式
        
        格式：
        [Segment 0] (0:00-0:05)
        Text: "This is the first point..."
        
        [Segment 1] (0:05-0:12)
        Text: "And here we discuss..."
        """
        lines = []
        for idx, seg in enumerate(segments):
            time_range = seg.get("time", f"{seg.get('start', 0):.1f}s")
            text = seg.get("text", "")
            lines.append(f"[Segment {idx}] {time_range}\nText: {text}\n")
        
        return "\n".join(lines)
    
    def _analyze_with_llm(
        self,
        transcript_text: str,
        segments: List[Dict],
        language: str
    ) -> List[Dict]:
        """
        使用 Gemini 進行 LLM 分析，輸出結構化的回想信息
        """
        
        # 構建 LLM 提示詞
        if language == "zh":
            prompt = self._build_chinese_prompt(transcript_text, segments)
        else:
            prompt = self._build_english_prompt(transcript_text, segments)
        
        try:
            print("[RecallDetector] 調用 Gemini API...")
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(prompt)
            response_text = response.text
            print("[RecallDetector] API 返回成功")
            
            # 解析 JSON 輸出（傳入 language 用於過濾）
            recalls = self._parse_llm_response(response_text, segments, language)
            return recalls
            
        except Exception as e:
            print(f"[RecallDetector] ❌ LLM 分析失敗: {e}")
            return []
    
    def _build_chinese_prompt(self, transcript_text: str, segments: List[Dict]) -> str:
        """構建中文提示詞"""
        return f"""你是一個影片分析專家。請分析以下逐字稿，找出所有的「回想」現象。

回想是指說話者明確提及或隱含參考之前提到過的內容。分為兩種類型：

1. **直接提及 (direct)**：
   - 明確提到過去內容的時刻或語詞
   - 例如：「如我之前所說」、「剛才我們討論過」、「還記得那個例子嗎」
   - 特徵：通常用「之前」「剛才」「前面」「之前提到」等詞

2. **對比提及 (contrast)**：
   - 將當前內容與過去內容作比較
   - 例如：「不像之前那樣」、「與前面不同」、「相反地」
   - 特徵：涉及對立、對比、差異的邏輯

### 逐字稿：
{transcript_text}

### 輸出要求：

請以 JSON 格式輸出結果，只輸出 JSON，不要其他文字。格式如下：

```json
{{
  "recalls": [
    {{
      "segment_idx": <當前 segment 索引>,
      "recall_type": "direct" 或 "contrast",
      "recall_cue": "<觸發詞，例如：'如我之前所說'、'不像之前'>",
      "current_text": "<當前 segment 的完整文本>",
      "recalled_segment_idx": <被回想的過去 segment 索引>,
      "recalled_text": "<過去 segment 的完整文本>",
      "position_in_segment_ratio": <回想觸發的位置，範圍 0.0-1.0，代表在 segment 內的百分比位置>,
      "confidence": <置信度 0.0-1.0，1.0 表示非常確定>,
      "reasoning": "<為什麼認為這是回想，解釋 segment_idx 和 recalled_segment_idx 的關係>"
    }},
    ...
  ]
}}
```

### 重要注意：
- position_in_segment_ratio 應該基於觸發詞在 segment 中的位置百分比
- 只包含明確的或強烈暗示的回想，不要包含模糊的可能性
- 如果沒有找到回想，返回空列表
- recall_cue 應該是段落中實際出現的詞彙或短語
"""

    def _build_english_prompt(self, transcript_text: str, segments: List[Dict]) -> str:
        """構建英文提示詞"""
        return f"""You are an expert video analyst. Your task is to identify ONLY EXPLICIT and UNMISTAKABLE recalls in this transcript.

STRICT CRITERIA FOR RECALLS:

1. **Direct Recall** (Only if speaker EXPLICITLY references a previous point):
   - Must contain explicit reference phrases: "earlier", "before", "previously", "as I said", "when I mentioned", "remember when", "as we discussed"
   - Example: Segment says "unlike what I said before" → must be found in an earlier segment
   - EXCLUDE: Generic references or coincidental word repetition
   
2. **Contrast Recall** (Only if speaker EXPLICITLY compares with past):
   - Must contain comparison phrases: "unlike", "unlike before", "different from", "contrary to", "not like", "opposite of"
   - Must explicitly connect current to a past statement
   - EXCLUDE: Different topics that just share vocabulary

WHAT NOT TO REPORT:
- ❌ Just because words appear in multiple segments (e.g., "region" appears twice doesn't mean recall)
- ❌ Topic continuation (e.g., discussing speed signs at two different times)
- ❌ General references without explicit "before/previously/earlier" markers
- ❌ Vague semantic connections

### Transcript:
{transcript_text}

### Output Requirements:

Output ONLY valid JSON (no other text):

```json
{{
  "recalls": [
    {{
      "segment_idx": <current segment index (the one doing the recalling)>,
      "recall_type": "direct" or "contrast",
      "recall_cue": "<EXACT phrase from segment showing the recall, e.g., 'as mentioned earlier'>",
      "current_text": "<full text of current segment>",
      "recalled_segment_idx": <index of past segment being referenced (must be < segment_idx)>,
      "recalled_text": "<full text of past segment>",
      "position_in_segment_ratio": <0.0-1.0 where recall phrase appears in segment>,
      "confidence": <0.0-1.0: only 0.8+ for explicit recalls with clear markers>,
      "reasoning": "<WHY this is a recall: show the explicit connection>"
    }},
    ...
  ]
}}
```

### Critical Instructions:
- ONLY report recalls with confidence >= 0.8 if explicit marker phrases are present
- If confidence would be < 0.8, DO NOT include it
- Return empty list if no clear recalls found
- recall_cue MUST be actual text from the segment containing the recall indicator
"""

    def _parse_llm_response(self, response_text: str, segments: List[Dict], language: str = "en") -> List[Dict]:
        """
        解析 LLM 返回的 JSON 結果
        
        Args:
            response_text: LLM 返回的文本
            segments: 逐字稿段落
            language: 語言 ("zh" 或 "en")，用於決定過濾閾值
        """
        try:
            # 試著找到 JSON 塊
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end <= json_start:
                print("[RecallDetector] ⚠️  無法在返回中找到 JSON")
                return []
            
            json_str = response_text[json_start:json_end]
            data = json.loads(json_str)
            
            recalls = data.get("recalls", [])
            
            # 驗證和清理結果
            cleaned_recalls = []
            for recall in recalls:
                try:
                    # 確保所有必要字段存在
                    if not all(k in recall for k in [
                        "segment_idx", "recall_type", "recall_cue",
                        "current_text", "recalled_segment_idx", "recalled_text",
                        "position_in_segment_ratio", "confidence", "reasoning"
                    ]):
                        continue
                    
                    # 驗證索引
                    seg_idx = int(recall["segment_idx"])
                    rec_seg_idx = int(recall["recalled_segment_idx"])
                    
                    if not (0 <= seg_idx < len(segments) and 0 <= rec_seg_idx < len(segments)):
                        continue
                    
                    if seg_idx <= rec_seg_idx:
                        continue  # 回想應該是引用過去的內容
                    
                    # 規範化比例
                    ratio = float(recall.get("position_in_segment_ratio", 0.5))
                    ratio = max(0.0, min(1.0, ratio))
                    
                    # 規範化置信度
                    confidence = float(recall.get("confidence", 0.5))
                    confidence = max(0.0, min(1.0, confidence))
                    
                    # ← 新增：英文視頻置信度過濾（只接受置信度 >= 0.75 的 recall）
                    # 英文視頻的 Gemini 誤判率較高，需要更嚴格的閾值
                    if language == "en" and confidence < 0.75:
                        print(f"[RecallDetector] 跳過低置信度 recall (conf={confidence:.1%}): {recall.get('recall_cue')}")
                        continue
                    
                    cleaned_recalls.append({
                        "segment_idx": seg_idx,
                        "recall_type": recall.get("recall_type", "direct"),
                        "recall_cue": str(recall.get("recall_cue", "")),
                        "current_text": str(recall.get("current_text", "")),
                        "recalled_segment_idx": rec_seg_idx,
                        "recalled_text": str(recall.get("recalled_text", "")),
                        "position_in_segment_ratio": ratio,
                        "confidence": confidence,
                        "reasoning": str(recall.get("reasoning", ""))
                    })
                    
                    print(
                        f"[RecallDetector] ✓ {recall.get('recall_type')} recall: "
                        f"seg {seg_idx} ('{recall.get('recall_cue')}') → seg {rec_seg_idx} "
                        f"(conf: {confidence:.1%})"
                    )
                except (ValueError, KeyError, TypeError) as e:
                    print(f"[RecallDetector] ⚠️  跳過無效記錄: {e}")
                    continue
            
            return cleaned_recalls
            
        except json.JSONDecodeError as e:
            print(f"[RecallDetector] ❌ JSON 解析失敗: {e}")
            print(f"[RecallDetector] 返回內容: {response_text[:200]}...")
            return []

