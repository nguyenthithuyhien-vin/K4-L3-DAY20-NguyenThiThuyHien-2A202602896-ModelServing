# 02 - Continuous batching under load (u50)

Host `Darwin-arm64` · `--parallel 4` · 27 samples over
60s at 2.0s intervals · raw CSV: `02-server-metrics-u50.csv`

| Gauge | Peak observed |
|:--|--:|
| `n_busy_slots_per_decode` (avg/decode) | 3.93 of 4 slots (98%) |
| `requests_processing` | 4 |
| `requests_deferred` | 46 |
| `kv_cache_usage_ratio` | n/a — not exported by llama.cpp `b10488` |
| `tokens_predicted_total` (final) | 11154 |

Highest sampled value was **3.93 of 4** slots. Note this gauge is llama.cpp's *average* busy slots per decode step, so the number below is the highest average we sampled, not an instantaneous maximum batch width. A peak near 1 means
requests were served one at a time -- either the load was too light to overlap, or
they arrived too far apart. A peak approaching `--parallel` means the scheduler was
genuinely packing concurrent requests into shared decode steps.
`requests_deferred` went above zero: more requests arrived than there were slots, so some waited. That wait is the queue time in your P95.

## Your observation

- **Peak Batch Width quan sát được:** Chỉ số `n_busy_slots_per_decode` đạt đỉnh tại **3.93 / 4 slots** (~98.25% dung lượng slot khả dụng). Đồng thời, `requests_processing` duy trì ở mức tối đa là 4 slot. Điều này là bằng chứng thực nghiệm rõ ràng cho thấy cơ chế **Continuous Batching (iteration-level scheduling)** của `llama-server` đang hoạt động hiệu quả, liên tục gộp các request đến vào chung các bước tính toán decode thay vì xử lý tuần tự (sequential) từng request.
- **So sánh với Effective Concurrency (34.7) trong `02-server-results.md`:**
  - Hai con số này khác nhau về mặt bản chất đo lường:
    - **`n_busy_slots_per_decode` (3.93 / 4):** Phản ánh **Compute / Slot Utilisation**, tức số lượng request thực tế đang nằm trong GPU/CPU compute pipeline tại mỗi bước sinh token. Do server khởi chạy với `--parallel 4`, con số này bị chặn trên bởi 4 slots.
    - **`Effective Concurrency` ($L = \lambda \times W = 34.7$):** Phản ánh **System Occupancy** theo Định luật Little, đo tổng số request đang tồn tại trong toàn bộ hệ thống (in-flight), bao gồm 4 request đang được tính toán và ~46 request đang nằm chờ trong hàng đợi (`requests_deferred = 46`).
- **Đánh giá độ tin cậy:** Cả hai con số đều hoàn toàn chính xác và nhất quán: Metric đo từ server khẳng định scheduler đã bão hòa tài nguyên xử lý (3.93/4 slots), còn Little's Law khẳng định hệ thống đang quá tải nghiêm trọng về mặt lưu lượng khiến phần lớn thời gian trễ của client bị chi phối bởi **Queue Time** trong hàng đợi.
