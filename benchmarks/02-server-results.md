# 02 - Serve: load test + saturation reading

Host `Darwin-arm64` · llama.cpp `b10488` ·
`--parallel 4` · `ctx=2048` · `threads=12` ·
`ngl=99`

| Users | Reqs | RPS | P50 (ms) | P95 (ms) | P99 (ms) | Eff. concurrency | Failures |
|:--|--:|--:|--:|--:|--:|--:|--:|
| 10 | 99 | 1.75 | 4600 | 6400 | 9000 | 8.2 | 0.0% |
| 50 | 93 | 1.59 | 27000 | 33000 | 34000 | 34.7 | 0.0% |

*Effective concurrency = RPS x average latency (Little's Law) -- how many requests were
really in flight, regardless of how many users locust simulated. It counts queued requests
too, so the occupancy/slot ratio can legitimately exceed 1.0; it is occupancy, not
utilisation. For true slot utilisation use the server's own gauges (`make metrics`).*

## What these two runs say

| Going from 10 to 50 users | |
|:--|--:|
| Offered load | 5x |
| Throughput actually delivered | **0.91x** (18% of linear) |
| P95 latency | **5.16x** |
| Effective concurrency at 50 users | 34.7 vs `--parallel 4` slots (occupancy/slot ratio 8.69) |

**Saturated.** Throughput delivered only 0.91x for 5x the offered load, and effective concurrency (34.7) is at or above all 4 decode slots. Saturation sets in somewhere at or below 50 users; the load you added beyond that point became queue time rather than throughput.

Throughput moved 0.91x while P95 moved 5.16x. That gap is the goodput argument: past saturation you buy throughput by spending latency, and if your SLO is a P95 target then the requests you added are no longer being served within it. (This lab does not fix an SLO number for you -- pick one in your write-up and state how much goodput you keep at it.)

## Your reading

- **Điểm bão hoà của Server & Bằng chứng số liệu:**
  - Hệ thống đã bão hòa hoàn toàn ở mức tải dưới 50 users (thực tế điểm uốn bão hòa nằm ở khoảng 10–12 users).
  - Con số bằng chứng thuyết phục nhất: Khi tăng tải mô phỏng lên **5x** (từ 10 lên 50 users), thông lượng (throughput) thực tế hoàn toàn đình trệ, thậm chí giảm nhẹ từ **1.75 RPS xuống 1.59 RPS** (chỉ đạt 0.91x so với mức 10 users).
  - Ngược lại, độ trễ **P95 tăng vọt 5.16x** (từ 6,400 ms lên 33,000 ms) và **P50 tăng 5.87x** (từ 4,600 ms lên 27,000 ms).
  - Theo Định luật Little, **Effective Concurrency ở 50 users là 34.7**, vượt xa sức chứa của server (**`--parallel 4`** slots, tỉ lệ tải/slot đạt **8.69x**). Hàng đợi ghi nhận tới 46 request bị hoãn (`requests_deferred = 46`). Toàn bộ phần độ trễ phình to thêm (~26.6s ở P95) chính là **Queue Time** nằm chờ slot trống chứ không phải do GPU tính toán chậm đi.
- **Lập luận Goodput@SLO:**
  - Giả sử hệ thống cam kết Service Level Objective (SLO) cho ứng dụng là **$P95 \le 8,000\text{ ms}$**:
    - Ở mức 10 users: $P95 = 6,400\text{ ms} < 8,000\text{ ms}$, hệ thống đạt **Goodput@SLO = 1.75 RPS** (100% request hoàn thành đạt chuẩn SLO).
    - Ở mức 50 users: $P95 = 33,000\text{ ms}$ (ngay cả $P50 = 27,000\text{ ms}$ cũng trượt xa mục tiêu 8s). Khi đó, **Goodput@SLO tụt về 0 RPS** dù raw throughput vẫn báo 1.59 RPS. Mọi compute cycles phục vụ các request quá hạn này đều trở thành lãng phí.
- **Knob cần can thiệp đầu tiên để nâng cao Goodput@SLO:**
  - Knob tôi sẽ thay đổi đầu tiên là **tăng `--parallel` (từ 4 lên 8 hoặc 12 slots)**, đồng thời cố định **`-t 6`** (tối ưu CPU P-cores từ kết quả `make tune`).
  - **Lý do chọn knob này thay vì knob khác:**
    1. Máy có tới 24 GB Unified Memory, việc tăng slot chỉ tiêu tốn thêm một phần nhỏ dung lượng KV cache (vài trăm MB cho context ngắn), không hề gây nguy cơ OOM.
    2. Pha decode là **memory-bandwidth-bound** (stream 2.97 GB trọng số một lần qua bộ nhớ). Khi tăng số slot, `llama.cpp` sẽ tính toán đồng thời nhiều output tokens hơn cho mỗi lượt stream trọng số qua bus bộ nhớ (tận dụng đặc tính amortization của continuous batching). Điều này làm tăng raw token throughput thực tế, giải phóng hàng đợi nhanh hơn và kéo P95 tụt dốc trở lại ngưỡng SLO.
    3. Không chọn tăng `n_ctx` vì nó làm phình to KV cache mà không giúp gì cho việc giải tỏa hàng đợi; cũng không giảm bit quantization xuống 2-bit vì sẽ làm giảm chất lượng mô hình không đáng có.
