# -*- coding: utf-8 -*-
"""Phase 1.2 — 向量知识库构建

Embedding 层抽象为可插拔：默认离线 TF-IDF+ SVD（零依赖、无需联网），
设置环境变量 USE_SENTENCE_TRANSFORMERS=1 且能联网时改用 sentence-transformers。

存储：ChromaDB 本地持久化 + behavior_tag -> question_ids 倒排索引。

用法：
    python build_kb.py                 # 全量重建
    python build_kb.py --incremental   # 增量更新
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402
from services.embedder import TfidfEmbedder, SentenceEmbedder  # noqa: E402

EMBEDDER_STATE = os.path.join(config.CHROMA_DIR, "embedder.joblib")


def build_embedder():
    """返回可用的 embedder。默认离线 TF-IDF。"""
    if os.environ.get("USE_SENTENCE_TRANSFORMERS", "0") == "1":
        return SentenceEmbedder(config.EMBEDDING_MODEL)
    return TfidfEmbedder()


class EthicsKnowledgeBase:
    """CFA 道德题库向量知识库"""

    def __init__(self, corpus_path=None, chroma_dir=None, collection=None,
                 embedder=None):
        self.corpus_path = corpus_path or config.CORPUS_PATH
        self.chroma_dir = chroma_dir or config.CHROMA_DIR
        self.collection_name = collection or config.CHROMA_COLLECTION
        self.embedder = embedder or build_embedder()
        self._client = None
        self._collection = None

    # ---------- Embedding ----------
    def fit(self, texts):
        """在语料上拟合 embedder（TF-IDF 需要；sentence-transformers 无需）"""
        self.embedder.fit(texts)

    def embed(self, texts):
        return self.embedder.encode(texts)

    # ---------- ChromaDB ----------
    def _client_(self):
        if self._client is None:
            import chromadb
            os.makedirs(self.chroma_dir, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self.chroma_dir)
        return self._client

    def collection(self):
        if self._collection is None:
            self._collection = self._client_().get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collection

    # ---------- 数据读写 ----------
    @staticmethod
    def load_corpus(path=None):
        path = path or config.CORPUS_PATH
        recs = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    recs.append(json.loads(line))
        return recs

    @staticmethod
    def _doc_text(rec):
        return f"{rec.get('scenario_cn', '')} {rec.get('explanation', '')}".strip()

    @staticmethod
    def _meta(rec):
        def s(x):
            return ",".join(x) if isinstance(x, list) else str(x or "")
        return {
            "question_id": rec["question_id"],
            "module": rec.get("module", ""),
            "standard_code": s(rec.get("standard_code", [])),
            "risk_level": rec.get("risk_level", "low"),
            "behavior_tags": s(rec.get("behavior_tags", [])),
            "required_actions": s(rec.get("required_actions", [])),
            "correct_answer": rec.get("correct_answer", ""),
        }

    # ---------- 核心方法 ----------
    def add_documents(self, records, incremental=False):
        col = self.collection()
        ids, docs, metas = [], [], []

        if incremental:
            existing = set(col.get()["ids"])
            records = [r for r in records if r["question_id"] not in existing]

        if not records:
            print("无新增文档。")
            return 0

        for r in records:
            ids.append(r["question_id"])
            docs.append(self._doc_text(r))
            metas.append(self._meta(r))

        # TF-IDF 需先在全部文档上拟合（含已有文档以保持词表一致）
        all_docs = docs
        if incremental:
            all_docs = [self._doc_text(r) for r in self.load_corpus()]
        self.fit(all_docs)
        embeds = self.embed(docs)

        col.add(ids=ids, documents=docs, metadatas=metas, embeddings=embeds)

        self.embedder.save(EMBEDDER_STATE)
        self._build_inverted_index()
        print(f"已写入 {len(ids)} 条文档到集合 '{self.collection_name}'")
        return len(ids)

    def search(self, query, top_k=None):
        """向量检索相似案例，返回 [{question_id, similarity, ...}]"""
        top_k = top_k or config.RETRIEVAL_TOP_K
        col = self.collection()

        # 查询时若 embedder 未拟合（如 TF-IDF 刚加载），从磁盘恢复
        if getattr(self.embedder, "vectorizer", None) is None and hasattr(self.embedder, "load"):
            if os.path.exists(EMBEDDER_STATE):
                self.embedder.load(EMBEDDER_STATE)

        q_emb = self.embed([query])[0]
        res = col.query(query_embeddings=[q_emb], n_results=top_k,
                        include=["documents", "metadatas", "distances"])
        out = []
        ids = res.get("ids", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]
        docs = (res.get("documents") or [[]])[0]
        for i, qid in enumerate(ids):
            m = metas[i] if i < len(metas) else {}
            d = dists[i] if i < len(dists) else 1.0
            out.append({
                "question_id": qid,
                "similarity": round(1 - float(d), 4),
                "standard_code": (m.get("standard_code") or "").split(","),
                "risk_level": m.get("risk_level", "low"),
                "behavior_tags": (m.get("behavior_tags") or "").split(","),
                "required_actions": (m.get("required_actions") or "").split(","),
                "text": docs[i] if i < len(docs) else "",
            })
        return out

    # ---------- 倒排索引 ----------
    def _build_inverted_index(self):
        col = self.collection()
        data = col.get(include=["metadatas"])
        inv = {}
        for qid, m in zip(data.get("ids", []), data.get("metadatas", [])):
            keys = set()
            keys.update((m.get("behavior_tags") or "").split(","))
            keys.update((m.get("standard_code") or "").split(","))
            keys.update((m.get("risk_level") or "").split(","))
            for k in keys:
                k = k.strip()
                if not k:
                    continue
                inv.setdefault(k, []).append(qid)
        os.makedirs(self.chroma_dir, exist_ok=True)
        with open(config.INVERTED_INDEX_PATH, "w", encoding="utf-8") as f:
            json.dump(inv, f, ensure_ascii=False, indent=2)
        return inv

    def get_by_tag(self, tag):
        if not os.path.exists(config.INVERTED_INDEX_PATH):
            self._build_inverted_index()
        with open(config.INVERTED_INDEX_PATH, encoding="utf-8") as f:
            inv = json.load(f)
        return inv.get(tag, [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--incremental", action="store_true", help="增量更新")
    parser.add_argument("--include-conceptual", action="store_true",
                        help="同时索引无准则代码的概念题（M1/M4 定义题）")
    args = parser.parse_args()

    kb = EthicsKnowledgeBase()
    records = kb.load_corpus()
    if not args.include_conceptual:
        # 仅索引含明确准则代码的合规案例，避免概念题污染行为匹配检索
        records = [r for r in records if r.get("standard_code")]
    print(f"语料共 {len(records)} 题（已过滤概念题）")
    n = kb.add_documents(records, incremental=args.incremental)
    print(f"知识库就绪，本次写入 {n} 条")


if __name__ == "__main__":
    main()
