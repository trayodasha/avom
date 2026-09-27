import math
import re
from typing import List, Dict, Any, Tuple


class BM25Index:
    """
    Okapi BM25 implementation for lexical sparse retrieval across indexed chunks.
    Formula:
        IDF(q_i) = ln((N - n(q_i) + 0.5) / (n(q_i) + 0.5) + 1)
        Score(D, Q) = sum(IDF(q_i) * (f(q_i, D) * (k1 + 1)) / (f(q_i, D) + k1 * (1 - b + b * (|D| / avgdl))))
    """
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus_size: int = 0
        self.avg_doc_len: float = 0.0
        self.doc_lens: Dict[str, int] = {}
        self.doc_freqs: Dict[str, int] = {}
        self.term_freqs: Dict[str, Dict[str, int]] = {}
        self.doc_metadata: Dict[str, Dict[str, Any]] = {}

    def _tokenize(self, text: str) -> List[str]:
        # Lowercase alphanumeric word tokenization
        tokens = re.findall(r'\b[a-zA-Z0-9_-]+\b', text.lower())
        return tokens

    def index_documents(self, documents: List[Dict[str, Any]]) -> None:
        """
        Index a list of documents/chunks.
        Each doc must have: {"id": str, "text": str, "metadata": dict}
        """
        self.corpus_size = len(documents)
        total_len = 0
        self.doc_lens.clear()
        self.doc_freqs.clear()
        self.term_freqs.clear()
        self.doc_metadata.clear()

        for doc in documents:
            doc_id = doc["id"]
            text = doc.get("text", "")
            tokens = self._tokenize(text)
            doc_len = len(tokens)
            self.doc_lens[doc_id] = doc_len
            total_len += doc_len
            self.doc_metadata[doc_id] = doc

            tf: Dict[str, int] = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self.term_freqs[doc_id] = tf

            for t in tf.keys():
                self.doc_freqs[t] = self.doc_freqs.get(t, 0) + 1

        self.avg_doc_len = (total_len / self.corpus_size) if self.corpus_size > 0 else 0.0

    def _compute_idf(self, term: str) -> float:
        n = self.doc_freqs.get(term, 0)
        return math.log(((self.corpus_size - n + 0.5) / (n + 0.5)) + 1.0)

    def search(self, query: str, top_k: int = 20) -> List[Tuple[str, float]]:
        if self.corpus_size == 0:
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        scores: Dict[str, float] = {}

        for doc_id, tf_map in self.term_freqs.items():
            score = 0.0
            doc_len = self.doc_lens[doc_id]
            len_norm = 1.0 - self.b + self.b * (doc_len / self.avg_doc_len) if self.avg_doc_len > 0 else 1.0

            for q in query_tokens:
                if q not in tf_map:
                    continue
                tf = tf_map[q]
                idf = self._compute_idf(q)
                numerator = tf * (self.k1 + 1.0)
                denominator = tf + self.k1 * len_norm
                score += idf * (numerator / denominator)

            if score > 0:
                scores[doc_id] = score

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]
