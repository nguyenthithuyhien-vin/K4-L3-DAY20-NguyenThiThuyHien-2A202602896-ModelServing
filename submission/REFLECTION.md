# Reflection — Day 20 Lab (Personal Report)

> **Đây là báo cáo cá nhân.** Số liệu của bạn **không** so sánh được với bạn cùng lớp
> — chỉ so **before vs after trên chính máy bạn**. Rubric chấm độ rõ ràng của setup,
> đo lường và **lập luận**, không chấm tốc độ tuyệt đối.
>
> `make verify` sẽ fail nếu còn placeholder chưa điền. Đó là cố ý.

**Họ Tên:** Nguyễn Thị Thúy Hiền
**MSSV:** 2A202602896
**Cohort:** AICB-K4
**Ngày submit:** 2026-10-07

---

## 1. Hardware & runtime  *(rubric 1, 2 — 10 điểm)*

> Từ `make probe`. Paste output hoặc điền tay.

- **OS:** macOS 25.6.0 (Darwin arm64)
- **CPU:** Apple M4 Pro
- **Cores:** 12 physical / 12 logical
- **CPU extensions:** NEON
- **RAM:** 24.0 GB
- **Accelerator:** Apple Metal (MTL0: Apple M4 Pro)
- **llama.cpp asset đã tải:** llama-b10488-bin-macos-arm64.tar.gz
- **Model đã dùng:** Gemma 4 E2B (`LAB_MODEL=gemma4-e2b`)
- **Quantization:** UD-Q4_K_XL (primary) + UD-Q2_K_XL (compare)

**Chạy ở đâu:** laptop của tôi

**Setup story** (≤ 80 chữ): Quá trình setup diễn ra trên macOS chip M4 Pro. Thư viện huggingface_hub gặp lỗi kết nối CAS khi tải file lớn, tôi đã dùng `curl -L -C -` theo hướng dẫn `docs/MANUAL-DOWNLOAD.md` để tải đầy đủ 2 file weights GGUF và sinh manifest `active.json` thành công.

---

## 2. Đo lường  *(rubric 3, 4, 5 — 20 điểm)*

> Paste bảng từ `benchmarks/01-quickstart-results.md` (`make bench` tự sinh).

| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |
|---|--:|--:|--:|--:|--:|--:|
| UD-Q4_K_XL | 2.97 | 3069 | 85 / 228 | 15.2 / 15.6 | 1041 / 1179 / 1179 | 65.8 |
| UD-Q2_K_XL | 2.24 | 3039 | 82 / 309 | 13.1 / 14.6 | 891 / 1156 / 1156 | 76.5 |

**Quan sát** (≤ 60 chữ): Bản 2-bit decode nhanh hơn 1.16x (76.5 vs 65.8 tok/s) và nhẹ hơn 0.73 GB do giảm tải memory bandwidth. Tuy nhiên chất lượng câu trả lời bị suy thoái ngữ nghĩa rõ rệt. Với máy 24 GB RAM, bản UD-Q4_K_XL vượt trội và đáng dùng hơn nhiều.

---

## 3. Serving under load  *(rubric 8, 9, 10 — 20 điểm)*

> Từ `benchmarks/02-server-results.md` (`make load-report`).

| Users | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Eff. concurrency | Failures |
|--:|--:|--:|--:|--:|--:|--:|
| 10 | 1.75 | 4600 | 6400 | 9000 | 8.2 | 0.0% |
| 50 | 1.59 | 27000 | 33000 | 34000 | 34.7 | 0.0% |

- **Offered load tăng 5×, throughput thực tăng:** 0.91×
- **P95 tăng:** 5.16×
- **Effective concurrency ở 50 users:** 34.7 so với `--parallel` = 4 slots

**Peak `llamacpp:n_busy_slots_per_decode`** (từ `make metrics` khi `make load-50` đang chạy): 3.93 / 4 slots

**Saturation reading** (≤ 80 chữ): Server bão hòa ở ~10-12 users khi throughput chững lại ở 1.75 RPS và giảm còn 1.59 RPS ở 50 users, trong khi P95 tăng 5.16x. Độ trễ tăng vọt là Queue Time vì Effective Concurrency (34.7) vượt xa 4 slots và requests_deferred = 46. Để nâng Goodput@SLO, tôi sẽ tăng `--parallel` (lên 8 slots) vì RAM 24 GB còn trống nhiều, giúp gộp nhiều token hơn vào mỗi đợt stream weights của decode step.

---

## 4. Integration  *(rubric 12, 13 — 15 điểm)*

> Từ `make pipeline`. Nói thật cái nào real, cái nào stub — stub **không** mất điểm.

| Day | Piece | Real hay stub? |
|---|---|---|
| N16 Cloud/IaC | Pre-chunked corpus | stub |
| N17 Data pipeline | Keyword overlap fallback | stub |
| N18 Lakehouse | Memory score sorting | stub |
| N19 Vector + features | Memory context retrieval | stub |
| N20 Serving | `llama-server` | real |

**Latency split** (mean của 3 query, từ output của `pipeline.py`):

- embed: 0.0 ms
- retrieve: 0.0 ms
- llm: 605.7 ms
- **stage chiếm nhiều nhất:** llm (100% của total)

**Reflection** (≤ 60 chữ): Bottleneck hoàn toàn ở LLM (100%), đúng kỳ vọng vì search keyword gần như 0 ms còn LLM phải prefill và decode qua Metal. Để giảm latency 2x, tôi sẽ áp dụng prompt caching cho prompt cố định và speculative decoding (MTP head) để tăng tốc pha decode.

---

## 5. The single change that mattered most  *(rubric 11 — 10 điểm)*

> **Phần quan trọng nhất của report.** Không cần bonus track: `make tune` đã cho bạn
> một before/after thật (`benchmarks/01-tuning-tg128.md`). Đổi quantization,
> `LAB_N_CTX`, hay `--parallel` rồi đo lại cũng được.

**Change:** Tối ưu số luồng tính toán CPU từ -t 12 xuống -t 6 (tối ưu cụm Performance cores)

```
before:  65.6 tok/s
after:   86.2 tok/s
speedup: 1.31×
```

**Tại sao nó work** (1–2 đoạn — đây là phần grader đọc kỹ nhất):

Trên chip Apple M4 Pro (12 cores), CPU được cấu tạo bất đối xứng gồm cụm Performance cores (P-cores) và Efficiency cores (E-cores). Khi để mặc định 12 luồng (`-t 12`), scheduler phân bổ thread lên cả các E-core yếu hơn. Trong kiến trúc tính toán song song GGML, các luồng phải đợi nhau tại điểm đồng bộ barrier (barrier synchronization). Do đó, tốc độ của toàn bộ bước tính toán bị ghì lại bởi luồng chạy trên E-core (hiệu ứng straggler).

Khi hạ xuống `-t 6`, toàn bộ 6 worker threads chạy hoàn toàn trên các P-cores mạnh nhất, loại bỏ hoàn toàn hiện tượng straggler và giảm xung đột bộ nhớ đệm cache L2/L3 giữa các core cluster, giúp tốc độ decode tăng vọt từ 65.6 lên 86.2 tok/s (speedup 1.31x).

---

## 6. Bonus  *(optional — tối đa 10 điểm)*

> Bỏ trống nếu không làm. Xem `docs/bonus/README.md`. Đừng làm hết — **một** finding sâu
> ăn điểm hơn năm bảng nông.

**Đã làm:** 

**Numbers:**

```
before:  
after:   
speedup: 
```

**Điều này nói lên gì mà deck chưa nói:**

(để trống nếu bạn không làm phần này)

---

## 7. Điều làm bạn ngạc nhiên nhất  *(optional)*

Điều ngạc nhiên nhất là việc giảm một nửa số thread (-t 12 xuống -t 6) lại giúp tăng tốc tới 1.31x trên Apple Silicon, minh họa rõ nét hiệu ứng straggler trong barrier synchronization của kiến trúc heterogeneous core.

---

## 8. Self-check trước khi push

- [x] `hardware.json` committed
- [x] `models/active.json` committed
- [x] `benchmarks/01-quickstart-results.md` committed (`make bench`)
- [x] `benchmarks/01-tuning-tg128.md` committed (`make tune`)
- [x] `benchmarks/02-server-results.md` committed (`make load-report`)
- [x] `benchmarks/02-server-batching-u50.md` hoặc `-metrics-u50.csv` committed (`make metrics`)
- [x] `benchmarks/locust-10_stats.csv` + `locust-50_stats.csv` committed (`make load-10` / `load-50`)
- [x] `benchmarks/03-integration-results.md` committed (`make pipeline`)
- [x] Mọi section **"required — replace this line"** trong các file `benchmarks/*.md`
      đã được thay bằng nhận xét của bạn
- [x] 5 screenshots trong `submission/screenshots/`
- [ ] `make verify` → **exit 0**
- [x] Repo tên đúng mẫu `K4-L3-DAY20-HoVaTen-MSSV-ModelServing` (xem `docs/SUBMISSION.md`)
- [x] Repo GitHub ở chế độ **public**
- [ ] Đã push và paste public URL vào VinUni LMS **trước 23:59 (UTC+7) ngày làm lab**
- [x] **Không** commit `models/*.gguf`, `runtime/` hay `.env` (đã có trong `.gitignore`)

**Quan trọng:** repo phải **public** đến khi điểm được công bố. Private → grader không
xem được → 0 điểm.

---

## 9. Khai báo sử dụng AI  *(xem `docs/RULES.md` §3)*

Sử dụng Antigravity Coding Assistant để hỗ trợ đọc tài liệu lab, chạy các lệnh tự động, trích xuất số liệu benchmark và giải thích cơ chế kỹ thuật.
