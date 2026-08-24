# -*- coding: utf-8 -*-
"""Embedding 抽象层

优先使用 sentence-transformers（需联网下载模型）；网络不可用时回退到
离线 TF-IDF（字符 n-gram）+ SVD 降维方案，保证零依赖可运行。
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config  # noqa: E402


class TfidfEmbedder:
    """离线 Embedder：jieba 分词 + 词级/字符 n-gram TF-IDF + SVD 降维"""

    def __init__(self, dim=128):
        self.dim = dim
        self.vectorizer = None
        self.svd = None

    @staticmethod
    def _tok(text):
        import jieba
        words = [w.strip() for w in jieba.cut(text) if w.strip()]
        # 补充字符 bigram，提升对未登录词/中英混合的覆盖
        chars = [c for c in text if not c.isspace()]
        bigrams = ["".join(chars[i:i + 2]) for i in range(len(chars) - 1)]
        return " ".join(words + bigrams)

    def fit(self, texts):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD
        self.vectorizer = TfidfVectorizer(
            analyzer="word", ngram_range=(1, 2),
            min_df=2, max_features=30000,
        )
        X = self.vectorizer.fit_transform([self._tok(t) for t in texts])
        self.svd = TruncatedSVD(n_components=min(self.dim, X.shape[1] - 1))
        self.svd.fit(X)
        return self

    def encode(self, texts):
        if self.vectorizer is None:
            raise RuntimeError("TfidfEmbedder 未 fit")
        X = self.vectorizer.transform([self._tok(t) for t in texts])
        v = self.svd.transform(X)
        norm = np.linalg.norm(v, axis=1, keepdims=True)
        norm[norm == 0] = 1
        return (v / norm).tolist()

    def save(self, path):
        import joblib
        joblib.dump({"vectorizer": self.vectorizer, "svd": self.svd}, path)

    def load(self, path):
        import joblib
        data = joblib.load(path)
        self.vectorizer = data["vectorizer"]
        self.svd = data["svd"]
        return self


class SentenceEmbedder:
    """sentence-transformers Embedder（联网可用）"""

    def __init__(self, model_name=None):
        self.model_name = model_name or config.EMBEDDING_MODEL
        self.model = None

    def fit(self, texts):
        # 预训练模型无需 fit
        return self

    def encode(self, texts):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
        vecs = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return [v.tolist() for v in vecs]

    def save(self, path):
        # 模型权重在 HF 缓存，这里只记录模型名
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_name)

    def load(self, path):
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self.model_name = f.read().strip() or self.model_name
        return self


def create_embedder(force_offline=False):
    """工厂：返回可用的 embedder。默认尝试 sentence-transformers，失败则回退 TF-IDF"""
    if not force_offline:
        try:
            from sentence_transformers import SentenceTransformer  # noqa: F401
            # 仅当模型已缓存或能联网时才真正可用；这里先返回，真正加载时再判断
            return SentenceEmbedder(), False
        except Exception:
            pass
    return TfidfEmbedder(), True
