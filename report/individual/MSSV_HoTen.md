# Báo cáo Day 7 — Agentic RAG & Context Engineering

- **Họ và tên:** Nguyễn Đình Nam
- **MSSV:** 2A202603797
- **Lớp:** K5-L3B

> Bản báo cáo đầy đủ cũng được lưu tại [report/individual/2A202603797_NguyenDinhNam.md](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/report/individual/2A202603797_NguyenDinhNam.md).

---

## 1. Dữ liệu và benchmark

- **Nguồn, quyền sử dụng, số trang và số chunk:**
  - Tài liệu: *Harry Potter and the Sorcerer's Stone* (Chương 1–4, trang **12–61**, tổng cộng **50 trang** văn bản hợp lệ), sử dụng cho mục đích học tập/nghiên cứu nội bộ môn học.
  - Số lượng chunk: **200 chunks** kế thừa từ Chiến lược C của Day 6 (`by_paragraph`, tối đa 600 ký tự), lưu tại `starter/data/converted/chunks.json`.
- **Vector store, embedding model, phiên bản và số chiều:**
  - Embedding model: Google Gemini API `models/gemini-embedding-001` (`v1beta`), **3072 chiều**.
  - Vector store: PostgreSQL 16.16 + pgvector 0.8.7 (`127.0.0.1:55433/day6_lab`, bảng `document_chunks`, khoảng cách Cosine `<=>`) đồng bộ với cache vector `.embedding_cache.json`.
- **Agent model, cách chạy và phân chia dev/test:**
  - Agent model: `gemini-3.5-flash-lite` (`temperature=0.0`, JSON structured output).
  - Bộ câu hỏi Benchmark (**24 câu**):
    - `dev` (**17 câu**): **15 câu có đáp án** (`q01`–`q15`) + **2 câu thiếu bằng chứng** (`u01`–`u02`).
    - `test` (**7 câu**): **5 câu có đáp án** (`q16`–`q20`) + **2 câu thiếu bằng chứng** (`u03`–`u04`).
- **Cách xác định câu có/thiếu evidence và tiêu chí chấm:**
  - Câu có đáp án có trích dẫn `evidence` nguyên văn nằm trọn trong chunk đúng `source_id` và `page`.
  - Câu thiếu bằng chứng hỏi về các chi tiết không có trong Chương 1–4 (giá đũa phép ở Chương 5, lương của ông Dursley, nhà Phân loại ở Chương 7, biển số xe máy bay của Sirius Black).

---

## 2. Retrieval và thử nghiệm

| Cấu hình | Phương pháp, top-k, filter, rerank, context budget | Giả thuyết / thay đổi | Split | Hit@1 | Evidence Hit@3 | Context Evidence Rate | Thời gian / chi phí |
|---|---|---|---|---|---|---|---|
| **Baseline (`tfidf-baseline`)** | Lexical TF-IDF, `top_k=3`, `budget=800` | Baseline từ khóa của starter | `dev` | 10/15 (66.7%) | 13/15 (86.7%) | 10/15 (66.7%) | 0.34 ms / \$0.00 |
| **Phương pháp 2 (`bm25`)** | Okapi BM25 ($k_1=1.5, b=0.75$), `top_k=3`, `budget=800` | Lọc stopwords và chuẩn hóa độ dài chunk | `dev` | 10/15 (66.7%) | 14/15 (93.3%) | 10/15 (66.7%) | 0.21 ms / \$0.00 |
| **Phương pháp 3 (`dense-day6`)** | Dense `gemini-embedding-001` (3072-d), `top_k=3`, `budget=800` | Bắt tương đồng ngữ nghĩa khi câu hỏi khác từ vựng | `dev` | **12/15 (80.0%)** | **15/15 (100.0%)** | 12/15 (80.0%) | 43.83 ms / \$0.00 |
| **Phương pháp 4 (`hybrid-rrf-b800`)** | Hybrid RRF (Dense + BM25, $k=60$), `top_k=3`, `budget=800` | Hợp nhất thứ hạng Dense và BM25 | `dev` | 11/15 (73.3%) | **15/15 (100.0%)** | 11/15 (73.3%) | 43.86 ms / \$0.00 |
| **Cải thiện 1 (`improve1-dense-b1500`)** *(Đã chọn)* | Dense `gemini-embedding-001`, `top_k=3`, **`budget=1500`** | Tăng budget lên 1500 ký tự để không làm rơi chunk Rank 2 | `dev` | **12/15 (80.0%)** | **15/15 (100.0%)** | **15/15 (100.0%)** | 43.70 ms / \$0.00 |
| **Cải thiện 2 (`improve2-hybrid-rrf-b1500`)** | Hybrid RRF (Dense + BM25), `top_k=3`, **`budget=1500`** | Kết hợp Hybrid RRF với `budget=1500` | `dev` | 11/15 (73.3%) | **15/15 (100.0%)** | **15/15 (100.0%)** | 43.95 ms / \$0.00 |
| **Cải thiện 3 (`improve3-hybrid-rrf-k5-b1800`)** | Hybrid RRF, **`top_k=5`**, **`budget=1800`** | Thử tăng `top_k=5, budget=1800` (không tăng thêm điểm so với Cải thiện 1 nhưng tốn thêm context) | `dev` | 11/15 (73.3%) | **15/15 (100.0%)** | **15/15 (100.0%)** | 43.10 ms / \$0.00 |
| **Cấu hình đã chọn (`improve1-dense-b1500`)** | Dense `gemini-embedding-001`, `top_k=3`, **`budget=1500`** | Đánh giá trên tập `test` sau khi chốt | **`test`** | **4/5 (80.0%)** | **5/5 (100.0%)** | **5/5 (100.0%)** | 42.75 ms / \$0.00 |
| **Baseline (`tfidf-baseline`)** | Lexical TF-IDF, `top_k=3`, `budget=800` | Đánh giá Baseline trên tập `test` | **`test`** | 3/5 (60.0%) | 4/5 (80.0%) | 4/5 (80.0%) | 0.41 ms / \$0.00 |

- **Hai lỗi dev, nguyên nhân, cách thử và lý do chọn cấu hình:**
  1. **Lỗi 1 (Lexical Mismatch ở `q05` & `q12`):** TF-IDF trượt top-3 ở `q05` và `q12` do câu hỏi dùng từ khái quát còn văn bản mô tả hành động cụ thể. Chuyển sang Dense Retrieval (`gemini-embedding-001`) đưa `Evidence Hit@3` từ `13/15 (86.7%)` lên **`15/15 (100.0%)`**.
  2. **Lỗi 2 (Context Budget Truncation ở `q02`, `q05`, `q09`):** Với `budget=800`, chunk ở Rank 1 (~550 ký tự + header) đã chiếm gần hết ngân sách khiến chunk bằng chứng ở Rank 2 bị `pack_context` cắt bỏ (ở `q09` tổng độ dài 2 chunk là `838 > 800`, chỉ vượt 38 ký tự). Tăng `budget=1500` (`improve1-dense-b1500`) nâng `Context Evidence Rate` từ `12/15 (80.0%)` lên **`15/15 (100.0%)`**. Do đó chốt cấu hình `improve1-dense-b1500`.

---

## 3. Agent và đánh giá

- **Tool, số lượt gọi, điều kiện dừng, cách chọn context và xử lý lỗi:**
  - Agent dùng `Day6RetrieverAdapter` và `GeminiController` (`max_searches=3`). Lượt 1 tìm bằng câu hỏi gốc; lượt 2–3 tự động viết lại truy vấn (Query Rewriting) nếu context chưa đủ bằng chứng; dừng và trả lời kèm `[chunk-id]` khi đủ bằng chứng hoặc từ chối (`abstain`) khi tài liệu không hỗ trợ.

| Cấu hình / split | Tool use | Số lượt gọi | Grounded answer 0/1/2 và trung bình | Citation hợp lệ | Câu có citation | Abstention đúng | Từ chối nhầm |
|---|---|---|---|---|---|---|---|
| **Baseline** / `dev` | 17/17 (100%) | TB 1.29 (13×1, 3×2, 1×3) | `0`: 4, `1`: 1, `2`: 10 — **TB: 1.40/2** | 11/11 (100.0%) | 11/11 (100.0%) | 2/2 (100.0%) | 4/15 (26.7%) |
| **Cấu hình chọn** / `dev` | 17/17 (100%) | TB 1.06 (16×1, 1×2) | `0`: 0, `1`: 0, `2`: 15 — **TB: 2.00/2** | **16/16 (100.0%)** | **15/15 (100.0%)** | **2/2 (100.0%)** | **0/15 (0.0%)** |
| **Baseline** / `test` | 7/7 (100%) | TB 1.14 (6×1, 1×2) | `0`: 0, `1`: 1, `2`: 4 — **TB: 1.80/2** | 5/6 (83.3%) | 5/5 (100.0%) | 2/2 (100.0%) | 0/5 (0.0%) |
| **Cấu hình chọn** / `test` | 7/7 (100%) | TB 1.14 (6×1, 1×2) | `0`: 0, `1`: 0, `2`: 5 — **TB: 2.00/2** | **5/5 (100.0%)** | **5/5 (100.0%)** | **2/2 (100.0%)** | **0/5 (0.0%)** |

| Query ID | Loại câu | Tool call và kết quả | Câu trả lời và citation | Nhãn, lý do |
|---|---|---|---|---|
| `q16` (`test`) | Có đáp án | 1 lượt search -> lấy `hp-book1-ch1-4_p023_paraC_00` (trang 23) | *"Sirius Black lent Hagrid the flying motorcycle `[hp-book1-ch1-4_p023_paraC_00]`."* | **Grade 2**, Citation `[true]`. Trang 23 nêu rõ *"Young Sirius Black lent it to me"*. |
| `q17` (`test`) | Có đáp án | 1 lượt search -> Selected lấy `p029_paraC_00` (trang 29); Baseline chỉ lấy `p028_paraC_03, p028_paraC_04` (trang 28) | **Selected:** *"Aunt Petunia said Dudley would have thirty-nine presents in total `[hp-book1-ch1-4_p029_paraC_00]`."* | **Selected: Grade 2**, Citation `[true]`. **Baseline: Grade 1**, Citation `[true, false]` (trang 28 không có câu nói *"Thirty-nine, sweetums"*). |
| `q18` (`test`) | Có đáp án | 1 lượt search -> lấy `hp-book1-ch1-4_p041_paraC_01` (trang 41) | *"Harry ended up lying flat on his stomach... because Dudley won their furious but silent fight over who would get to listen at the keyhole `[hp-book1-ch1-4_p041_paraC_01]`."* | **Grade 2**, Citation `[true]`. Khớp hoàn toàn với trang 41. |
| `q19` (`test`) | Có đáp án | 1 lượt search -> lấy `hp-book1-ch1-4_p058_paraC_00` (trang 58) | *"You-Know-Who showed up at the village on Halloween ten years ago, and Harry was just a year old at the time `[hp-book1-ch1-4_p058_paraC_00]`."* | **Grade 2**, Citation `[true]`. Đủ cả 3 ý (Halloween, 10 năm trước, 1 tuổi). |
| `q20` (`test`) | Có đáp án | 1 lượt search -> lấy `hp-book1-ch1-4_p059_paraC_01` (trang 59) | *"Hagrid drew a battered pink umbrella from inside his coat and pointed it like a sword at Uncle Vernon `[hp-book1-ch1-4_p059_paraC_01]`."* | **Grade 2**, Citation `[true]`. Khớp chính xác trang 59. |
| `u03` (`test`) | Thiếu bằng chứng | 2 lượt search (viết lại query tìm Sorting Hat / Gryffindor) | *"Không đủ bằng chứng để trả lời."* (`status: "abstain"`, Citations: `[]`) | **Abstention đúng (`true`):** Sự kiện ở Chương 7, không có trong Chương 1–4. |
| `u04` (`test`) | Thiếu bằng chứng | 1 lượt search (thấy đoạn xe máy trang 23 nhưng không có biển số) | *"Không đủ bằng chứng để trả lời."* (`status: "abstain"`, Citations: `[]`) | **Abstention đúng (`true`):** Tài liệu không đề cập biển số xe. |

- **Đường dẫn trace, nhãn, lệnh chạy, thời gian và chi phí:**
  - Kết quả Agent lưu tại `starter/results/{dev,test}-agent-{baseline,selected}/{traces,reviews,summary,run_meta}.json`.
  - Lệnh chạy tái lập:
    - `python3 -m unittest discover -s tests -v`
    - `python3 src/retrievers.py --split dev && python3 src/retrievers.py --split test`
    - `python3 src/agent.py --run-all`
    - `python3 src/generate_reviews_and_metrics.py`
- **Kết quả trước/sau, ví dụ lỗi, đánh đổi và giới hạn:**
  - Cải thiện giúp nâng `Grounded Answer` từ `1.40/2` lên `2.00/2` trên `dev` và từ `1.80/2` lên `2.00/2` trên `test`, đồng thời khắc phục hoàn toàn lỗi từ chối nhầm (`4/15 -> 0/15` trên `dev`) và lỗi trích dẫn thiếu câu nói trực tiếp ở `q17` trên `test`.
