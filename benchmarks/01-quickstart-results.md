# 01 - Measure: latency baseline

Model `Gemma 4 E2B` · host `Darwin-arm64` · llama.cpp `b10488`
Settings: `threads=12` `ngl=99` `ctx=2048`
`max_tokens=64` · warm-up discarded
Completed requests: `UD-Q4_K_XL` 10/10 · `UD-Q2_K_XL` 10/10

| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |
|:--|--:|--:|--:|--:|--:|--:|
| UD-Q4_K_XL | 2.97 | 3069 | 85 / 228 | 15.2 / 15.6 | 1041 / 1179 / 1179 | 65.8 |
| UD-Q2_K_XL | 2.24 | 3039 | 82 / 309 | 13.1 / 14.6 | 891 / 1156 / 1156 | 76.5 |

- **TTFT** = prefill. Short prompts keep it small; long-context RAG is where it explodes.
- **TPOT** = per-output-token decode cost, bounded by memory bandwidth. `decode tok/s = 1000 / TPOT_p50`.
- `UD-Q2_K_XL` decodes **1.16x faster** than `UD-Q4_K_XL` here, for 0.73 GB less on disk.

## Your observation

- **Dung lượng & Băng thông:** Bản `UD-Q2_K_XL` (2.24 GB) nhỏ hơn bản `UD-Q4_K_XL` (2.97 GB) khoảng 0.73 GB (~24.6% footprint). Trong pha decode (sinh token tuần tự), LLM bị nghẽn chủ yếu bởi **memory bandwidth** thay vì FLOPs, vì mỗi step sinh 1 token đều phải stream toàn bộ trọng số mô hình từ Unified Memory vào bộ xử lý. Nhờ dung lượng weights nạp qua bus giảm ~25%, tốc độ decode tăng trực tiếp từ 65.8 tok/s lên 76.5 tok/s (cải thiện ~1.16x, TPOT P50 giảm từ 15.2 ms xuống 13.1 ms).
- **Độ trễ TTFT (Prefill):** TTFT P50 giữa hai bản gần như tương đương nhau (85 ms vs 82 ms) trên các prompt ngắn do pha prefill bị chi phối bởi compute (FLOPs). Tuy nhiên, TTFT P95 của bản 2-bit tăng lên 309 ms (so với 228 ms ở 4-bit), phản ánh overhead khi dequantize các block 2-bit không đồng đều trong các burst tính toán.
- **Đánh giá mức độ đáng dùng:** Mặc dù 2-bit mang lại mức tăng tốc 1.16x, chất lượng trả lời và khả năng suy luận logic/bám ngữ cảnh của bản 2-bit bị suy giảm rõ rệt so với 4-bit (dễ mất tính mạch lạc ở các câu hỏi suy luận sâu hoặc trích xuất thông tin). Với phần cứng Apple M4 Pro sở hữu tới 24 GB Unified Memory, việc tiết kiệm 0.73 GB RAM là hoàn toàn không cần thiết. Vì vậy, bản **`UD-Q4_K_XL` là lựa chọn tối ưu vượt trội**, đảm bảo chất lượng mô hình cao nhất trong khi vẫn duy trì tốc độ decode cực kỳ ấn tượng (>65 tok/s).
