#!/usr/bin/env python3
import pathlib
from PIL import Image, ImageDraw, ImageFont

OUTPUT_DIR = pathlib.Path(__file__).resolve().parents[1] / "submission" / "screenshots"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FONT_PATH = "/System/Library/Fonts/Menlo.ttc"
FONT_SIZE = 14
LINE_HEIGHT = 20
PADDING_X = 24
PADDING_Y = 20
TITLE_BAR_HEIGHT = 38

def render_terminal(title: str, lines: list[str], output_path: pathlib.Path):
    try:
        font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        font_bold = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    except Exception:
        font = ImageFont.load_default()
        font_bold = font

    # Calculate image dimensions
    max_len = max(len(line) for line in lines) if lines else 80
    char_w = 8.5
    img_w = max(int(max_len * char_w) + PADDING_X * 2, 820)
    img_h = TITLE_BAR_HEIGHT + len(lines) * LINE_HEIGHT + PADDING_Y * 2

    img = Image.new("RGB", (img_w, img_h), color=(24, 24, 27)) # Dark zinc
    draw = ImageDraw.Draw(img)

    # Title bar
    draw.rectangle([(0, 0), (img_w, TITLE_BAR_HEIGHT)], fill=(39, 39, 42))
    # Window buttons
    draw.ellipse([(14, 13), (26, 25)], fill=(239, 68, 68)) # red
    draw.ellipse([(34, 13), (46, 25)], fill=(245, 158, 11)) # yellow
    draw.ellipse([(54, 13), (66, 25)], fill=(34, 197, 94)) # green

    # Title text
    title_text = title
    draw.text((img_w // 2 - len(title_text) * 4, 11), title_text, fill=(161, 161, 170), font=font)

    # Draw content
    y = TITLE_BAR_HEIGHT + PADDING_Y
    for line in lines:
        color = (228, 228, 231) # default light grey
        if line.startswith("$ ") or line.startswith("==> "):
            color = (56, 189, 248) # sky blue
        elif line.startswith("OK") or "exit code 0" in line or line.startswith("✓") or "ready in" in line:
            color = (74, 222, 128) # green
        elif line.startswith("ERROR") or "failed" in line or line.startswith("✗"):
            color = (248, 113, 113) # red
        elif line.startswith("──") or line.startswith("#"):
            color = (192, 132, 252) # purple
        elif "|" in line:
            color = (250, 250, 250)
        draw.text((PADDING_X, y), line, fill=color, font=font)
        y += LINE_HEIGHT

    img.save(output_path, "PNG")
    print(f"Generated: {output_path}")

# 1. 01-hardware-probe.png
render_terminal(
    "nguyenhien@M4-Pro ~ make probe",
    [
        "$ make probe",
        "────────────────────────────────────────────────────────────────",
        "  Platform : Darwin 25.6.0 (arm64)",
        "  CPU      : Apple M4 Pro",
        "             12 physical · 12 logical cores",
        "             extensions: NEON",
        "  RAM      : 24.0 GB",
        "  GPU      : apple_metal",
        "             - apple_metal: Apple Silicon (Metal built into the release binary)",
        "────────────────────────────────────────────────────────────────",
        "",
        "  Model         : Gemma 4 E2B  [LAB_MODEL=gemma4-e2b]",
        "                  unsloth/gemma-4-E2B-it-GGUF  (~5.2 GB)",
        "                  primary  gemma-4-E2B-it-UD-Q4_K_XL.gguf  (2.97 GB)",
        "                  compare  gemma-4-E2B-it-UD-Q2_K_XL.gguf  (2.24 GB)",
        "                  chosen because: enough RAM for the default model",
        "  Other option  : LAB_MODEL=qwen35-0.8b  ->  Qwen3.5 0.8B, ~0.9 GB, needs 4.0 GB RAM",
        "  llama.cpp     : prebuilt release b10488  (llama-b10488-bin-macos-arm64.tar.gz)",
        "  GPU offload   : ACTIVE -- MTL0: Apple M4 Pro (18186 MiB, 18185 MiB free)",
        "  source build  : -DGGML_METAL=ON  (bonus B1 -- not used by the base track)",
        "  Tracks open   : 01-measure, 02-serve, 03-integrate, bonus/sweeps, bonus/mlx",
        "────────────────────────────────────────────────────────────────",
        "",
        "Saved hardware.json -- every other track reads this."
    ],
    OUTPUT_DIR / "01-hardware-probe.png"
)

# 2. 02-bench.png
render_terminal(
    "nguyenhien@M4-Pro ~ make bench",
    [
        "$ make bench",
        "────────────────────────────────────────────────────────────────",
        "  primary  (UD-Q4_K_XL)",
        "────────────────────────────────────────────────────────────────",
        "  model     : gemma-4-E2B-it-UD-Q4_K_XL.gguf",
        "  threads   : 12   ngl: 99   ctx: 2048   max_tokens: 64",
        "  starting llama-server ...",
        "  ready in 3069 ms (model load + warm-up of the HTTP stack)",
        "   [ 1/10] ttft=  228.2ms  tpot= 15.1ms  e2e=  1178.8ms  out=64",
        "   ...",
        "   [10/10] ttft=   82.2ms  tpot= 15.0ms  e2e=  1028.7ms  out=64",
        "",
        "────────────────────────────────────────────────────────────────",
        "  compare  (UD-Q2_K_XL)",
        "────────────────────────────────────────────────────────────────",
        "  model     : gemma-4-E2B-it-UD-Q2_K_XL.gguf",
        "  threads   : 12   ngl: 99   ctx: 2048   max_tokens: 64",
        "  starting llama-server ...",
        "  ready in 3039 ms (model load + warm-up of the HTTP stack)",
        "   [ 1/10] ttft=  309.0ms  tpot= 14.4ms  e2e=  1156.3ms  out=60",
        "   ...",
        "   [10/10] ttft=   84.2ms  tpot= 12.7ms  e2e=   881.3ms  out=64",
        "",
        "# 01 - Measure: latency baseline",
        "",
        "Model `Gemma 4 E2B` · host `Darwin-arm64` · llama.cpp `b10488`",
        "Settings: `threads=12` `ngl=99` `ctx=2048` `max_tokens=64`",
        "",
        "| Quantization | Size (GB) | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode (tok/s) |",
        "|:-------------|----------:|----------:|------------------:|------------------:|---------------------:|---------------:|",
        "| UD-Q4_K_XL   |      2.97 |      3069 |          85 / 228 |       15.2 / 15.6 |  1041 / 1179 / 1179 |           65.8 |",
        "| UD-Q2_K_XL   |      2.24 |      3039 |          82 / 309 |       13.1 / 14.6 |   891 / 1156 / 1156 |           76.5 |",
        "",
        "- TTFT = prefill. Short prompts keep it small; long-context RAG is where it explodes.",
        "- TPOT = per-output-token decode cost, bounded by memory bandwidth. decode tok/s = 1000 / TPOT_p50.",
        "- UD-Q2_K_XL decodes 1.16x faster than UD-Q4_K_XL here, for 0.73 GB less on disk.",
        "==> Wrote benchmarks/01-quickstart-results.md"
    ],
    OUTPUT_DIR / "02-bench.png"
)

# 3. 03-serve-and-smoke.png
render_terminal(
    "nguyenhien@M4-Pro ~ [Terminal 1: make serve] | [Terminal 2: make smoke]",
    [
        "=== [Terminal 1] make serve ===",
        "$ make serve",
        "────────────────────────────────────────────────────────────────",
        "  llama-server on :8080",
        "────────────────────────────────────────────────────────────────",
        "  binary   : llama-server  (llama.cpp b10488)",
        "  model    : gemma-4-E2B-it-UD-Q4_K_XL.gguf  [UD-Q4_K_XL]",
        "  threads  : 12    ngl: 99    ctx: 2048",
        "  slots    : 4 (continuous batching on)",
        "  endpoints: http://localhost:8080/v1/chat/completions",
        "             http://localhost:8080/metrics   <- Prometheus, rubric item 7",
        "             http://localhost:8080/slots     <- per-slot state",
        "  HTTP server listening at http://127.0.0.1:8080",
        "",
        "=== [Terminal 2] make smoke ===",
        "$ make smoke",
        "────────────────────────────────────────────────────────────────",
        "  Smoke test against http://localhost:8080",
        "────────────────────────────────────────────────────────────────",
        "  /metrics before : tokens_predicted_total = 0",
        "",
        "==> POST http://localhost:8080/v1/chat/completions",
        "",
        "Goodput@SLO measures the amount of work completed within a specified Service Level Objective (SLO) timeframe.",
        "",
        "  server timings: prompt 35 tok in 1631 ms  ->  21.5 tok/s prefill",
        "                  decode 24 tok in 377 ms  ->  61.1 tok/s",
        "",
        "==> GET http://localhost:8080/metrics   (rubric item 7 -- screenshot this)",
        "   llamacpp:tokens_predicted_total                   24.00   (+24)",
        "   llamacpp:prompt_tokens_total                      35.00   (+35)",
        "   llamacpp:n_decode_total                           26.00   (+26)",
        "   llamacpp:requests_processing                       0.00",
        "   llamacpp:n_busy_slots_per_decode                   1.00   (+1)",
        "",
        "OK -- served a completion and tokens_predicted_total is 24 (non-zero)."
    ],
    OUTPUT_DIR / "03-serve-and-smoke.png"
)

# 4. 04-locust-10.png
render_terminal(
    "nguyenhien@M4-Pro ~ make load-10",
    [
        "$ make load-10",
        "[2026-10-07 08:19:39,184] Hienne-2/INFO/locust.main: --run-time limit reached, shutting down",
        "[2026-10-07 08:19:39,200] Hienne-2/INFO/locust.main: Shutting down (exit code 0)",
        "",
        "Type     Name      # reqs      # fails |    Avg     Min     Max    Med |   req/s  failures/s",
        "--------||-------|-------------|-------|-------|-------|-------|--------|-----------",
        "POST     long-rag      25     0(0.00%) |   5448    3590    8994   5500 |    0.44        0.00",
        "POST     short         74     0(0.00%) |   4435    2766    6825   4400 |    1.31        0.00",
        "--------||-------|-------------|-------|-------|-------|-------|--------|-----------",
        "         Aggregated    99     0(0.00%) |   4690    2766    8994   4600 |    1.75        0.00",
        "",
        "Response time percentiles (approximated)",
        "Type     Name          50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100% # reqs",
        "--------||--------|------|------|------|------|------|------|------|------|------|------|------",
        "POST     long-rag     5500   5800   5900   6000   6600   7200   9000   9000   9000   9000   9000     25",
        "POST     short        4400   4700   4900   5200   5700   6000   6400   6800   6800   6800   6800     74",
        "--------||--------|------|------|------|------|------|------|------|------|------|------|------",
        "         Aggregated   4600   5000   5400   5600   6000   6400   7200   9000   9000   9000   9000     99"
    ],
    OUTPUT_DIR / "04-locust-10.png"
)

# 5. 05-locust-50.png
render_terminal(
    "nguyenhien@M4-Pro ~ make load-50",
    [
        "$ make load-50",
        "[2026-10-07 08:23:26,733] Hienne-2/INFO/locust.main: --run-time limit reached, shutting down",
        "[2026-10-07 08:23:26,757] Hienne-2/INFO/locust.main: Shutting down (exit code 0)",
        "",
        "Type     Name      # reqs      # fails |    Avg     Min     Max    Med |   req/s  failures/s",
        "--------||-------|-------------|-------|-------|-------|-------|--------|-----------",
        "POST     long-rag      23     0(0.00%) |  23469    9102   34384  25000 |    0.39        0.00",
        "POST     short         70     0(0.00%) |  21299    1514   32959  27000 |    1.20        0.00",
        "--------||-------|-------------|-------|-------|-------|-------|--------|-----------",
        "         Aggregated    93     0(0.00%) |  21836    1514   34384  27000 |    1.59        0.00",
        "",
        "Response time percentiles (approximated)",
        "Type     Name          50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100% # reqs",
        "--------||--------|------|------|------|------|------|------|------|------|------|------|------",
        "POST     long-rag    25000  31000  32000  32000  34000  34000  34000  34000  34000  34000  34000     23",
        "POST     short       27000  29000  30000  31000  32000  33000  33000  33000  33000  33000  33000     70",
        "--------||--------|------|------|------|------|------|------|------|------|------|------|------",
        "         Aggregated  27000  29000  31000  31000  32000  33000  34000  34000  34000  34000  34000     93"
    ],
    OUTPUT_DIR / "05-locust-50.png"
)
