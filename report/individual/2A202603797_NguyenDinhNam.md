# Báo cáo Day 7 — Agentic RAG & Context Engineering

- **Họ và tên:** Nguyễn Đình Nam
- **MSSV:** 2A202603797
- **Lớp:** K5-L3B

---

## 1. Dữ liệu và benchmark

### Nguồn, quyền sử dụng, số trang và số chunk
- **Nguồn tài liệu:** *Harry Potter and the Sorcerer's Stone* (J.K. Rowling), trích xuất từ **Chương 1 đến Chương 4** (trang **12–61**, tổng cộng **50 trang** nội dung văn bản hợp lệ, vượt mức tối thiểu 30 trang của đề bài). Mã nguồn định danh: `hp-book1-ch1-4` (`data/raw/Harry Potter and the Sorcerer's Stone.pdf` từ Day 6).
- **Quyền sử dụng:** Tài liệu và các đoạn trích (chunks) được sử dụng thuần túy cho mục đích thực hành học thuật nội bộ môn học. Dữ liệu đã chuyển đổi sang chuẩn Day 7 được lưu tại [starter/data/converted/chunks.json](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/starter/data/converted/chunks.json).
- **Chiến lược chia đoạn (Chunking) & Số lượng chunk:** Kế thừa **Chiến lược C (`by_paragraph`, tối đa 600 ký tự, không cắt giữa câu)** đã được chọn ở Day 6, gồm **200 chunks** có ID duy nhất theo mẫu `hp-book1-ch1-4_p<trang>_paraC_<thứ_tự>`, giữ nguyên `source_id`, `source`, `page` và `metadata` (`section`, `strategy`, `char_len`, `token_est`).

### Vector store, embedding model, phiên bản và số chiều
- **Embedding Model:** Google Gemini Embedding API — model `models/gemini-embedding-001` (endpoint `https://generativelanguage.googleapis.com/v1beta`), số chiều vector **3072 dimensions**.
- **Vector Store:**
  - **PostgreSQL 16.16 + pgvector 0.8.7** chạy trên Docker (`DATABASE_URL=postgresql://day6:day6_local_only@127.0.0.1:55433/day6_lab`), bảng `document_chunks` (`strategy = 'C'`), truy vấn bằng toán tử khoảng cách Cosine `1 - (embedding <=> %s::vector)`.
  - Đồng thời đồng bộ toàn bộ 200 vector chunk (3072 chiều) và vector câu hỏi vào bộ nhớ đệm cục bộ `starter/data/converted/.embedding_cache.json` để đảm bảo tái lập 100% điểm số Cosine similarity ngay cả khi chạy ở chế độ chỉ dùng thư viện chuẩn Python 3.11+.

### Agent model, cách chạy và phân chia dev/test
- **Agent Controller Model:** Google Gemini API — `gemini-3.5-flash-lite` (kèm cơ chế xoay vòng dự phòng tự động sang `gemini-3.1-flash-lite` / `gemini-3.5-flash` khi gặp giới hạn RPM), `temperature = 0.0`, ép kiểu đầu ra JSON (`responseMimeType: "application/json"`).
- **Phân chia bộ Benchmark (Tổng cộng 24 cases):**
  - Lưu tại [starter/data/converted/questions.json](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/starter/data/converted/questions.json) (20 câu có đáp án dùng cho đánh giá Retrieval) và [starter/data/converted/cases.json](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/starter/data/converted/cases.json) (24 câu gồm 20 câu có đáp án + 4 câu thiếu bằng chứng dùng cho đánh giá Agent):

| Loại câu hỏi | Tập `dev` | Tập `test` | Tổng cộng |
|---|---:|---:|---:|
| **Có đáp án trong tài liệu (`answerable: true`)** | 15 (`q01`–`q15`) | 5 (`q16`–`q20`) | **20** |
| **Không đủ bằng chứng (`answerable: false`)** | 2 (`u01`–`u02`) | 2 (`u03`–`u04`) | **4** |
| **Tổng số câu** | **17** | **7** | **24** |

### Cách xác định câu có/thiếu evidence và tiêu chí chấm
- **Câu có đáp án (`q01`–`q20`):** Mỗi câu gắn với danh sách `gold` chứa `{source_id, page, evidence}`, trong đó chuỗi `evidence` là trích dẫn nguyên văn nằm trọn trong một chunk đúng nguồn và đúng trang (đã kiểm chứng 100% qua hàm `validate()` trong [starter/baseline.py](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/starter/baseline.py)).
- **Câu thiếu bằng chứng (`u01`–`u04`):** Là các câu hỏi cùng chủ đề *Harry Potter* nhưng thông tin không tồn tại trong phạm vi Chương 1–4 đã index:
  - `u01` (`dev`): Giá tiền mua đũa phép tại tiệm Ollivander ở Hẻm Xéo (thuộc Chương 5, ngoài phạm vi Chương 1–4).
  - `u02` (`dev`): Mức lương hàng năm của ông Vernon Dursley tại công ty Grunnings (trang 12 chỉ nêu chức danh giám đốc, không nêu lương).
  - `u03` (`test`): Chiếc nón Phân loại xếp Harry vào nhà nào trong tiệc khai giảng (thuộc Chương 7, ngoài phạm vi Chương 1–4).
  - `u04` (`test`): Biển số chiếc xe máy bay mà Sirius Black cho Hagrid mượn ở Chương 1 (trang 23 chỉ nhắc việc mượn xe, không có biển số).
- **Quy tắc chống rò rỉ dữ liệu:** Tuyệt đối không đưa `gold`, `expected_answer` hay `absence_reason` vào Agent hoặc Retriever. Mọi tinh chỉnh phương pháp và `budget` chỉ thực hiện trên `dev`; tập `test` chỉ chạy sau khi đã chốt cấu hình.

---

## 2. Retrieval và thử nghiệm

### Bảng so sánh các phương pháp Retrieval và cấu hình cải thiện

Toàn bộ 4 phương pháp và 3 cấu hình cải thiện được cài đặt trong [src/retrievers.py](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/src/retrievers.py). Các chỉ số `Hit@1` và `Evidence Hit@3` đều được tính thống nhất ở cùng ngưỡng cắt top-3 trên tập câu hỏi có đáp án (`dev`: $N=15$, `test`: $N=5$). Chi phí dịch vụ embedding phát sinh thêm bằng `$0.00` do tái sử dụng index/cache từ Day 6.

| Cấu hình | Phương pháp, `top_k`, `filter`, `rerank`, `context_budget` | Giả thuyết / thay đổi | Split | Hit@1 | Evidence Hit@3 | Context Evidence Rate | Thời gian (`median_ms`) / Chi phí |
|---|---|---|---|---|---|---|---|
| **Baseline (`tfidf-baseline`)** | Lexical TF-IDF cosine, `top_k=3`, `filter=None`, `budget=800` ký tự | Baseline từ khóa đơn giản của starter | `dev` | 10/15 (66.7%) | 13/15 (86.7%) | 10/15 (66.7%) | 0.34 ms / \$0.00 |
| **Phương pháp 2 (`bm25`)** | Lexical Okapi BM25 ($k_1=1.5, b=0.75$, lọc stopwords), `top_k=3`, `budget=800` | Chuẩn hóa độ dài đoạn văn và bỏ từ dừng tiếng Anh để tăng độ chính xác khớp từ khóa | `dev` | 10/15 (66.7%) | 14/15 (93.3%) | 10/15 (66.7%) | 0.21 ms / \$0.00 |
| **Phương pháp 3 (`dense-day6`)** | Dense Retrieval (`gemini-embedding-001` 3072-d, Cosine), `top_k=3`, `budget=800` | Dùng biểu diễn ngữ nghĩa 3072 chiều từ Day 6 để xử lý các câu hỏi diễn đạt khác nguyên văn | `dev` | **12/15 (80.0%)** | **15/15 (100.0%)** | 12/15 (80.0%) | 43.83 ms / \$0.00 |
| **Phương pháp 4 (`hybrid-rrf-b800`)** | Hybrid RRF (Dense + BM25, $k=60, w_d=1.2, w_l=1.0$), `top_k=3`, `budget=800` | Kết hợp thứ hạng ngữ nghĩa (Dense) và từ khóa (BM25) trên tập 20 ứng viên | `dev` | 11/15 (73.3%) | **15/15 (100.0%)** | 11/15 (73.3%) | 43.86 ms / \$0.00 |
| **Cải thiện 1 (`improve1-dense-b1500`)** *(Đã chọn)* | Dense Retrieval (`gemini-embedding-001`), `top_k=3`, **`budget=1500` ký tự** | Mở rộng context budget từ 800 lên 1500 ký tự để không làm rơi chunk bằng chứng ở Rank 2 | `dev` | **12/15 (80.0%)** | **15/15 (100.0%)** | **15/15 (100.0%)** | 43.70 ms / \$0.00 |
| **Cải thiện 2 (`improve2-hybrid-rrf-b1500`)** | Hybrid RRF (Dense + BM25), `top_k=3`, **`budget=1500` ký tự** | Kết hợp RRF với `budget=1500` để kiểm tra xem hợp nhất thứ hạng có giữ đủ 100% evidence trong context không | `dev` | 11/15 (73.3%) | **15/15 (100.0%)** | **15/15 (100.0%)** | 43.95 ms / \$0.00 |
| **Cải thiện 3 (`improve3-hybrid-rrf-k5-b1800`)** | Hybrid RRF (Dense + BM25), **`top_k=5`**, **`budget=1800` ký tự** | Tăng `top_k=5` và `budget=1800`; không tăng thêm `Hit@1` hay `Context Hit` (vốn đã 15/15) nhưng làm tăng độ dài context trung bình lên 1580 ký tự | `dev` | 11/15 (73.3%) | **15/15 (100.0%)** | **15/15 (100.0%)** | 43.10 ms / \$0.00 |
| **Cấu hình đã chọn (`improve1-dense-b1500`)** | Dense Retrieval (`gemini-embedding-001`), `top_k=3`, **`budget=1500` ký tự** | Đánh giá cấu hình đã chốt trên tập `test` độc lập | **`test`** | **4/5 (80.0%)** | **5/5 (100.0%)** | **5/5 (100.0%)** | 42.75 ms / \$0.00 |
| **Baseline (`tfidf-baseline`)** | Lexical TF-IDF cosine, `top_k=3`, `budget=800` ký tự | Đánh giá baseline trên tập `test` để đối chiếu | **`test`** | 3/5 (60.0%) | 4/5 (80.0%) | 4/5 (80.0%) | 0.41 ms / \$0.00 |

### Phân tích 2 lỗi cụ thể trên tập `dev` và lý do chọn cấu hình

1. **Lỗi 1 — Lệch từ vựng ngữ nghĩa (Lexical Mismatch) ở `q05` và `q12` trong Baseline TF-IDF:**
   - **Hiện tượng:** Trên tập `dev`, `tfidf-baseline` hoàn toàn không tìm thấy chunk bằng chứng trong top-3 (`hit3 = false`) đối với câu `q05` (*"How did Dumbledore plan to explain Harry’s background to his aunt and uncle when leaving him on their doorstep?"*) và `q12` (*"Where did Uncle Vernon sleep at night to prevent Harry from sneaking downstairs to collect the morning mail?"*).
   - **Nguyên nhân:** Câu hỏi dùng từ khái quát (*"explain Harry's background"*, *"prevent Harry from sneaking downstairs"*), trong khi văn bản gốc ở `hp-book1-ch1-4_p024_paraC_00` (trang 24) và `hp-book1-ch1-4_p044_paraC_00` (trang 44) mô tả hành động cụ thể (*"took a letter out of his cloak, tucked it inside Harry’s blankets"* và *"lying at the foot of the front door in a sleeping bag"*). TF-IDF bị nhiễu bởi các đoạn khác có lặp tên nhân vật *Dumbledore*, *Harry*, *Uncle Vernon*.
   - **Cách thử & Kết quả:** Chuyển sang **BM25 (`bm25`)** giúp lọc bỏ từ dừng và cứu được câu `q05` (`Hit@3` tăng từ `13/15` lên `14/15`), nhưng vẫn trượt `q12`. Khi chuyển sang **Dense Retrieval (`dense-day6`)** và **Hybrid RRF (`hybrid-rrf-b800`)**, cả `q05` và `q12` đều được tìm thấy trong top-2, nâng `Evidence Hit@3` từ `13/15 (86.7%)` lên tuyệt đối **`15/15 (100.0%)`** và `Hit@1` từ `10/15 (66.7%)` lên **`12/15 (80.0%)`**.

2. **Lỗi 2 — Cắt cụt ngữ cảnh (Context Budget Truncation) làm rơi bằng chứng ở Rank 2 (`q02`, `q05`, `q09`):**
   - **Hiện tượng:** Ở cấu hình `dense-day6` (`budget=800`), dù `Evidence Hit@3` đạt **15/15 (100.0%)**, chỉ số `Context Evidence Rate` chỉ đạt **12/15 (80.0%)** — tức là có 3 câu (`q02`, `q05`, `q09`) tìm được bằng chứng trong top-3 nhưng bằng chứng lại **không có mặt trong context cuối** gửi cho LLM!
   - **Nguyên nhân:** Kiểm tra [starter/results/dev-dense-day6/traces.json](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/starter/results/dev-dense-day6/traces.json) cho thấy ở cả 3 câu `q02`, `q05`, `q09`, chunk chứa bằng chứng chuẩn nằm ở **Rank 2**:
     - `q02`: Rank 1 (`p014_paraC_01`, 526 ký tự + 64 ký tự header = 590 ký tự) + Rank 2 (`p014_paraC_00`, 399 + 64 = 463 ký tự) = **1,055 ký tự > 800**.
     - `q05`: Rank 1 (`p022_paraC_00`, 550 + 64 = 614 ký tự) + Rank 2 (`p024_paraC_00`, 497 + 64 = 561 ký tự) = **1,177 ký tự > 800**.
     - `q09`: Rank 1 (`p034_paraC_00`, 329 + 64 = 393 ký tự) + Rank 2 (`p034_paraC_01`, 379 + 64 = 443 ký tự) = **838 ký tự > 800** (vượt ngân sách đúng **38 ký tự**!).
     Do Chiến lược C ở Day 6 thiết kế mỗi chunk có độ dài tối đa 600 ký tự, ngân sách `budget=800` ký tự của starter thực chất chỉ chứa nổi **đúng 1 chunk** (Rank 1) và loại bỏ hoàn toàn Rank 2 và Rank 3.
   - **Cách thử & Kết quả:** Thử nghiệm **Cải thiện 1 (`improve1-dense-b1500`)** và **Cải thiện 2 (`improve2-hybrid-rrf-b1500`)** với `budget=1500` ký tự (tương đương ~300–350 tokens, đủ chứa 2–3 chunks của `top_k=3`). Kết quả: `Context Evidence Rate` trên `dev` tăng vọt từ `12/15 (80.0%)` lên **`15/15 (100.0%)`** mà không làm tăng thời gian truy xuất (`43.70 ms`). Thử nghiệm thêm **Cải thiện 3 (`improve3-hybrid-rrf-k5-b1800`)** với `top_k=5, budget=1800` không làm tăng thêm độ chính xác (vì `top_k=3, budget=1500` đã đạt 100% `Context Evidence Rate`) nhưng làm kích thước context trung bình tăng từ `1157` lên `1580` ký tự (tốn thêm token đầu vào cho Agent).

- **Quyết định chọn cấu hình (`improve1-dense-b1500`):** Chọn **Dense Retrieval (`gemini-embedding-001`) với `top_k=3, budget=1500`** vì đạt điểm cao nhất trên mọi tiêu chí ở tập `dev`: `Hit@1 = 12/15 (80.0%)`, `Evidence Hit@3 = 15/15 (100.0%)`, `Context Evidence Rate = 15/15 (100.0%)` với kích thước context gọn (`1157.27` ký tự trung bình).

### Chấm điểm thủ công Context (thang 0/1/2) trên 5 câu `test` có đáp án (`q16`–`q20`)

Theo yêu cầu tại mục 2 của [BENCHMARK.md](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/BENCHMARK.md), bảng dưới đây đối chiếu thủ công chất lượng ngữ cảnh (`0` = không có evidence; `1` = có nhưng thiếu điều kiện hoặc nguồn trực tiếp; `2` = đủ evidence và nguồn) giữa **Baseline (`tfidf-baseline`)** và **Cấu hình đã chọn (`improve1-dense-b1500`)** trên tập `test`:

| Query ID | Context IDs trong Baseline (`budget=800`) | Điểm Context Baseline | Context IDs trong Cấu hình chọn (`budget=1500`) | Điểm Context Cấu hình chọn | Lý do đối chiếu thủ công |
|---|---|---:|---|---:|---|
| `q16` | `['hp-book1-ch1-4_p023_paraC_00']` | **2** | `['hp-book1-ch1-4_p023_paraC_00', 'hp-book1-ch1-4_p022_paraC_02']` | **2** | Cả hai đều chứa `p023_paraC_00` (trang 23) nêu rõ *"Young Sirius Black lent it to me"*. |
| `q17` | `['hp-book1-ch1-4_p028_paraC_03', 'hp-book1-ch1-4_p028_paraC_04']` | **1** | `['hp-book1-ch1-4_p028_paraC_03', 'hp-book1-ch1-4_p029_paraC_00']` | **2** | Baseline chỉ lấy được trang 28 (nêu Dudley đếm được 37 món quà và Petunia hứa mua thêm 2 món), **thiếu đoạn trang 29 (`p029_paraC_00`)** nơi dì Petunia nói trực tiếp tổng số *"Thirty-nine, sweetums"* -> chấm **1**. Cấu hình chọn lấy được cả `p028_paraC_03` và `p029_paraC_00` -> chấm **2**. |
| `q18` | `['hp-book1-ch1-4_p041_paraC_01']` | **2** | `['hp-book1-ch1-4_p041_paraC_01', 'hp-book1-ch1-4_p041_paraC_02']` | **2** | Cả hai đều chứa `p041_paraC_01` (trang 41) nêu rõ Dudley thắng cuộc chiến giành lỗ khóa nên Harry phải nằm sát sàn nghe qua khe cửa. |
| `q19` | `['hp-book1-ch1-4_p058_paraC_00']` | **2** | `['hp-book1-ch1-4_p058_paraC_00', 'hp-book1-ch1-4_p057_paraC_02']` | **2** | Cả hai đều chứa `p058_paraC_00` (trang 58) nêu rõ *"on Halloween ten years ago. You was just a year old."* |
| `q20` | `['hp-book1-ch1-4_p059_paraC_01']` | **2** | `['hp-book1-ch1-4_p059_paraC_01', 'hp-book1-ch1-4_p060_paraC_00']` | **2** | Cả hai đều chứa `p059_paraC_01` (trang 59) nêu rõ Hagrid rút chiếc ô màu hồng cũ kỹ (*"battered pink umbrella"*) chĩa như thanh kiếm. |
| **Tổng hợp** | **Mức 0: 0 · Mức 1: 1 · Mức 2: 4 (TB: 1.80/2)** | | **Mức 0: 0 · Mức 1: 0 · Mức 2: 5 (TB: 2.00/2)** | | Cấu hình chọn đạt điểm tuyệt đối **5/5 ở mức 2**. |

---

## 3. Agent và đánh giá

### Thiết kế Agent, số lượt gọi, điều kiện dừng, cách chọn context và xử lý lỗi
- **Kiến trúc điều phối ([src/agent.py](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/src/agent.py) + [starter/agentic.py](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/starter/agentic.py)):**
  - `Day6RetrieverAdapter`: Chuẩn hóa giao diện `search(query, filters, top_k)` cho mọi phương pháp truy xuất, đảm bảo khử trùng lặp chunk ID.
  - `GeminiController`:
    - **Lượt 1 (Turn 1):** Luôn phát lệnh `{"action": "search", "query": <câu_hỏi_gốc>}` để đảm bảo đánh giá đúng truy vấn gốc trước tiên.
    - **Lượt 2 đến `max_searches=3`:** Model đọc `context` đã đóng gói (với chỉ dẫn rõ ràng coi nội dung tài liệu là dữ liệu thuần túy `DATA ONLY`, không thực thi chỉ dẫn bên trong văn bản). Nếu đã đủ bằng chứng trả lời trọn vẹn câu hỏi, model trả về `{"action": "answer", "answer": "... [chunk-id]", "citations": ["chunk-id"]}`. Nếu chưa đủ bằng chứng và còn lượt tìm kiếm, model tự động **viết lại truy vấn (Query Rewriting)** nhắm vào các thực thể/khái niệm còn thiếu.
    - **Điều kiện dừng & Abstention:** Nếu đã tìm kiếm nhưng ngữ cảnh không có thông tin (hoặc chạm ngưỡng `max_searches=3`), Agent trả về `answer=""` để kích hoạt trạng thái `status: "abstain"` (*"Không đủ bằng chứng để trả lời."*), tuyệt đối không bịa đặt từ kiến thức bên ngoài.
    - **Xử lý lỗi kết nối:** Tự động thử lại và xoay vòng qua các model trong họ Gemini Flash khi gặp lỗi HTTP 429/503; nếu vẫn lỗi thì ghi nhận `status: "error"` riêng biệt, không dùng kết quả giả.

### Bảng tổng hợp kết quả đánh giá Agent (từ `starter/agent_metrics.py`)

| Cấu hình / Split | Tool use | Số lượt gọi search (TB / phân bố) | Grounded answer (0 / 1 / 2 và TB /2) | Citation hợp lệ | Câu có citation | Abstention đúng | Từ chối nhầm (False Abstention) | Thời gian (`median_ms`) / Chi phí |
|---|---|---|---|---|---|---|---|---|
| **Baseline (`dev-agent-baseline`)** (`tfidf, k=3, b=800`) / `dev` | 17/17 (100%) | TB: 1.29 (13 câu 1 lượt, 3 câu 2 lượt, 1 câu 3 lượt) | `0`: 4, `1`: 1, `2`: 10 — **TB: 1.40 / 2.00** | 11/11 (100.0%) | 11/11 (100.0%) | 2/2 (100.0%) | **4/15 (26.7%)** | 2660.11 ms / \$0.003175 |
| **Cấu hình chọn (`dev-agent-selected`)** (`dense, k=3, b=1500`) / `dev` | 17/17 (100%) | TB: 1.06 (16 câu 1 lượt, 1 câu 2 lượt) | `0`: 0, `1`: 0, `2`: 15 — **TB: 2.00 / 2.00** | **16/16 (100.0%)** | **15/15 (100.0%)** | **2/2 (100.0%)** | **0/15 (0.0%)** | 1709.52 ms / \$0.003411 |
| **Baseline (`test-agent-baseline`)** (`tfidf, k=3, b=800`) / **`test`** | 7/7 (100%) | TB: 1.14 (6 câu 1 lượt, 1 câu 2 lượt) | `0`: 0, `1`: 1, `2`: 4 — **TB: 1.80 / 2.00** | 5/6 (83.3%) | 5/5 (100.0%) | 2/2 (100.0%) | 0/5 (0.0%) | 3197.15 ms / \$0.001233 |
| **Cấu hình chọn (`test-agent-selected`)** (`dense, k=3, b=1500`) / **`test`** | 7/7 (100%) | TB: 1.14 (6 câu 1 lượt, 1 câu 2 lượt) | `0`: 0, `1`: 0, `2`: 5 — **TB: 2.00 / 2.00** | **5/5 (100.0%)** | **5/5 (100.0%)** | **2/2 (100.0%)** | **0/5 (0.0%)** | 1218.46 ms / \$0.001394 |

### Bảng chi tiết từng câu trên tập `test` (kèm các ca điển hình trên `dev`)

| Query ID | Loại câu | Tool call và kết quả | Câu trả lời và citation (Cấu hình đã chọn vs Baseline) | Nhãn, lý do kiểm tra thủ công |
|---|---|---|---|---|
| `q16` (`test`) | Có đáp án | **1 lượt search:** Truy vấn gốc lấy ngay `hp-book1-ch1-4_p023_paraC_00` ở Rank 1 (cả Baseline và Selected). | **Selected:** *"Sirius Black lent Hagrid the flying motorcycle `[hp-book1-ch1-4_p023_paraC_00]`."*<br>**Baseline:** *"Young Sirius Black lent Hagrid the flying motorcycle `[hp-book1-ch1-4_p023_paraC_00]`."* | **Selected: Grade 2**, Citation `[true]`.<br>**Baseline: Grade 2**, Citation `[true]`. Đoạn trang 23 ghi rõ *"Young Sirius Black lent it to me"*. |
| `q17` (`test`) *(Ca lỗi Baseline)* | Có đáp án | **1 lượt search:**<br>- **Baseline (TF-IDF, b=800):** Chỉ lấy `p028_paraC_03` và `p028_paraC_04` (trang 28), rơi mất `p029_paraC_00` (trang 29).<br>- **Selected (Dense, b=1500):** Lấy cả `p028_paraC_03` và `p029_paraC_00`. | **Selected:** *"Aunt Petunia said Dudley would have thirty-nine presents in total `[hp-book1-ch1-4_p029_paraC_00]`."*<br>**Baseline:** *"After promising to buy him two more presents, Aunt Petunia brought his total to thirty-nine presents `[hp-book1-ch1-4_p028_paraC_03] [hp-book1-ch1-4_p028_paraC_04]`."* | **Selected: Grade 2**, Citation `[true]` (trích dẫn đúng trang 29 *"Thirty-nine, sweetums"*).<br>**Baseline: Grade 1**, Citation `[true, false]`: minh họa điển hình việc **ID hợp lệ trong context nhưng nguồn không hỗ trợ trực tiếp** (`p028_paraC_04` chỉ có câu *"Two more presents. Is that all right?"*, hoàn toàn không có con số 39). |
| `q18` (`test`) | Có đáp án | **1 lượt search:** Lấy `hp-book1-ch1-4_p041_paraC_01` (trang 41) ở Rank 1. | **Selected:** *"Harry ended up lying flat on his stomach to listen at the crack between the door and floor because Dudley won their furious but silent fight over who would get to listen at the keyhole `[hp-book1-ch1-4_p041_paraC_01]`."* | **Selected & Baseline: Grade 2**, Citation `[true]`. Khớp hoàn toàn với bằng chứng trang 41. |
| `q19` (`test`) | Có đáp án | **1 lượt search:** Lấy `hp-book1-ch1-4_p058_paraC_00` (trang 58) ở Rank 1. | **Selected:** *"You-Know-Who showed up at the village on Halloween ten years ago, and Harry was just a year old at the time `[hp-book1-ch1-4_p058_paraC_00]`."* | **Selected & Baseline: Grade 2**, Citation `[true]`. Đủ cả 3 điều kiện: dịp lễ (Halloween), số năm (10 năm trước) và tuổi của Harry (1 tuổi). |
| `q20` (`test`) | Có đáp án | **1 lượt search:** Lấy `hp-book1-ch1-4_p059_paraC_01` (trang 59) ở Rank 1. | **Selected:** *"Hagrid drew a battered pink umbrella from inside his coat and pointed it like a sword at Uncle Vernon `[hp-book1-ch1-4_p059_paraC_01]`."* | **Selected & Baseline: Grade 2**, Citation `[true]`. Khớp chính xác chi tiết chiếc ô màu hồng cũ kỹ trang 59. |
| `u03` (`test`) *(Ca thiếu evidence)* | Thiếu bằng chứng | **2 lượt search (Multi-turn):**<br>1. Câu hỏi gốc về Sorting Hat.<br>2. Viết lại query: `"Harry Potter Sorting Hat house Gryffindor banquet"`. | **Selected & Baseline:** `status: "abstain"` — *"Không đủ bằng chứng để trả lời."* (Citations: `[]`) | **Abstention đúng (`true`):** Agent chủ động thử tìm lại lần 2 với từ khóa mới, xác nhận các đoạn Chương 1–4 không nhắc tới lễ Phân loại (Chương 7) và từ chối trả lời thay vì dùng kiến thức tiền huấn luyện để đoán "Gryffindor". |
| `u04` (`test`) *(Ca thiếu evidence)* | Thiếu bằng chứng | **1 lượt search:** Tìm thấy đoạn trang 23 (`p023_paraC_00`) nói về chiếc xe máy bay của Sirius Black nhưng kiểm tra thấy không có biển số xe. | **Selected & Baseline:** `status: "abstain"` — *"Không đủ bằng chứng để trả lời."* (Citations: `[]`) | **Abstention đúng (`true`):** Đoạn văn nói về chiếc xe đã nằm ngay trong context nên Agent không cần tìm lại mà kết luận ngay tài liệu không ghi biển số xe. |
| `q05` (`dev`) *(Ca cải thiện Multi-chunk)* | Có đáp án | **1 lượt search:**<br>- **Baseline:** Chỉ có `p022_paraC_00` (trang 22).<br>- **Selected:** Có cả `p022_paraC_00` (trang 22) và `p024_paraC_00` (trang 24). | **Selected:** *"Dumbledore planned to have Harry's aunt and uncle explain everything to him when he was older, and he wrote them a letter which he tucked inside Harry's blankets on their doorstep `[hp-book1-ch1-4_p022_paraC_00] [hp-book1-ch1-4_p024_paraC_00]`."* | **Selected: Grade 2**, Citation `[true, true]` (tổng hợp từ 2 trang 22 và 24).<br>**Baseline: Grade 1**, Citation `[true]` (thiếu hành động đặt thư vào chăn trên bậc cửa ở trang 24). |
| `q09` (`dev`) *(Ca lỗi Budget Baseline)* | Có đáp án | **Baseline gọi 3 lượt search** nhưng `p034_paraC_00` ở lượt 1 đã chiếm chỗ khiến `p034_paraC_01` không lọt vào `budget=800`. **Selected gọi 1 lượt search** lấy đủ cả hai. | **Selected:** *"The snake had never been to Brazil because it was bred in the zoo `[hp-book1-ch1-4_p034_paraC_01]`."*<br>**Baseline:** `status: "abstain"` (*"Không đủ bằng chứng để trả lời."*) | **Selected: Grade 2**, Citation `[true]`.<br>**Baseline: Grade 0 (Từ chối nhầm)** do hiệu ứng nghẽn ngân sách `budget=800` qua nhiều lượt tìm kiếm. |

### Đường dẫn trace, nhãn, lệnh chạy, thời gian và chi phí

- **Đường dẫn các file kết quả & trace đã lưu:**
  - Dữ liệu chuẩn hóa từ Day 6:
    - [starter/data/converted/chunks.json](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/starter/data/converted/chunks.json)
    - [starter/data/converted/questions.json](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/starter/data/converted/questions.json)
    - [starter/data/converted/cases.json](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/starter/data/converted/cases.json)
  - Trace & Summary của Retrieval (`dev` và `test`):
    - `starter/results/dev-tfidf-baseline/` · `starter/results/dev-bm25/` · `starter/results/dev-dense-day6/` · `starter/results/dev-hybrid-rrf-b800/`
    - `starter/results/dev-improve1-dense-b1500/` · `starter/results/dev-improve2-hybrid-rrf-b1500/` · `starter/results/dev-improve3-hybrid-rrf-k5-b1800/`
    - `starter/results/test-tfidf-baseline/` · `starter/results/test-improve1-dense-b1500/`
  - Trace, Reviews & Summary của Agent (`dev` và `test`):
    - Dev Baseline: [traces.json](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/starter/results/dev-agent-baseline/traces.json) · [reviews.json](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/starter/results/dev-agent-baseline/reviews.json) · [summary.json](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/starter/results/dev-agent-baseline/summary.json)
    - Dev Selected: [traces.json](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/starter/results/dev-agent-selected/traces.json) · [reviews.json](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/starter/results/dev-agent-selected/reviews.json) · [summary.json](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/starter/results/dev-agent-selected/summary.json)
    - Test Baseline: [traces.json](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/starter/results/test-agent-baseline/traces.json) · [reviews.json](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/starter/results/test-agent-baseline/reviews.json) · [summary.json](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/starter/results/test-agent-baseline/summary.json)
    - Test Selected: [traces.json](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/starter/results/test-agent-selected/traces.json) · [reviews.json](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/starter/results/test-agent-selected/reviews.json) · [summary.json](file:///Users/mac/K5-L3-Day07-Retrieval-Context-Engineering/starter/results/test-agent-selected/summary.json)

- **Lệnh chạy tái lập toàn bộ kết quả:**
  ```bash
  # 1. Chạy kiểm thử unit tests (17/17 tests)
  python3 -m unittest discover -s tests -v

  # 2. Chạy benchmark các phương pháp Retrieval & Context trên dev và test
  python3 src/retrievers.py --split dev
  python3 src/retrievers.py --split test

  # 3. Chạy Agentic RAG cho Baseline và Cấu hình đã chọn trên dev và test
  python3 src/agent.py --run-all

  # 4. Xuất nhãn kiểm tra thủ công (reviews.json) và tổng hợp metrics qua starter/agent_metrics.py
  python3 src/generate_reviews_and_metrics.py
  ```

### Kết quả trước/sau, đánh đổi và giới hạn
- **Kết quả trước và sau cải thiện:**
  - Trên tập `dev`, việc chuyển từ Baseline (`tfidf, budget=800`) sang Cấu hình chọn (`dense, budget=1500`) giúp tăng `Context Evidence Rate` từ **66.7% (10/15)** lên **100.0% (15/15)**, triệt tiêu hoàn toàn tỷ lệ từ chối nhầm (`False Abstention` giảm từ **26.7% (4/15)** xuống **0.0% (0/15)**), và nâng điểm trung bình câu trả lời `Grounded Answer` từ **1.40/2.00** lên **2.00/2.00**. Đồng thời số lượt gọi tool trung bình giảm từ `1.29` xuống `1.06` lượt/câu (nhờ tìm trúng bằng chứng ngay từ lượt đầu), giúp thời gian phản hồi trung vị giảm từ `2660 ms` xuống `1710 ms`.
  - Trên tập `test` độc lập, Cấu hình chọn đạt **100% ở mọi chỉ số**: `Evidence Hit@3 = 5/5 (100%)`, `Context Evidence Rate = 5/5 (100%)`, `Grounded Answer = 2.00/2.00`, `Citation Validity = 5/5 (100%)`, và `Abstention = 2/2 (100%)` (so với Baseline đạt `Grounded Answer = 1.80/2.00` và `Citation Validity = 83.3%`).
- **Đánh đổi (Trade-offs):**
  - Tăng `budget` từ `800` lên `1500` ký tự làm độ dài context trung bình tăng khoảng gấp đôi (~`555` lên ~`1157` ký tự), nhưng tổng chi phí LLM trên cả tập `test` (7 câu) chỉ tăng từ `$0.001233` lên `$0.001394` (chênh lệch chưa tới `$0.0002`), đổi lại thời gian chạy nhanh hơn gần 2.6 lần (`1218 ms` so với `3197 ms`) do Agent không phải gọi thêm lượt tìm kiếm lại trong vô vọng.
- **Giới hạn hiện tại:**
  - Hàm `pack_context` mặc định trong `starter/baseline.py` ưu tiên giữ các chunk theo thứ tự xuất hiện trong `candidates`. Nếu `budget` quá hẹp, chunk không liên quan từ lượt tìm kiếm thứ nhất có thể chiếm hết ngân sách và chặn các chunk tốt hơn ở lượt tìm kiếm thứ hai. Mở rộng `budget=1500` giải quyết triệt để vấn đề này cho `top_k=3`, nhưng với các bài toán multi-hop dài hơn cần kết hợp cơ chế xếp hạng lại (rerank) toàn bộ `candidates` qua các lượt trước khi đóng gói context.
