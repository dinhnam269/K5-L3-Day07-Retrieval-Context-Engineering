"""Retrieval methods and context engineering for Day 7.

Connects to Day 6 embedding model (models/gemini-embedding-001, 3072 dims)
and Day 6 PostgreSQL + pgvector store (or synced Day 6 vector cache when running
in standard library mode).

Implements:
1. TF-IDF Lexical Retrieval (Baseline)
2. Okapi BM25 Lexical Retrieval
3. Dense Retrieval (Day 6 gemini-embedding-001 3072-d vectors)
4. Hybrid Retrieval (Reciprocal Rank Fusion of Dense + BM25)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR / "starter") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "starter"))

from baseline import TfidfIndex, hit, pack_context, tokenize, validate


def load_env_file(env_path: Path | None = None) -> None:
    """Load simple KEY=VALUE lines from .env without requiring python-dotenv."""
    candidates = [env_path] if env_path else [
        ROOT_DIR / ".env",
        Path("/Users/mac/K5-L3B-DAY06-NguyenDinhNam-2A202603797-DataIngestion/starter/.env"),
    ]
    for path in candidates:
        if path and path.exists():
            for raw_line in path.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip("'").strip('"')
                if k and k not in os.environ:
                    os.environ[k] = v
            break


STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "in", "on", "at", "to", "for", "of", "with", "by", "from", "as", "into",
    "and", "or", "but", "if", "when", "what", "why", "how", "who", "which",
    "where", "did", "does", "do", "had", "has", "have", "that", "this",
    "his", "her", "their", "its", "he", "she", "they", "it", "him", "them",
}


def tokenize_bm25(text: str) -> list[str]:
    tokens = tokenize(text)
    filtered = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    return filtered if filtered else tokens


class BM25Index:
    """Okapi BM25 lexical retriever with stopword removal."""

    def __init__(self, chunks: list[dict[str, Any]], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self.doc_tokens = [tokenize_bm25(c["text"]) for c in chunks]
        self.doc_lens = [len(tokens) for tokens in self.doc_tokens]
        self.avgdl = (sum(self.doc_lens) / len(self.doc_lens)) if self.doc_lens else 1.0
        self.tf = [Counter(tokens) for tokens in self.doc_tokens]
        df = Counter(term for row in self.tf for term in row)
        n_docs = len(chunks)
        self.idf = {
            term: math.log(1.0 + (n_docs - freq + 0.5) / (freq + 0.5))
            for term, freq in df.items()
        }

    def search(
        self,
        question: str,
        top_k: int = 3,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        q_terms = tokenize_bm25(question)
        results: list[dict[str, Any]] = []
        for chunk, tf_row, dl in zip(self.chunks, self.tf, self.doc_lens):
            if not _match_filters(chunk, filters):
                continue
            score = 0.0
            for term in q_terms:
                if term not in tf_row:
                    continue
                freq = tf_row[term]
                idf = self.idf.get(term, 0.0)
                denom = freq + self.k1 * (1.0 - self.b + self.b * (dl / self.avgdl))
                score += idf * (freq * (self.k1 + 1.0)) / denom
            if score > 0:
                results.append({**chunk, "score": round(float(score), 6), "strategy": "bm25"})
        return sorted(results, key=lambda c: (-c["score"], c["id"]))[:top_k]


def _match_filters(chunk: dict[str, Any], filters: dict[str, Any] | None) -> bool:
    if not filters:
        return True
    meta = chunk.get("metadata") or {}
    for k, v in filters.items():
        if v is None:
            continue
        if k in ("source_id", "source", "page"):
            if chunk.get(k) != v:
                return False
        elif meta.get(k) != v:
            return False
    return True


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class Day6DenseIndex:
    """Dense retriever using Day 6 Gemini embeddings (models/gemini-embedding-001, 3072-d).

    Supports querying PostgreSQL + pgvector directly when psycopg is installed
    and the Day 6 database is reachable, and uses the verified Day 6 embedding
    cache + Gemini Embedding API for 100% consistent cosine similarity scoring.
    """

    EMBEDDING_MODEL = "models/gemini-embedding-001"
    CACHE_PREFIX = "gemini:gemini-embedding-001:"

    def __init__(
        self,
        chunks: list[dict[str, Any]],
        cache_path: Path | None = None,
        use_pgvector: bool = True,
        pg_strategy: str = "C",
    ):
        load_env_file()
        self.chunks = chunks
        self.pg_strategy = pg_strategy
        self.use_pgvector = use_pgvector
        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://day6:day6_local_only@127.0.0.1:55433/day6_lab",
        )
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.cache_path = cache_path or (ROOT_DIR / "starter" / "data" / "converted" / ".embedding_cache.json")
        self.cache: dict[str, list[float]] = {}
        if self.cache_path.exists():
            self.cache = json.loads(self.cache_path.read_text(encoding="utf-8"))
        self.api_calls = 0

        # Pre-bind chunk vectors from Day 6 embedding cache
        self.chunk_vectors: list[list[float]] = []
        for c in self.chunks:
            vec = self.embed_text(c["text"])
            self.chunk_vectors.append(vec)

    def _cache_key(self, text: str) -> str:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        return f"{self.CACHE_PREFIX}{digest}"

    def embed_text(self, text: str) -> list[float]:
        key = self._cache_key(text)
        if key in self.cache:
            return self.cache[key]
        if not self.api_key:
            raise RuntimeError(
                f"Query chưa có trong embedding cache và thiếu GEMINI_API_KEY để gọi {self.EMBEDDING_MODEL}."
            )
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/"
            f"{self.EMBEDDING_MODEL}:batchEmbedContents?key={self.api_key}"
        )
        payload = json.dumps({
            "requests": [
                {
                    "model": self.EMBEDDING_MODEL,
                    "content": {"parts": [{"text": text}]},
                }
            ]
        }).encode("utf-8")
        for attempt in range(5):
            try:
                req = urllib.request.Request(
                    url,
                    data=payload,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=60) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as e:
                body = e.read().decode("utf-8", errors="replace")
                if e.code in (429, 500, 503) and attempt < 4:
                    m = re.search(r"retry in ([0-9.]+)s", body, re.IGNORECASE)
                    wait_sec = float(m.group(1)) + 2.0 if m else 15.0 * (attempt + 1)
                    time.sleep(min(wait_sec, 45.0))
                    continue
                raise RuntimeError(f"Gemini embedding HTTP {e.code}: {body[:300]}") from e
        else:
            raise RuntimeError("Exceeded retry attempts for Gemini embedding API")
        vec = [float(x) for x in data["embeddings"][0]["values"]]
        self.cache[key] = vec
        self.api_calls += 1
        try:
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)
            self.cache_path.write_text(json.dumps(self.cache), encoding="utf-8")
        except OSError:
            pass
        return vec

    def _search_pgvector(
        self,
        query_vec: list[float],
        top_k: int,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]] | None:
        if not self.use_pgvector:
            return None
        try:
            import psycopg  # type: ignore
        except ImportError:
            return None
        vec_literal = "[" + ",".join(f"{float(x):.8f}" for x in query_vec) + "]"
        where_clauses = ["strategy = %s"]
        params: list[Any] = [self.pg_strategy]
        if filters and filters.get("section"):
            where_clauses.append("section = %s")
            params.append(filters["section"])
        where_sql = " AND ".join(where_clauses)
        sql = f"""
            SELECT
                chunk_id AS id,
                text,
                document_id AS source_id,
                source,
                page,
                metadata,
                1 - (embedding <=> %s::vector) AS score
            FROM document_chunks
            WHERE {where_sql}
            ORDER BY embedding <=> %s::vector ASC
            LIMIT %s;
        """
        full_params = [vec_literal] + params + [vec_literal, top_k]
        try:
            hits: list[dict[str, Any]] = []
            with psycopg.connect(self.database_url, connect_timeout=3) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, full_params)
                    for row in cur.fetchall():
                        cid, text, source_id, source, page, metadata, score = row
                        hits.append({
                            "id": cid,
                            "text": text,
                            "source_id": source_id,
                            "source": source,
                            "page": int(page),
                            "metadata": metadata if isinstance(metadata, dict) else json.loads(metadata),
                            "score": round(float(score), 6),
                            "strategy": "dense_pgvector",
                        })
            return hits
        except Exception:
            return None

    def search(
        self,
        question: str,
        top_k: int = 3,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        query_vec = self.embed_text(question)
        pg_hits = self._search_pgvector(query_vec, top_k=top_k, filters=filters)
        if pg_hits is not None:
            return pg_hits

        results: list[dict[str, Any]] = []
        for chunk, chunk_vec in zip(self.chunks, self.chunk_vectors):
            if not _match_filters(chunk, filters):
                continue
            score = _cosine_similarity(query_vec, chunk_vec)
            results.append({**chunk, "score": round(float(score), 6), "strategy": "dense"})
        return sorted(results, key=lambda c: (-c["score"], c["id"]))[:top_k]


class HybridRRFIndex:
    """Hybrid retriever combining Dense (Day 6) and Lexical (BM25) via Reciprocal Rank Fusion."""

    def __init__(
        self,
        dense_index: Day6DenseIndex,
        lexical_index: BM25Index | TfidfIndex,
        rrf_k: int = 60,
        candidate_pool: int = 20,
        dense_weight: float = 1.2,
        lexical_weight: float = 1.0,
    ):
        self.dense_index = dense_index
        self.lexical_index = lexical_index
        self.rrf_k = rrf_k
        self.candidate_pool = candidate_pool
        self.dense_weight = dense_weight
        self.lexical_weight = lexical_weight

    def search(
        self,
        question: str,
        top_k: int = 3,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        dense_hits = self.dense_index.search(question, top_k=self.candidate_pool, filters=filters)
        if isinstance(self.lexical_index, BM25Index):
            lex_hits = self.lexical_index.search(question, top_k=self.candidate_pool, filters=filters)
        else:
            raw_lex = self.lexical_index.search(question, top_k=self.candidate_pool)
            lex_hits = [c for c in raw_lex if _match_filters(c, filters)]

        fused_scores: dict[str, float] = {}
        chunk_map: dict[str, dict[str, Any]] = {}
        rank_info: dict[str, dict[str, Any]] = {}

        for rank, c in enumerate(dense_hits, start=1):
            cid = c["id"]
            chunk_map[cid] = c
            fused_scores[cid] = fused_scores.get(cid, 0.0) + self.dense_weight * (1.0 / (self.rrf_k + rank))
            rank_info.setdefault(cid, {})["dense_rank"] = rank
            rank_info[cid]["dense_score"] = c["score"]

        for rank, c in enumerate(lex_hits, start=1):
            cid = c["id"]
            chunk_map[cid] = c
            fused_scores[cid] = fused_scores.get(cid, 0.0) + self.lexical_weight * (1.0 / (self.rrf_k + rank))
            rank_info.setdefault(cid, {})["lexical_rank"] = rank
            rank_info[cid]["lexical_score"] = c["score"]

        results: list[dict[str, Any]] = []
        for cid, score in fused_scores.items():
            base_chunk = {k: v for k, v in chunk_map[cid].items() if k not in ("score", "strategy")}
            results.append({
                **base_chunk,
                "score": round(float(score), 6),
                "strategy": "hybrid_rrf",
                "fusion_detail": rank_info[cid],
            })
        return sorted(results, key=lambda c: (-c["score"], c["id"]))[:top_k]


def evaluate_retriever(
    index: Any,
    questions: list[dict[str, Any]],
    strategy_name: str,
    top_k: int = 3,
    budget: int = 800,
) -> list[dict[str, Any]]:
    """Evaluate a retriever on a split, always computing Hit@1 and Hit@3 on top-3 for fair comparison."""
    traces: list[dict[str, Any]] = []
    search_k = max(top_k, 3)
    for q in questions:
        start = time.perf_counter()
        filters = q.get("filter")
        try:
            raw_results = index.search(q["question"], top_k=search_k, filters=filters)
        except TypeError:
            raw_results = index.search(q["question"], top_k=search_k)
        results_for_context = raw_results[:top_k]
        results_top3 = raw_results[:3]
        context, ids = pack_context(results_for_context, budget=budget)
        elapsed_ms = (time.perf_counter() - start) * 1000
        marked_context = [{**c, "hit": hit(c, q["gold"])} for c in results_for_context]
        marked_top3 = [{**c, "hit": hit(c, q["gold"])} for c in results_top3]
        traces.append({
            "query_id": q["id"],
            "split": q["split"],
            "question": q["question"],
            "strategy": strategy_name,
            "top_k": top_k,
            "budget_chars": budget,
            "gold": q["gold"],
            "results": marked_context,
            "context": context,
            "context_ids": ids,
            "context_chars": len(context),
            "elapsed_ms": round(elapsed_ms, 4),
            "hit1": bool(marked_top3 and marked_top3[0]["hit"]),
            "hit3": any(c["hit"] for c in marked_top3),
            "hit_k": any(c["hit"] for c in marked_context),
            "context_hit": any(c["hit"] and c["id"] in ids for c in marked_context),
        })
    return traces


def run_benchmark_suite(
    chunks_path: Path,
    questions_path: Path,
    split: str,
    output_root: Path,
) -> dict[str, Any]:
    chunks = json.loads(chunks_path.read_text(encoding="utf-8"))
    questions = json.loads(questions_path.read_text(encoding="utf-8"))
    selected = [q for q in questions if q.get("split") == split]
    validate(chunks, selected)

    # Build indexes
    t0 = time.perf_counter()
    tfidf_idx = TfidfIndex(chunks)
    tfidf_init_s = time.perf_counter() - t0

    t0 = time.perf_counter()
    bm25_idx = BM25Index(chunks)
    bm25_init_s = time.perf_counter() - t0

    t0 = time.perf_counter()
    dense_idx = Day6DenseIndex(chunks)
    dense_init_s = time.perf_counter() - t0

    t0 = time.perf_counter()
    hybrid_idx = HybridRRFIndex(
        dense_idx, bm25_idx, rrf_k=60, candidate_pool=20, dense_weight=1.2, lexical_weight=1.0
    )
    hybrid_init_s = time.perf_counter() - t0

    configs = [
        ("tfidf-baseline", tfidf_idx, "tfidf", 3, 800, tfidf_init_s),
        ("bm25", bm25_idx, "bm25", 3, 800, bm25_init_s),
        ("dense-day6", dense_idx, "dense", 3, 800, dense_init_s),
        ("hybrid-rrf-b800", hybrid_idx, "hybrid_rrf", 3, 800, hybrid_init_s),
        ("improve1-dense-b1500", dense_idx, "dense_b1500", 3, 1500, dense_init_s),
        ("improve2-hybrid-rrf-b1500", hybrid_idx, "hybrid_rrf_b1500", 3, 1500, hybrid_init_s),
        ("improve3-hybrid-rrf-k5-b1800", hybrid_idx, "hybrid_rrf_k5_b1800", 5, 1800, hybrid_init_s),
    ]

    suite_summary: dict[str, Any] = {}
    for folder_name, idx, strat_name, top_k, budget, init_s in configs:
        traces = evaluate_retriever(idx, selected, strat_name, top_k=top_k, budget=budget)
        summary = {
            "config_name": folder_name,
            "strategy": strat_name,
            "split": split,
            "n": len(traces),
            "top_k": top_k,
            "budget_chars": budget,
            "hit1": sum(t["hit1"] for t in traces),
            "hit1_rate": round(sum(t["hit1"] for t in traces) / len(traces), 4),
            "hit3": sum(t["hit3"] for t in traces),
            "hit3_rate": round(sum(t["hit3"] for t in traces) / len(traces), 4),
            "hit_k": sum(t["hit_k"] for t in traces),
            "context_hit": sum(t["context_hit"] for t in traces),
            "context_hit_rate": round(sum(t["context_hit"] for t in traces) / len(traces), 4),
            "avg_context_chars": round(statistics.mean(t["context_chars"] for t in traces), 2),
            "median_ms": round(statistics.median(t["elapsed_ms"] for t in traces), 4),
            "index_seconds": round(init_s, 4),
            "service_cost_usd": 0.0,
        }
        out_dir = output_root / f"{split}-{folder_name}"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "traces.json").write_text(json.dumps(traces, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (out_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        suite_summary[folder_name] = summary

    return suite_summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Day 7 retrieval methods and configurations")
    parser.add_argument("--chunks", type=Path, default=ROOT_DIR / "starter/data/converted/chunks.json")
    parser.add_argument("--questions", type=Path, default=ROOT_DIR / "starter/data/converted/questions.json")
    parser.add_argument("--split", choices=("dev", "test"), default="dev")
    parser.add_argument("--output-root", type=Path, default=ROOT_DIR / "starter/results")
    args = parser.parse_args()
    res = run_benchmark_suite(args.chunks, args.questions, args.split, args.output_root)
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
