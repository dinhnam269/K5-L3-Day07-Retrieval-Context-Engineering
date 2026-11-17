"""Build a self-contained interactive HTML demo dashboard (demo.html) from Day 7 results."""
from __future__ import annotations

import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def load_json(rel_path: str):
    return json.loads((ROOT_DIR / rel_path).read_text(encoding="utf-8"))


def main() -> None:
    chunks = load_json("starter/data/converted/chunks.json")
    questions = load_json("starter/data/converted/questions.json")
    cases = load_json("starter/data/converted/cases.json")

    retrieval_configs = [
        "dev-tfidf-baseline",
        "dev-bm25",
        "dev-dense-day6",
        "dev-hybrid-rrf-b800",
        "dev-improve1-dense-b1500",
        "dev-improve2-hybrid-rrf-b1500",
        "dev-improve3-hybrid-rrf-k5-b1800",
        "test-tfidf-baseline",
        "test-bm25",
        "test-dense-day6",
        "test-hybrid-rrf-b800",
        "test-improve1-dense-b1500",
        "test-improve2-hybrid-rrf-b1500",
        "test-improve3-hybrid-rrf-k5-b1800",
    ]
    retr_summaries = {}
    retr_traces = {}
    for cfg in retrieval_configs:
        p_sum = ROOT_DIR / "starter/results" / cfg / "summary.json"
        p_tr = ROOT_DIR / "starter/results" / cfg / "traces.json"
        if p_sum.exists():
            retr_summaries[cfg] = json.loads(p_sum.read_text(encoding="utf-8"))
        if p_tr.exists():
            retr_traces[cfg] = json.loads(p_tr.read_text(encoding="utf-8"))

    agent_runs = [
        "dev-agent-baseline",
        "dev-agent-selected",
        "test-agent-baseline",
        "test-agent-selected",
    ]
    agent_data = {}
    for r in agent_runs:
        r_dir = ROOT_DIR / "starter/results" / r
        agent_data[r] = {
            "summary": json.loads((r_dir / "summary.json").read_text(encoding="utf-8")),
            "meta": json.loads((r_dir / "run_meta.json").read_text(encoding="utf-8")),
            "traces": json.loads((r_dir / "traces.json").read_text(encoding="utf-8")),
            "reviews": json.loads((r_dir / "reviews.json").read_text(encoding="utf-8")),
        }

    bundle = {
        "chunks": chunks,
        "questions": questions,
        "cases": cases,
        "retrievalSummaries": retr_summaries,
        "retrievalTraces": retr_traces,
        "agentData": agent_data,
    }
    data_js = json.dumps(bundle, ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Day 7 — Agentic RAG & Context Engineering Demo | Nguyễn Đình Nam (2A202603797)</title>
  <style>
    :root {{
      --bg: #0f172a;
      --bg-card: #1e293b;
      --bg-card-alt: #0b1120;
      --border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --accent-soft: rgba(56, 189, 248, 0.14);
      --success: #22c55e;
      --success-soft: rgba(34, 197, 94, 0.15);
      --warn: #f59e0b;
      --warn-soft: rgba(245, 158, 11, 0.16);
      --danger: #ef4444;
      --danger-soft: rgba(239, 68, 68, 0.16);
      --purple: #a855f7;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.55;
    }}
    header {{
      background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 55%, #0f172a 100%);
      border-bottom: 1px solid var(--border);
      padding: 28px 24px 20px;
    }}
    .container {{
      max-width: 1360px;
      margin: 0 auto;
    }}
    .badge-row {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 10px;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 11px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 600;
      background: var(--accent-soft);
      color: var(--accent);
      border: 1px solid rgba(56, 189, 248, 0.3);
    }}
    .badge.green {{ background: var(--success-soft); color: #4ade80; border-color: rgba(34, 197, 94, 0.35); }}
    .badge.amber {{ background: var(--warn-soft); color: #fbbf24; border-color: rgba(245, 158, 11, 0.35); }}
    .badge.red {{ background: var(--danger-soft); color: #f87171; border-color: rgba(239, 68, 68, 0.35); }}
    h1 {{
      margin: 0 0 6px;
      font-size: 26px;
      letter-spacing: -0.02em;
    }}
    .subtitle {{
      margin: 0;
      color: var(--text-muted);
      font-size: 14px;
    }}
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 14px;
      margin-top: 20px;
    }}
    .kpi-card {{
      background: rgba(30, 41, 59, 0.85);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 14px 16px;
    }}
    .kpi-label {{
      font-size: 12px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .kpi-value {{
      font-size: 24px;
      font-weight: 700;
      margin: 4px 0;
      display: flex;
      align-items: baseline;
      gap: 8px;
    }}
    .kpi-delta {{
      font-size: 12px;
      font-weight: 600;
      color: #4ade80;
    }}
    .kpi-sub {{
      font-size: 12px;
      color: var(--text-muted);
    }}
    nav.tabs {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 22px;
    }}
    .tab-btn {{
      background: rgba(15, 23, 42, 0.7);
      color: var(--text-muted);
      border: 1px solid var(--border);
      padding: 9px 16px;
      border-radius: 8px;
      cursor: pointer;
      font-size: 13.5px;
      font-weight: 600;
      transition: all 0.15s;
    }}
    .tab-btn:hover {{
      color: var(--text);
      border-color: var(--accent);
    }}
    .tab-btn.active {{
      background: var(--accent);
      color: #0f172a;
      border-color: var(--accent);
    }}
    main {{
      padding: 24px;
    }}
    .tab-panel {{
      display: none;
    }}
    .tab-panel.active {{
      display: block;
    }}
    .card {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      margin-bottom: 20px;
    }}
    .card h2 {{
      margin: 0 0 12px;
      font-size: 18px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }}
    .card h3 {{
      margin: 0 0 8px;
      font-size: 15px;
      color: var(--accent);
    }}
    .pipeline-steps {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
      gap: 14px;
    }}
    .step-box {{
      background: var(--bg-card-alt);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 15px;
      position: relative;
    }}
    .step-num {{
      display: inline-block;
      background: var(--accent);
      color: #0f172a;
      font-weight: 700;
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 99px;
      margin-bottom: 8px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13.5px;
    }}
    th, td {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--border);
      text-align: left;
      vertical-align: top;
    }}
    th {{
      color: var(--text-muted);
      font-weight: 600;
      background: rgba(15, 23, 42, 0.5);
    }}
    tr.highlight-row {{
      background: rgba(34, 197, 94, 0.08);
    }}
    .bar-wrap {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .bar-track {{
      flex: 1;
      height: 8px;
      background: #0f172a;
      border-radius: 99px;
      overflow: hidden;
      min-width: 70px;
    }}
    .bar-fill {{
      height: 100%;
      border-radius: 99px;
      background: var(--accent);
    }}
    .bar-fill.green {{ background: var(--success); }}
    .bar-fill.amber {{ background: var(--warn); }}
    .inspector-layout {{
      display: grid;
      grid-template-columns: 320px 1fr;
      gap: 18px;
    }}
    @media (max-width: 960px) {{
      .inspector-layout {{ grid-template-columns: 1fr; }}
    }}
    .case-list {{
      max-height: 760px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 6px;
      padding-right: 4px;
    }}
    .case-item {{
      background: var(--bg-card-alt);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 10px 12px;
      cursor: pointer;
      transition: all 0.12s;
    }}
    .case-item:hover {{ border-color: var(--accent); }}
    .case-item.active {{
      border-color: var(--accent);
      background: rgba(56, 189, 248, 0.12);
    }}
    .compare-cols {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }}
    @media (max-width: 960px) {{
      .compare-cols {{ grid-template-columns: 1fr; }}
    }}
    .run-box {{
      background: var(--bg-card-alt);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 16px;
    }}
    .run-box.selected {{
      border-color: rgba(34, 197, 94, 0.45);
    }}
    pre.context-pre {{
      background: #070b14;
      border: 1px solid #1e293b;
      border-radius: 8px;
      padding: 10px 12px;
      font-size: 12px;
      white-space: pre-wrap;
      word-break: break-word;
      max-height: 290px;
      overflow-y: auto;
      color: #cbd5e1;
      margin: 8px 0 0;
    }}
    mark.ev-mark {{
      background: rgba(34, 197, 94, 0.28);
      color: #86efac;
      padding: 1px 3px;
      border-radius: 3px;
      font-weight: 600;
    }}
    .filter-bar {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;
    }}
    .filter-chip {{
      background: var(--bg-card-alt);
      color: var(--text-muted);
      border: 1px solid var(--border);
      border-radius: 6px;
      padding: 5px 10px;
      font-size: 12px;
      cursor: pointer;
    }}
    .filter-chip.active {{
      background: var(--accent-soft);
      color: var(--accent);
      border-color: var(--accent);
      font-weight: 600;
    }}
    .matrix-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(56px, 1fr));
      gap: 6px;
      margin-top: 8px;
    }}
    .matrix-cell {{
      padding: 6px;
      border-radius: 6px;
      text-align: center;
      font-size: 11.5px;
      font-weight: 600;
      border: 1px solid var(--border);
    }}
    .cell-ok {{ background: var(--success-soft); color: #4ade80; border-color: rgba(34,197,94,0.3); }}
    .cell-warn {{ background: var(--warn-soft); color: #fbbf24; border-color: rgba(245,158,11,0.3); }}
    .cell-miss {{ background: var(--danger-soft); color: #f87171; border-color: rgba(239,68,68,0.3); }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 12px;
      background: rgba(15, 23, 42, 0.75);
      padding: 2px 6px;
      border-radius: 4px;
      color: #7dd3fc;
    }}
  </style>
</head>
<body>
  <header>
    <div class="container">
      <div class="badge-row">
        <span class="badge">Day 7 — Agentic RAG & Context Engineering</span>
        <span class="badge green">MSSV: 2A202603797 · Nguyễn Đình Nam</span>
        <span class="badge">Day 6 Store: PostgreSQL 16 + pgvector (200 chunks)</span>
        <span class="badge">Embedding: gemini-embedding-001 (3072-d)</span>
        <span class="badge green">Unit Tests: 17/17 PASS</span>
      </div>
      <h1>Bảng Điều Khiển Thực Nghiệm Agentic RAG & Context Engineering</h1>
      <p class="subtitle">
        Kết nối dữ liệu & Vector Store từ Day 6 (*Harry Potter and the Sorcerer's Stone*, Chương 1–4, trang 12–61) ·
        So sánh 4 phương pháp Retrieval, 3 cấu hình cải thiện Context Budget & Đánh giá Agent trên 24 câu hỏi (17 Dev / 7 Test).
      </p>

      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-label">Context Evidence Rate (Dev / Test)</div>
          <div class="kpi-value">
            100% <span class="kpi-delta">+33.3% so với Baseline (66.7%)</span>
          </div>
          <div class="kpi-sub">Dev: 15/15 câu · Test: 5/5 câu có đủ bằng chứng trong context</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Điểm Grounded Answer (Thang 0–2)</div>
          <div class="kpi-value">
            2.00 / 2 <span class="kpi-delta">Baseline Dev: 1.40 · Test: 1.80</span>
          </div>
          <div class="kpi-sub">Đạt 15/15 mức 2 trên Dev & 5/5 mức 2 trên Test</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Citation Hợp Lệ & Hỗ Trợ</div>
          <div class="kpi-value">
            100% <span class="kpi-delta">Dev: 16/16 · Test: 5/5</span>
          </div>
          <div class="kpi-sub">Khắc phục lỗi trích dẫn thiếu câu nói trực tiếp ở q17 (Baseline: 83.3%)</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Abstention Đúng / Từ Chối Nhầm</div>
          <div class="kpi-value">
            100% / 0% <span class="kpi-delta">Giảm 4 ca từ chối nhầm ở Dev</span>
          </div>
          <div class="kpi-sub">Từ chối đúng 4/4 câu ngoài tài liệu (u01–u04), 0% bịa đặt</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Tốc Độ Trung Vị Agent (Test)</div>
          <div class="kpi-value">
            1,218 ms <span class="kpi-delta">Nhanh hơn 2.6× (Baseline: 3,197 ms)</span>
          </div>
          <div class="kpi-sub">Nhờ lấy trúng bằng chứng ngay lượt 1 (TB 1.06–1.14 lượt search)</div>
        </div>
      </div>

      <nav class="tabs">
        <button class="tab-btn active" onclick="switchTab('overview', this)">1. Tổng quan những gì đã làm</button>
        <button class="tab-btn" onclick="switchTab('retrieval', this)">2. Benchmark 4 Phương pháp Retrieval & Context</button>
        <button class="tab-btn" onclick="switchTab('errors', this)">3. Phân tích Lỗi & Cải thiện trên Dev</button>
        <button class="tab-btn" onclick="switchTab('inspector', this)">4. Soi Chi Tiết Trace Agent (24 Câu Hỏi)</button>
      </nav>
    </div>
  </header>

  <main class="container">
    <!-- TAB 1: OVERVIEW -->
    <section id="tab-overview" class="tab-panel active">
      <div class="card">
        <h2>Quy trình 5 bước đã triển khai hoàn chỉnh</h2>
        <div class="pipeline-steps">
          <div class="step-box">
            <span class="step-num">BƯỚC 1 · DỮ LIỆU DAY 6</span>
            <h3>Kết nối Corpus & Vector Store</h3>
            <p style="font-size:13px;color:var(--text-muted);margin:0;">
              Chuyển đổi <strong>200 chunks</strong> (Chiến lược C: <code>by_paragraph</code>, max 600 ký tự, trang 12–61) cùng vector <strong>3072 chiều</strong> từ <code>models/gemini-embedding-001</code> và PostgreSQL 16 + <code>pgvector</code> sang schema Day 7. Xây dựng bộ <strong>24 cases</strong> (15 câu có đáp án + 2 câu thiếu bằng chứng ở <code>dev</code>; 5 câu có đáp án + 2 câu thiếu bằng chứng ở <code>test</code>).
            </p>
          </div>
          <div class="step-box">
            <span class="step-num">BƯỚC 2 · 4 RETRIEVERS</span>
            <h3>Đa dạng phương pháp truy xuất</h3>
            <p style="font-size:13px;color:var(--text-muted);margin:0;">
              Cài đặt trong <code>src/retrievers.py</code>:<br/>
              1. <strong>TF-IDF Baseline</strong> (Lexical)<br/>
              2. <strong>Okapi BM25</strong> (Lexical + lọc stopwords)<br/>
              3. <strong>Dense Retrieval Day 6</strong> (Gemini 3072-d Cosine)<br/>
              4. <strong>Hybrid RRF</strong> (Hợp nhất thứ hạng Dense + BM25, <code>k=60</code>).
            </p>
          </div>
          <div class="step-box">
            <span class="step-num">BƯỚC 3 · CONTEXT ENGINEERING</span>
            <h3>Khắc phục nghẽn Context Budget</h3>
            <p style="font-size:13px;color:var(--text-muted);margin:0;">
              Phát hiện <code>budget=800</code> ký tự của starter chỉ chứa vừa 1 chunk (~550 ký tự + header), làm rơi mất bằng chứng ở Rank 2 tại <code>q02, q05, q09</code>. Mở rộng <code>budget=1500</code> ký tự giúp <strong>Context Evidence Rate đạt 100% (15/15 Dev & 5/5 Test)</strong>.
            </p>
          </div>
          <div class="step-box">
            <span class="step-num">BƯỚC 4 · AGENTIC LOOP</span>
            <h3>Điều phối Multi-turn & Abstention</h3>
            <p style="font-size:13px;color:var(--text-muted);margin:0;">
              Hiện thực <code>GeminiController</code> trong <code>src/agent.py</code>: Lượt 1 tìm kiếm với câu hỏi gốc; Lượt 2–3 tự động <strong>viết lại query (Query Rewriting)</strong> nếu thiếu thông tin; trả lời kèm trích dẫn <code>[chunk-id]</code> hoặc từ chối (<code>abstain</code>) khi không đủ bằng chứng.
            </p>
          </div>
          <div class="step-box">
            <span class="step-num">BƯỚC 5 · AUDIT & BÁO CÁO</span>
            <h3>Chấm thủ công & Kiểm thử</h3>
            <p style="font-size:13px;color:var(--text-muted);margin:0;">
              Đối chiếu từng câu trả lời và trích dẫn với văn bản gốc, xuất <code>reviews.json</code>, chạy <code>starter/agent_metrics.py</code>, vượt qua <strong>17/17 unit tests</strong> và hoàn thiện báo cáo tại <code>report/individual/2A202603797_NguyenDinhNam.md</code>.
            </p>
          </div>
        </div>
      </div>

      <div class="card">
        <h2>So sánh tổng hợp kết quả Agent (Baseline vs Cấu hình đã chọn)</h2>
        <table>
          <thead>
            <tr>
              <th>Cấu hình & Split</th>
              <th>Retriever & Context Budget</th>
              <th>Tool Use</th>
              <th>Số lượt gọi TB</th>
              <th>Grounded Answer (0 / 1 / 2)</th>
              <th>Điểm TB (/2.00)</th>
              <th>Citation Hợp lệ</th>
              <th>Abstention Đúng</th>
              <th>Từ chối nhầm (False Abstain)</th>
              <th>Thời gian trung vị</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td><strong>Baseline (Dev)</strong></td>
              <td><code>tfidf</code> · top_k=3 · budget=800</td>
              <td>17/17 (100%)</td>
              <td>1.29 lượt</td>
              <td>0: 4 · 1: 1 · 2: 10</td>
              <td><strong>1.40 / 2.00</strong></td>
              <td>11/11 (100%)</td>
              <td>2/2 (100%)</td>
              <td><span class="badge red">4/15 (26.7%)</span></td>
              <td>2,660.11 ms</td>
            </tr>
            <tr class="highlight-row">
              <td><strong>Cấu hình chọn (Dev)</strong></td>
              <td><code>dense</code> · top_k=3 · <strong>budget=1500</strong></td>
              <td>17/17 (100%)</td>
              <td>1.06 lượt</td>
              <td>0: 0 · 1: 0 · 2: 15</td>
              <td><span class="badge green">2.00 / 2.00</span></td>
              <td><strong>16/16 (100%)</strong></td>
              <td><strong>2/2 (100%)</strong></td>
              <td><span class="badge green">0/15 (0.0%)</span></td>
              <td>1,709.52 ms</td>
            </tr>
            <tr>
              <td><strong>Baseline (Test)</strong></td>
              <td><code>tfidf</code> · top_k=3 · budget=800</td>
              <td>7/7 (100%)</td>
              <td>1.14 lượt</td>
              <td>0: 0 · 1: 1 · 2: 4</td>
              <td><strong>1.80 / 2.00</strong></td>
              <td><span class="badge amber">5/6 (83.3%)</span></td>
              <td>2/2 (100%)</td>
              <td>0/5 (0.0%)</td>
              <td>3,197.15 ms</td>
            </tr>
            <tr class="highlight-row">
              <td><strong>Cấu hình chọn (Test)</strong></td>
              <td><code>dense</code> · top_k=3 · <strong>budget=1500</strong></td>
              <td>7/7 (100%)</td>
              <td>1.14 lượt</td>
              <td>0: 0 · 1: 0 · 2: 5</td>
              <td><span class="badge green">2.00 / 2.00</span></td>
              <td><span class="badge green">5/5 (100%)</span></td>
              <td><strong>2/2 (100%)</strong></td>
              <td><span class="badge green">0/5 (0.0%)</span></td>
              <td>1,218.46 ms</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- TAB 2: RETRIEVAL BENCHMARK -->
    <section id="tab-retrieval" class="tab-panel">
      <div class="card">
        <h2>Bảng kết quả 7 Cấu hình Retrieval & Context trên Dev (15 câu) và Test (5 câu)</h2>
        <table id="retr-table">
          <thead>
            <tr>
              <th>Cấu hình</th>
              <th>Split</th>
              <th>Phương pháp</th>
              <th>top_k</th>
              <th>Budget (ký tự)</th>
              <th>Hit@1</th>
              <th>Evidence Hit@3</th>
              <th>Context Evidence Rate</th>
              <th>Độ dài Context TB</th>
              <th>Thời gian trung vị</th>
            </tr>
          </thead>
          <tbody id="retr-tbody"></tbody>
        </table>
      </div>

      <div class="card">
        <h2>Ma trận kết quả từng câu hỏi (Hit@1 / Hit@3 / Context Hit)</h2>
        <p style="font-size:13px;color:var(--text-muted);margin-top:0;">
          Màu xanh lá (<code>CTX HIT</code>): bằng chứng chuẩn nằm trong context cuối gửi cho LLM ·
          Màu vàng (<code>HIT@3 ONLY</code>): tìm thấy trong top-3 nhưng bị cắt bỏ do vượt <code>budget=800</code> ·
          Màu đỏ (<code>MISS</code>): không có trong top-3.
        </p>
        <div id="heatmap-container"></div>
      </div>
    </section>

    <!-- TAB 3: ERROR ANALYSIS -->
    <section id="tab-errors" class="tab-panel">
      <div class="card">
        <h2>Phân tích 3 Ca Lỗi Điển Hình & Cách Khắc Phục</h2>
        <div class="compare-cols">
          <div class="run-box">
            <span class="badge red">LỖI 1 · TRUNCATION TRÊN DEV (q02, q05, q09)</span>
            <h3 style="margin-top:10px;">Nghẽn Context Budget 800 ký tự làm rơi bằng chứng ở Rank 2</h3>
            <p style="font-size:13.5px;color:var(--text-muted);">
              Ở câu <code>q09</code> (<em>"Although the sign next to the glass said Boa Constrictor, Brazil, why had the snake never actually been to Brazil?"</em>), cả TF-IDF và Dense đều xếp đoạn chứa đáp án <code>hp-book1-ch1-4_p034_paraC_01</code> ở <strong>Rank 2</strong>:
            </p>
            <ul style="font-size:13px;color:var(--text-muted);">
              <li>Rank 1 (<code>p034_paraC_00</code>): 329 ký tự + 64 ký tự header = <strong>393 ký tự</strong>.</li>
              <li>Rank 2 (<code>p034_paraC_01</code> — chứa <em>"This specimen was bred in the zoo"</em>): 379 ký tự + 64 ký tự header = <strong>443 ký tự</strong>.</li>
              <li>Tổng cộng: <code>393 + 2 + 443 = 838 ký tự > 800</code> (vượt ngân sách đúng <strong>38 ký tự</strong>!).</li>
              <li>Hệ quả: Dù Baseline Agent cố gọi tới <strong>3 lượt search</strong> với query viết lại, <code>pack_context</code> vẫn ưu tiên giữ đoạn Rank 1 của lượt đầu nên Agent đành từ chối nhầm (<code>status: abstain</code>).</li>
            </ul>
            <p style="font-size:13.5px;color:#4ade80;font-weight:600;margin-bottom:0;">
              Giải pháp: Tăng <code>budget</code> từ 800 lên <code>1500</code> ký tự giúp chứa trọn vẹn 2–3 đoạn đầu tiên, đưa Context Evidence Rate lên 15/15 (100%) ngay ở lượt search đầu tiên!
            </p>
          </div>

          <div class="run-box">
            <span class="badge amber">LỖI 2 · LEXICAL MISMATCH TRÊN DEV (q05 & q12)</span>
            <h3 style="margin-top:10px;">Khác biệt từ vựng giữa câu hỏi và nguyên văn</h3>
            <p style="font-size:13.5px;color:var(--text-muted);">
              Ở câu <code>q12</code> (<em>"Where did Uncle Vernon sleep at night to prevent Harry from sneaking downstairs to collect the morning mail?"</em>), TF-IDF và BM25 đều trượt top-3 vì văn bản gốc tại <code>hp-book1-ch1-4_p044_paraC_00</code> viết:
              <br/><em>"Uncle Vernon had been lying at the foot of the front door in a sleeping bag..."</em> (không có từ <em>"sleep at night"</em> hay <em>"morning mail"</em>).
            </p>
            <p style="font-size:13.5px;color:var(--text-muted);">
              Tương tự ở <code>q05</code>, câu hỏi cần kết hợp thông tin viết thư ở trang 22 (<code>p022_paraC_00</code>) và hành động nhét thư vào chăn của Harry trên bậc cửa ở trang 24 (<code>p024_paraC_00</code>).
            </p>
            <p style="font-size:13.5px;color:#4ade80;font-weight:600;margin-bottom:0;">
              Giải pháp: Dense Retrieval (<code>gemini-embedding-001</code> 3072 chiều) xếp <code>p044_paraC_00</code> lên thẳng Rank 1 cho <code>q12</code> và lấy đủ cả hai đoạn trang 22 & 24 cho <code>q05</code>!
            </p>
          </div>
        </div>

        <div class="run-box" style="margin-top:16px;">
          <span class="badge amber">LỖI 3 · CITATION ID HỢP LỆ NHƯNG THIẾU BẰNG CHỨNG TRỰC TIẾP TRÊN TEST (q17)</span>
          <h3 style="margin-top:10px;">Tại sao phải đọc đối chiếu Citation thủ công thay vì chỉ kiểm tra ID?</h3>
          <p style="font-size:13.5px;color:var(--text-muted);margin-bottom:6px;">
            Câu <code>q17</code> hỏi: <em>"How many presents did Aunt Petunia say Dudley would have in total on his birthday after promising to buy him two more?"</em>
          </p>
          <ul style="font-size:13px;color:var(--text-muted);margin-top:0;">
            <li><strong>Ở Baseline (TF-IDF, budget=800):</strong> Context chỉ lấy được 2 đoạn ở trang 28: <code>p028_paraC_03</code> (nêu Dudley đếm được 37 món và dì Petunia hứa mua thêm 2 món) và <code>p028_paraC_04</code> (chỉ có đúng câu <em>"Two more presents. Is that all right?"</em>), làm rơi mất đoạn trang 29 (<code>p029_paraC_00</code>). Agent trả lời <em>"thirty-nine presents"</em> và trích dẫn <code>[hp-book1-ch1-4_p028_paraC_03, hp-book1-ch1-4_p028_paraC_04]</code>. Khi kiểm tra thủ công, <code>p028_paraC_04</code> hoàn toàn không chứa tổng số 39 -> chấm <code>citation_support: [true, false]</code> và <code>answer_grade: 1</code>.</li>
            <li><strong>Ở Cấu hình đã chọn (Dense, budget=1500):</strong> Context chứa trực tiếp <code>hp-book1-ch1-4_p029_paraC_00</code> (trang 29: <em>"“Thirty-nine, sweetums,” said Aunt Petunia."</em>). Agent trích dẫn chính xác <code>[hp-book1-ch1-4_p029_paraC_00]</code> -> đạt <code>citation_support: [true]</code> và <code>answer_grade: 2</code>.</li>
          </ul>
        </div>
      </div>
    </section>

    <!-- TAB 4: INTERACTIVE TRACE INSPECTOR -->
    <section id="tab-inspector" class="tab-panel">
      <div class="card">
        <h2>Trình duyệt Trace & Đối chiếu Câu trả lời Agent (Toàn bộ 24 Cases)</h2>
        <div class="filter-bar">
          <button class="filter-chip active" onclick="filterCases('all', this)">Tất cả (24)</button>
          <button class="filter-chip" onclick="filterCases('dev', this)">Tập Dev (17)</button>
          <button class="filter-chip" onclick="filterCases('test', this)">Tập Test (7)</button>
          <button class="filter-chip" onclick="filterCases('unanswerable', this)">Câu thiếu bằng chứng u01–u04 (4)</button>
          <button class="filter-chip" onclick="filterCases('diff', this)">Ca Cải thiện rõ rệt (q01, q02, q05, q09, q12, q17)</button>
        </div>

        <div class="inspector-layout">
          <div class="case-list" id="case-list"></div>
          <div id="case-detail"></div>
        </div>
      </div>
    </section>
  </main>

  <script>
    const DATA = {data_js};

    function switchTab(tabId, btn) {{
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.getElementById('tab-' + tabId).classList.add('active');
      btn.classList.add('active');
    }}

    function escapeHtml(str) {{
      return String(str || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;');
    }}

    function highlightEvidence(text, evidences) {{
      let html = escapeHtml(text);
      (evidences || []).forEach(ev => {{
        if (!ev) return;
        const escEv = escapeHtml(ev);
        if (html.includes(escEv)) {{
          html = html.split(escEv).join('<mark class="ev-mark">' + escEv + '</mark>');
        }}
      }});
      return html;
    }}

    // Populate Retrieval Table & Heatmap
    function renderRetrievalTab() {{
      const order = [
        ['dev-tfidf-baseline', 'Baseline (TF-IDF)'],
        ['dev-bm25', 'Phương pháp 2 (Okapi BM25)'],
        ['dev-dense-day6', 'Phương pháp 3 (Dense Day 6)'],
        ['dev-hybrid-rrf-b800', 'Phương pháp 4 (Hybrid RRF)'],
        ['dev-improve1-dense-b1500', 'Cải thiện 1 (Dense + b=1500) ★ Đã chọn'],
        ['dev-improve2-hybrid-rrf-b1500', 'Cải thiện 2 (Hybrid RRF + b=1500)'],
        ['dev-improve3-hybrid-rrf-k5-b1800', 'Cải thiện 3 (Hybrid RRF + k=5, b=1800)'],
        ['test-improve1-dense-b1500', 'Cấu hình đã chọn (Test) ★'],
        ['test-tfidf-baseline', 'Baseline TF-IDF (Test)'],
      ];
      const tbody = document.getElementById('retr-tbody');
      tbody.innerHTML = order.map(([key, label]) => {{
        const s = DATA.retrievalSummaries[key];
        if (!s) return '';
        const isHighlight = key.includes('improve1-dense-b1500');
        const h1Pct = Math.round(s.hit1_rate * 1000) / 10;
        const h3Pct = Math.round(s.hit3_rate * 1000) / 10;
        const ctxPct = Math.round(s.context_hit_rate * 1000) / 10;
        return `<tr class="${{isHighlight ? 'highlight-row' : ''}}">
          <td><strong>${{escapeHtml(label)}}</strong></td>
          <td><span class="badge ${{s.split === 'test' ? 'amber' : ''}}">${{s.split.toUpperCase()}}</span></td>
          <td><code>${{escapeHtml(s.strategy)}}</code></td>
          <td>${{s.top_k}}</td>
          <td>${{s.budget_chars}}</td>
          <td>
            <div class="bar-wrap">
              <span>${{s.hit1}}/${{s.n}} (${{h1Pct}}%)</span>
              <div class="bar-track"><div class="bar-fill" style="width:${{h1Pct}}%"></div></div>
            </div>
          </td>
          <td>
            <div class="bar-wrap">
              <span>${{s.hit3}}/${{s.n}} (${{h3Pct}}%)</span>
              <div class="bar-track"><div class="bar-fill green" style="width:${{h3Pct}}%"></div></div>
            </div>
          </td>
          <td>
            <div class="bar-wrap">
              <strong>${{s.context_hit}}/${{s.n}} (${{ctxPct}}%)</strong>
              <div class="bar-track"><div class="bar-fill ${{ctxPct === 100 ? 'green' : 'amber'}}" style="width:${{ctxPct}}%"></div></div>
            </div>
          </td>
          <td>${{s.avg_context_chars}} ký tự</td>
          <td>${{s.median_ms}} ms</td>
        </tr>`;
      }}).join('');

      // Render Heatmap for Dev configurations
      const hmConfigs = [
        ['dev-tfidf-baseline', 'Dev: TF-IDF Baseline (budget=800)'],
        ['dev-bm25', 'Dev: Okapi BM25 (budget=800)'],
        ['dev-dense-day6', 'Dev: Dense Day 6 (budget=800)'],
        ['dev-improve1-dense-b1500', 'Dev: Cải thiện 1 — Dense Day 6 (budget=1500) ★'],
        ['test-tfidf-baseline', 'Test: TF-IDF Baseline (budget=800)'],
        ['test-improve1-dense-b1500', 'Test: Cấu hình chọn — Dense Day 6 (budget=1500) ★'],
      ];
      const hmDiv = document.getElementById('heatmap-container');
      hmDiv.innerHTML = hmConfigs.map(([key, title]) => {{
        const traces = DATA.retrievalTraces[key] || [];
        const cells = traces.map(t => {{
          let cls = 'cell-miss';
          let status = 'MISS';
          if (t.context_hit) {{
            cls = 'cell-ok';
            status = t.hit1 ? 'R1+CTX' : 'R2+CTX';
          }} else if (t.hit3) {{
            cls = 'cell-warn';
            status = 'DROP(b)';
          }}
          return `<div class="matrix-cell ${{cls}}" title="${{escapeHtml(t.question)}}">
            <div>${{t.query_id}}</div>
            <div style="font-size:10px;opacity:0.85;">${{status}}</div>
          </div>`;
        }}).join('');
        return `<div style="margin-bottom:14px;">
          <div style="font-size:13px;font-weight:600;margin-bottom:4px;">${{escapeHtml(title)}}</div>
          <div class="matrix-grid">${{cells}}</div>
        </div>`;
      }}).join('');
    }}

    // Inspector logic
    let currentFilter = 'all';
    let selectedCaseId = 'q09';

    const questionById = {{}};
    DATA.questions.forEach(q => {{ questionById[q.id] = q; }});

    function getAgentTrace(runKey, qid) {{
      const run = DATA.agentData[runKey];
      if (!run) return {{ trace: null, review: null }};
      const trace = (run.traces || []).find(t => t.query_id === qid) || null;
      const review = (run.reviews || []).find(r => r.query_id === qid) || null;
      return {{ trace, review }};
    }}

    function filterCases(mode, btn) {{
      currentFilter = mode;
      document.querySelectorAll('.filter-chip').forEach(b => b.classList.remove('active'));
      if (btn) btn.classList.add('active');
      renderCaseList();
    }}

    function renderCaseList() {{
      const diffIds = new Set(['q01', 'q02', 'q05', 'q09', 'q12', 'q17']);
      const filtered = DATA.cases.filter(c => {{
        if (currentFilter === 'dev') return c.split === 'dev';
        if (currentFilter === 'test') return c.split === 'test';
        if (currentFilter === 'unanswerable') return !c.answerable;
        if (currentFilter === 'diff') return diffIds.has(c.id);
        return true;
      }});
      if (!filtered.some(c => c.id === selectedCaseId) && filtered.length) {{
        selectedCaseId = filtered[0].id;
      }}
      const listEl = document.getElementById('case-list');
      listEl.innerHTML = filtered.map(c => {{
        const baseRun = c.split === 'dev' ? 'dev-agent-baseline' : 'test-agent-baseline';
        const selRun = c.split === 'dev' ? 'dev-agent-selected' : 'test-agent-selected';
        const bRev = getAgentTrace(baseRun, c.id).review;
        const sRev = getAgentTrace(selRun, c.id).review;
        const bLabel = c.answerable ? `Base: G${{bRev ? bRev.answer_grade : '?'}}` : `Base: Abstain`;
        const sLabel = c.answerable ? `Sel: G${{sRev ? sRev.answer_grade : '?'}}` : `Sel: Abstain`;
        return `<div class="case-item ${{c.id === selectedCaseId ? 'active' : ''}}" onclick="selectCase('${{c.id}}')">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
            <strong>${{c.id.toUpperCase()}} · ${{c.split.toUpperCase()}}</strong>
            <span style="font-size:11px;color:${{c.answerable ? '#38bdf8' : '#fbbf24'}};">
              ${{c.answerable ? 'Có đáp án' : 'Thiếu evidence'}}
            </span>
          </div>
          <div style="font-size:12.5px;color:var(--text-muted);display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">
            ${{escapeHtml(c.question)}}
          </div>
          <div style="margin-top:6px;display:flex;gap:6px;font-size:11px;">
            <span class="badge ${{bRev && bRev.answer_grade === 2 || (bRev && bRev.abstention_correct) ? 'green' : 'red'}}">${{bLabel}}</span>
            <span class="badge green">${{sLabel}}</span>
          </div>
        </div>`;
      }}).join('');
      renderCaseDetail();
    }}

    function selectCase(cid) {{
      selectedCaseId = cid;
      renderCaseList();
    }}

    function renderRunColumn(title, isSelectedConfig, trace, review, qObj, caseObj) {{
      if (!trace) return `<div class="run-box">Không có dữ liệu trace</div>`;
      const evidences = qObj ? (qObj.gold || []).map(g => g.evidence) : [];
      const gradeBadge = caseObj.answerable
        ? `<span class="badge ${{review.answer_grade === 2 ? 'green' : (review.answer_grade === 1 ? 'amber' : 'red')}}">Grounded Grade: ${{review.answer_grade}} / 2</span>`
        : `<span class="badge ${{review.abstention_correct ? 'green' : 'red'}}">Abstention Correct: ${{review.abstention_correct}}</span>`;

      const queriesHtml = (trace.queries || []).map((q, idx) =>
        `<div style="font-size:12px;margin-bottom:3px;"><code>Lượt ${{idx + 1}}</code> ${{escapeHtml(q)}}</div>`
      ).join('');

      const citsHtml = (trace.citations || []).length
        ? trace.citations.map((cid, i) => {{
            const ok = review && review.citation_support ? review.citation_support[i] : true;
            return `<span class="badge ${{ok ? 'green' : 'red'}}">[${{escapeHtml(cid)}}] ${{ok ? '✓ Hỗ trợ' : '✗ Không đủ hỗ trợ'}}</span>`;
          }}).join(' ')
        : `<span style="font-size:12px;color:var(--text-muted);">Không có citation (Abstain)</span>`;

      return `<div class="run-box ${{isSelectedConfig ? 'selected' : ''}}">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:6px;margin-bottom:10px;">
          <h3 style="margin:0;">${{escapeHtml(title)}}</h3>
          ${{gradeBadge}}
        </div>
        <div style="font-size:12px;color:var(--text-muted);margin-bottom:10px;">
          Retriever: <code>${{trace.retriever_type}}</code> · Budget: <code>${{trace.budget}}</code> ký tự ·
          Số lượt search: <strong>${{trace.num_searches}}</strong> · Thời gian: <strong>${{trace.elapsed_ms}} ms</strong>
        </div>

        <div style="margin-bottom:10px;">
          <div style="font-size:12px;font-weight:600;color:var(--text-muted);margin-bottom:4px;">TRUY VẤN SEARCH ĐÃ GỌI:</div>
          ${{queriesHtml}}
        </div>

        <div style="margin-bottom:10px;">
          <div style="font-size:12px;font-weight:600;color:var(--text-muted);margin-bottom:4px;">CÂU TRẢ LỜI CỦA AGENT (${{trace.status.toUpperCase()}}):</div>
          <div style="background:#0f172a;border:1px solid var(--border);border-radius:8px;padding:10px 12px;font-size:13.5px;">
            ${{escapeHtml(trace.answer)}}
          </div>
        </div>

        <div style="margin-bottom:10px;">
          <div style="font-size:12px;font-weight:600;color:var(--text-muted);margin-bottom:4px;">ĐÁNH GIÁ CITATION:</div>
          <div>${{citsHtml}}</div>
        </div>

        <div style="margin-bottom:10px;">
          <div style="font-size:12px;font-weight:600;color:var(--text-muted);margin-bottom:4px;">NHẬN XÉT AUDIT THỦ CÔNG:</div>
          <div style="font-size:12.5px;color:#cbd5e1;background:rgba(56,189,248,0.07);border-left:3px solid var(--accent);padding:8px 10px;border-radius:4px;">
            ${{escapeHtml(review ? review.audit_reason : '')}}
          </div>
        </div>

        <div>
          <div style="font-size:12px;font-weight:600;color:var(--text-muted);">
            CONTEXT CUỐI GỬI CHO MODEL (${{(trace.final_context || '').length}} / ${{trace.budget}} ký tự · tô sáng bằng chứng chuẩn):
          </div>
          <pre class="context-pre">${{highlightEvidence(trace.final_context || '', evidences)}}</pre>
        </div>
      </div>`;
    }}

    function renderCaseDetail() {{
      const caseObj = DATA.cases.find(c => c.id === selectedCaseId);
      if (!caseObj) return;
      const qObj = questionById[caseObj.id] || null;
      const baseRun = caseObj.split === 'dev' ? 'dev-agent-baseline' : 'test-agent-baseline';
      const selRun = caseObj.split === 'dev' ? 'dev-agent-selected' : 'test-agent-selected';
      const baseData = getAgentTrace(baseRun, caseObj.id);
      const selData = getAgentTrace(selRun, caseObj.id);

      const goldBox = qObj
        ? `<div style="margin-top:8px;font-size:13px;">
            <div><strong>Đáp án chuẩn kỳ vọng:</strong> ${{escapeHtml(qObj.expected_answer)}}</div>
            <div style="margin-top:4px;color:#86efac;">
              <strong>Gold Evidence (Trang ${{qObj.gold[0].page}}):</strong>
              <em>"${{escapeHtml(qObj.gold[0].evidence)}}"</em>
            </div>
          </div>`
        : `<div style="margin-top:8px;font-size:13px;color:#fbbf24;">
            <strong>Hành vi kỳ vọng:</strong> Tìm kiếm và Từ chối trả lời (<code>search_and_abstain</code>)<br/>
            <strong>Lý do thiếu bằng chứng:</strong> ${{escapeHtml(caseObj.absence_reason)}}
          </div>`;

      const detailEl = document.getElementById('case-detail');
      detailEl.innerHTML = `
        <div class="run-box" style="margin-bottom:14px;">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <span class="badge">${{caseObj.id.toUpperCase()}} · Tập ${{caseObj.split.toUpperCase()}}</span>
            <span class="badge ${{caseObj.answerable ? 'green' : 'amber'}}">
              ${{caseObj.answerable ? 'Câu hỏi có đáp án trong tài liệu' : 'Câu hỏi không đủ bằng chứng (Unanswerable)'}}
            </span>
          </div>
          <h3 style="margin:8px 0 4px;font-size:17px;color:var(--text);">${{escapeHtml(caseObj.question)}}</h3>
          ${{goldBox}}
        </div>
        <div class="compare-cols">
          ${{renderRunColumn('Baseline Agent (TF-IDF, budget=800)', false, baseData.trace, baseData.review, qObj, caseObj)}}
          ${{renderRunColumn('Selected Agent (Dense Day 6, budget=1500) ★', true, selData.trace, selData.review, qObj, caseObj)}}
        </div>
      `;
    }}

    renderRetrievalTab();
    renderCaseList();
  </script>
</body>
</html>
"""
    out_path = ROOT_DIR / "demo.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Created interactive demo at: {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
