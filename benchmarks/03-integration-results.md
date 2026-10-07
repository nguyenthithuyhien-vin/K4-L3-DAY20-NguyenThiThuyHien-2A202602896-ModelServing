# 03 - Integrate: RAG pipeline run

Host `Darwin-arm64` · llama.cpp `b10488` ·
retrieval backend: **keyword overlap** · 3 queries

| Query | Contexts retrieved | embed (ms) | retrieve (ms) | llm (ms) | total (ms) |
|:--|--:|--:|--:|--:|--:|
| Why is goodput more useful than raw throughp... | goodput, paged, radix | 0.0 | 0.0 | 763.7 | 763.7 |
| What problem does PagedAttention actually so... | paged, radix, disagg | 0.0 | 0.0 | 530.2 | 530.2 |
| When does splitting prefill and decode help?... | disagg, radix, batching | 0.0 | 0.0 | 523.2 | 523.3 |

Mean per stage (ms): embed **0.0** · retrieve **0.0** ·
llm **605.7** · total **605.7**
Dominant stage: **llm** (100% of total)

## Answers returned

**Why is goodput more useful than raw throughput?**

> Goodput@SLO counts only the requests per second that met the TTFT and TPOT targets. Throughput at saturation ignores SLOs.

**What problem does PagedAttention actually solve?**

> PagedAttention stores the KV cache in non-contiguous pages, removing the internal fragmentation that wasted most GPU memory.

**When does splitting prefill and decode help?**

> Splitting prefill and decode helps because prefill is compute-bound and decode is memory-bandwidth-bound.


## Which N16-N19 pieces are real

- **Khai báo tính hiện thực của các thành phần N16–N19:**
  - **N16 (Chunking / Text splitting):** **Stubbed** (dùng tài liệu pre-chunked dựng sẵn trong bộ nhớ của script).
  - **N17 (Embedding Generation):** **Stubbed** (sử dụng cơ chế đếm trùng lặp từ khóa / keyword overlap fallback, không nạp embedding model rời).
  - **N18 (Vector Store / Retrieval):** **Stubbed** (sắp xếp overlap score trực tiếp trong bộ nhớ thay vì truy vấn Vector DB phân tán như Qdrant/Milvus/Chroma).
  - **N19 (Model Serving Endpoint):** **Real** (gửi HTTP request thực tế tới `llama-server` phục vụ model `Gemma 4 E2B` trên port 8080 qua chuẩn OpenAI-compatible).

- **Phân tích Dominant Stage:**
  - Chặng LLM chiếm ưu thế tuyệt đối (**`llm`: 605.7 ms, chiếm 100% tổng thời gian** pipeline; các chặng embed và retrieve xấp xỉ 0.0 ms).
  - Con số này hoàn toàn đúng với kỳ vọng kiến trúc: việc tìm kiếm từ khóa cục bộ diễn ra trong vài chục microsecond, trong khi LLM phải thực hiện prefill ~113–149 tokens context và sau đó decode tuần tự 23–30 tokens qua GPU Metal.

- **Chiến lược cắt giảm 50% độ trễ (Halve Pipeline Latency):**
  - Vì LLM chiếm 100% latency, việc tối ưu embed hay retrieve sẽ không đem lại hiệu quả đo đạc được (Định luật Amdahl). Bắt buộc phải **tấn công trực tiếp vào LLM stage**:
    1. **Áp dụng Prompt / Prefix Caching:** Hệ thống RAG thường dùng chung System Prompt và các đoạn tài liệu tham khảo cố định. Bằng cách kích hoạt prompt caching trong `llama-server`, server tái sử dụng KV cache của phần prompt đã tính toán, giảm chi phí prefill từ ~163–244 ms xuống gần 0 ms cho các token trùng khớp.
    2. **Áp dụng Speculative Decoding (ví dụ MTP head của Gemma 4 E2B):** Trong tổng 605.7 ms của LLM, pha decode chiếm ~350–430 ms (chiếm >65% thời gian). Do decode bị nghẽn bởi memory bandwidth, kỹ thuật suy luận suy đoán (Speculative Decoding) cho phép xác thực đồng thời nhiều token trong một forward pass, giúp tăng tốc độ sinh từ ~65 tok/s lên >100 tok/s, từ đó cắt giảm một nửa latency decode.
