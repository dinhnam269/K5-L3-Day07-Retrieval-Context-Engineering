import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "starter"))
sys.path.insert(0, str(ROOT / "src"))

from retrievers import BM25Index, Day6DenseIndex, HybridRRFIndex, evaluate_retriever
from baseline import TfidfIndex, validate


class Day7PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chunks_path = ROOT / "starter/data/converted/chunks.json"
        cls.questions_path = ROOT / "starter/data/converted/questions.json"
        cls.cases_path = ROOT / "starter/data/converted/cases.json"
        cls.chunks = json.loads(cls.chunks_path.read_text(encoding="utf-8"))
        cls.questions = json.loads(cls.questions_path.read_text(encoding="utf-8"))
        cls.cases = json.loads(cls.cases_path.read_text(encoding="utf-8"))

    def test_benchmark_dataset_counts_and_schema(self):
        validate(self.chunks, self.questions)
        dev_q = [q for q in self.questions if q["split"] == "dev"]
        test_q = [q for q in self.questions if q["split"] == "test"]
        self.assertGreaterEqual(len(dev_q), 15)
        self.assertGreaterEqual(len(test_q), 5)

        dev_unans = [c for c in self.cases if c["split"] == "dev" and not c["answerable"]]
        test_unans = [c for c in self.cases if c["split"] == "test" and not c["answerable"]]
        self.assertGreaterEqual(len(dev_unans), 2)
        self.assertGreaterEqual(len(test_unans), 2)

    def test_three_distinct_retrieval_methods_on_dev(self):
        dev_q = [q for q in self.questions if q["split"] == "dev"]
        tfidf = TfidfIndex(self.chunks)
        bm25 = BM25Index(self.chunks)
        dense = Day6DenseIndex(self.chunks, use_pgvector=False)
        hybrid = HybridRRFIndex(dense, bm25)

        t_tfidf = evaluate_retriever(tfidf, dev_q, "tfidf", top_k=3, budget=800)
        t_bm25 = evaluate_retriever(bm25, dev_q, "bm25", top_k=3, budget=800)
        t_dense = evaluate_retriever(dense, dev_q, "dense_b1500", top_k=3, budget=1500)
        t_hybrid = evaluate_retriever(hybrid, dev_q, "hybrid_b1500", top_k=3, budget=1500)

        self.assertEqual(len(t_tfidf), 15)
        self.assertEqual(sum(t["hit3"] for t in t_dense), 15)
        self.assertEqual(sum(t["context_hit"] for t in t_dense), 15)
        self.assertEqual(sum(t["context_hit"] for t in t_hybrid), 15)
        self.assertGreater(sum(t["context_hit"] for t in t_dense), sum(t["context_hit"] for t in t_tfidf))


if __name__ == "__main__":
    unittest.main()
