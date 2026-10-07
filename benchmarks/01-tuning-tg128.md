# 01 - Tune: thread-count sweep

Model `gemma-4-E2B-it-UD-Q4_K_XL.gguf` · host `Darwin-arm64` · llama.cpp `b10488`
CPU: **12 physical · 12 logical** cores · `ngl=99` · metric `tg128`

| threads (-t) | tg128 (tok/s) | vs best |
|:--|--:|--:|
| 1 | 82.4 | 96% |
| 6 | 86.2 | 100% |
| 12 | 65.6 | 76% |
| 24 | 65.0 | 75% |

**Best**: `-t 6` at 86.2 tok/s
**Slowest tested**: `-t 24` at 65.0 tok/s (1.33x spread)
**Against the physical-core default** (`-t 12`, 65.6 tok/s): 1.31x

Use this in your run:

```bash
LAB_N_THREADS=6 make bench
```

## Your explanation

- **Vị trí điểm Knee:** Đỉnh hiệu năng (peak) đạt tại **`-t 6`** với **86.2 tok/s**, sau đó hiệu năng tụt dốc rõ rệt khi tăng lên `-t 12` (chỉ còn 65.6 tok/s, tương đương 76% mức đỉnh) và `-t 24` (65.0 tok/s).
- **Cơ chế kỹ thuật giải thích kết quả:**
  1. **Kiến trúc Heterogeneous Cores (P-cores vs E-cores):** Con chip Apple M4 Pro có 12 cores nhưng không đồng nhất, gồm cụm Performance cores (P-cores) xung nhịp cao và Efficiency cores (E-cores) tiết kiệm điện. Khi chạy với `-t 6`, toàn bộ các worker threads được lập lịch hoàn toàn trên cụm P-cores mạnh nhất.
  2. **Hiệu ứng Straggler trong Fork-Join Synchronization:** Khi nâng thread count lên `-t 12` (bằng tổng số physical core) hoặc `-t 24` (oversubscription), các tác vụ song song của GGML buộc phải phân bổ lên cả các E-cores. Vì các phép toán ma trận trong llama.cpp yêu cầu đồng bộ hóa barrier (barrier synchronization) giữa các luồng, tốc độ hoàn thành của mỗi bước tính toán bị giới hạn bởi luồng chạy chậm nhất (chạy trên E-core).
  3. **Tranh chấp tài nguyên & Đồng bộ GPU Metal (`ngl=99`):** Khi các layer được offload lên Metal GPU, vai trò của CPU là dispatch và điều phối. Quá nhiều threads (12 hoặc 24) gây ra context-switching overhead, tranh chấp cache L2/L3 giữa các cluster CPU và nghẽn memory bus, làm giảm throughput tổng thể thay vì tăng tốc.
- **Kết luận:** Cấu hình tối ưu nhất cho Apple M4 Pro trên bài toán này là **`-t 6`**, mang lại tốc độ vượt trội **1.31x** so với cấu hình mặc định 12 cores. Cấu hình này sẽ được áp dụng làm finding cốt lõi cho mục §5 trong REFLECTION.md.
