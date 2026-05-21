"""
回想內容識別模塊 - 使用語義搜索找出被引用的過去內容
支持直接提及和對比提及兩種類型
"""

from typing import Dict, List, Tuple
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError("sentence-transformers 未安裝，請執行: pip install sentence-transformers")


RECALL_TYPES = {
    "zh": {
        "direct": [
            "如我所說", "正如我說過", "我之前提到", "剛剛", "剛才",
            "前面", "之前", "前文", "我們說過", "上面提到", "基本上",
            "換句話說", "簡單來說", "另外", "延伸", "進一步"
        ],
        "contrast": ["不同於", "不一樣", "相反地", "相反", "不同"],  # 改用更靈活的匹配
    },
    "en": {
        "direct": [
            "as I said", "as I mentioned", "like I said", "earlier",
            "previously", "we talked about", "remember when", "recall",
            "we discussed", "mentioned earlier", "as we discussed", "as discussed", "mentioned"
        ],
        "contrast": ["unlike", "contrary to", "opposite of", "different from"],
    }
}


class RecallDetector:
    """回想內容識別類 - 使用語義搜索"""

    def __init__(self):
        """初始化回想偵測器"""
        print("[RecallDetector] 加載語義模型（all-MiniLM-L6-v2）...")
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        print("[RecallDetector] 語義模型加載完成 ✓")

    def detect_recalls(
        self,
        transcript_json: Dict,
        language: str = "en",
        similarity_threshold: float = 0.7
    ) -> Dict:
        """
        簡化版回想偵測：只有 direct 和 contrast 兩種類型

        Args:
            transcript_json: 逐字稿 JSON
            language: "zh" 或 "en"
            similarity_threshold: 相似度門檻 (0-1)

        Returns:
            dict: 
                {
                    "total_recalls": 5,
                    "recalls": [
                        {
                            "segment_idx": 15,
                            "recall_word": "as I mentioned",
                            "recall_type": "direct" 或 "contrast",
                            "recalled_segment_idx": 3,
                            "recalled_text": "if player equals computer",
                            "recalled_time": "[0:00:18]",
                            "similarity_score": 0.82
                        },
                        ...
                    ]
                }
        """
        segments = transcript_json.get("segments", [])
        all_texts = [s["text"] for s in segments]

        print(f"\n[RecallDetector] 開始向量化 {len(segments)} 個段落...")
        all_embeddings = self.embed_model.encode(all_texts, show_progress_bar=False)
        print(f"[RecallDetector] 向量化完成")

        recalls = []

        for idx, segment in enumerate(segments):
            current_text = segment["text"]

            # 偵測回想詞 + 類型
            recall_word, recall_type = self._detect_recall_word_with_type(
                current_text, language
            )
            if not recall_word:
                continue

            # 提取核心內容（去掉回想詞）
            core_content = self._extract_core_content(
                current_text, recall_word, language
            )

            # 向量化核心內容
            core_embedding = self.embed_model.encode([core_content])[0]

            # 在過去段落中搜索
            past_embeddings = all_embeddings[:idx]

            if len(past_embeddings) == 0:
                continue

            similarities = np.dot(past_embeddings, core_embedding)

            # 根據類型使用不同的搜索策略
            if recall_type == "direct":
                # 直接提及：找最相似的
                best_idx = np.argmax(similarities)
                best_score = similarities[best_idx]

                if best_score > similarity_threshold:
                    current_seg_time = segment.get("time", "[?]")
                    current_start = segment.get("start", 0)
                    current_end = segment.get("end", 0)
                    recalled_seg_time = segments[best_idx].get("time", "[?]")
                    recalled_start = segments[best_idx].get("start", 0)
                    recalled_end = segments[best_idx].get("end", 0)
                    
                    recalls.append(
                        {
                            "segment_idx": int(idx),
                            "segment_time": current_seg_time,
                            "segment_time_range": f"{current_start:.2f}s-{current_end:.2f}s",
                            "recall_word": recall_word,
                            "recall_type": "direct",
                            "recalled_segment_idx": int(best_idx),
                            "recalled_text": segments[best_idx]["text"][:50],
                            "recalled_time": recalled_seg_time,
                            "recalled_time_range": f"{recalled_start:.2f}s-{recalled_end:.2f}s",
                            "similarity_score": float(best_score),
                        }
                    )
                    print(
                        f"[RecallDetector] ✓ 直接提及: 段落{idx}{current_seg_time}({current_start:.2f}~{current_end:.2f}s)『{recall_word}』 → 段落{best_idx}{recalled_seg_time}({recalled_start:.2f}~{recalled_end:.2f}s) (相似度: {best_score:.2f})"
                    )

            elif recall_type == "contrast":
                # 對比提及：找「相反」的內容（相似度中等）
                # 策略：相似度在 0.3-0.7 之間的內容
                valid_mask = (similarities > 0.3) & (similarities < 0.7)
                valid_indices = np.where(valid_mask)[0]

                if len(valid_indices) > 0:
                    # 在有效範圍內找最接近 0.5 的（最相反）
                    distances_to_mid = np.abs(similarities[valid_indices] - 0.5)
                    best_in_valid = valid_indices[np.argmin(distances_to_mid)]
                    best_score = similarities[best_in_valid]

                    current_seg_time = segment.get("time", "[?]")
                    current_start = segment.get("start", 0)
                    current_end = segment.get("end", 0)
                    recalled_seg_time = segments[best_in_valid].get("time", "[?]")
                    recalled_start = segments[best_in_valid].get("start", 0)
                    recalled_end = segments[best_in_valid].get("end", 0)

                    recalls.append(
                        {
                            "segment_idx": int(idx),
                            "segment_time": current_seg_time,
                            "segment_time_range": f"{current_start:.2f}s-{current_end:.2f}s",
                            "recall_word": recall_word,
                            "recall_type": "contrast",
                            "recalled_segment_idx": int(best_in_valid),
                            "recalled_text": segments[best_in_valid]["text"][:50],
                            "recalled_time": recalled_seg_time,
                            "recalled_time_range": f"{recalled_start:.2f}s-{recalled_end:.2f}s",
                            "similarity_score": float(best_score),
                            "contrast_marker": "↔",
                        }
                    )
                    print(
                        f"[RecallDetector] ↔ 對比提及: 段落{idx}{current_seg_time}({current_start:.2f}~{current_end:.2f}s) ↔ 段落{best_in_valid}{recalled_seg_time}({recalled_start:.2f}~{recalled_end:.2f}s)『{recall_word}』 (相似度: {best_score:.2f})"
                    )

        print(f"\n[RecallDetector] 偵測完成，共找到 {len(recalls)} 個回想內容")
        return {"total_recalls": len(recalls), "recalls": recalls}

    def _detect_recall_word_with_type(
        self, text: str, language: str
    ) -> Tuple[str, str]:
        """偵測回想詞並分類為 direct 或 contrast"""
        recall_types = RECALL_TYPES.get(language, RECALL_TYPES["en"])

        # 先檢查 contrast（因為更specific）
        for pattern in recall_types.get("contrast", []):
            if pattern.lower() in text.lower():
                return pattern, "contrast"

        # 再檢查 direct
        for pattern in recall_types.get("direct", []):
            if pattern.lower() in text.lower():
                return pattern, "direct"

        return None, None

    def _extract_core_content(
        self, text: str, recall_word: str, language: str
    ) -> str:
        """
        從包含回想詞的句子中提取核心內容

        例子：
        「as I mentioned earlier, this is important」
        ↓
        「this is important」
        """
        # 找到回想詞的位置
        recall_pos = text.lower().find(recall_word.lower())

        if recall_pos == -1:
            return text  # 沒找到，返回原文

        # 回想詞後面是什麼？
        after_recall = text[recall_pos + len(recall_word) :]

        # 清除前導標點
        core_content = after_recall.lstrip(" ,，：;；").strip()

        # 如果只剩下很短的內容，返回原句
        if len(core_content) < 5:
            return text

        return core_content
