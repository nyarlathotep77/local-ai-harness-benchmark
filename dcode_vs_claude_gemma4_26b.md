# Benchmarking Local Coding Assistants: dcode vs. Claude Code

When developing software locally using agentic AI harnesses, performance and tool execution reliability are critical factors. In this post, the performance and correctness of two prominent terminal-based AI coding agents running on the same local hardware are compared: **dcode** (built on LangChain's open-source [deepagents](https://github.com/langchain-ai/deepagents) framework) and **Claude Code** (Anthropic's official [Claude CLI](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview)).

Both harnesses are configured to use the same local model, **gemma4:26b**, running via the same local Ollama instance on the same port. This ensures a fair and comparable environment where the model intelligence and raw generation speed are kept constant, allowing the evaluation of the efficiency and tool execution strategies of the harnesses themselves.

---

## Hardware and Software Configuration

To provide a consistent baseline, all benchmarks were executed on the following workstation setup:

### Hardware Specs:
- **Operating System**: Ubuntu 24.04.1 LTS (Linux Kernel 7.0.0-28-generic)
- **CPU**: AMD Ryzen 7 8845HS w/ Radeon 780M Graphics (8 Cores, 16 Threads)
- **RAM**: 64 GB DDR5 System Memory
- **GPU**: NVIDIA GeForce RTX 5060 Ti (16 GB GDDR6 VRAM)
- **CUDA/Driver Version**: CUDA 13.0 / NVIDIA Driver 580.159.03

### Software Versions and Token-Window Limits:
- **Ollama**: `0.32.3`
- **dcode**: `0.1.44` (running deepagents SDK `0.6.12`)
  - **Context Window (Input)**: `65,536` tokens (configured via `num_ctx` in client parameters)
  - **Max Output Tokens**: `4,096` tokens (configured via `num_predict`)
- **Claude Code**: `2.1.220` (Claude CLI)
  - **Context Window (Input)**: `128,000` tokens (CLI standard default context limit)
  - **Max Output Tokens**: `8,192` tokens (capped via internal CLI configuration)
- **Local Model**: `gemma4:26b` running via Ollama

---

## Benchmark Methodology

To ensure clean, independent, and reproducible results:
1. **Isolated Workspaces**: Each test case was run inside a fresh temporary directory (`/tmp/benchmark_<harness>_<test_id>`) to avoid file contamination.
2. **Sequential Execution**: Tests were executed one at a time to prevent CPU/GPU resource contention. The harnesses were not run in parallel.
3. **Identical Model**: Both agents were configured to use `gemma4:26b` running locally on Ollama.
4. **Comparable Instructions**:
   - `dcode` was run in non-interactive mode using: `dcode -n "<prompt>" -S all`
   - `claude` was run in print mode with all permissions pre-approved using: `claude -p "<prompt>" --dangerously-skip-permissions`
5. **Diverse Coding Tasks**: Ten tests were defined representing typical everyday coding operations, including standard Python utilities, bash scripting, and 3 simple Android Jetpack Compose mobile applications.

---

## Performance and Correctness Results

The results below are sorted by difficulty from the simplest script execution to the multi-file Android application configurations:

| Test ID | dcode Duration (s) | Claude Duration (s) | Speedup (dcode vs Claude) | dcode LOC | Claude LOC | dcode Status | Claude Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `fizzbuzz` | 49.76s | 70.83s | **1.42x** | 9 | 9 | ✅ Pass | ✅ Pass |
| `fibonacci` | 50.49s | 94.12s | **1.86x** | 15 | 14 | ✅ Pass | ✅ Pass |
| `reverse_words` | 52.10s | 77.41s | **1.49x** | 12 | 13 | ✅ Pass | ✅ Pass |
| `prime_generator` | 55.05s | 83.16s | **1.51x** | 26 | 22 | ✅ Pass | ✅ Pass |
| `weather_client` | 54.29s | 86.66s | **1.60x** | 18 | 15 | ✅ Pass | ✅ Pass |
| `search_replace` | 67.03s | 77.04s | **1.15x** | 41 | 0 | ✅ Pass | ❌ Fail (No File) |
| `dir_tree_bash` | 206.86s | 75.28s | **0.36x** | 171 | 0 | ✅ Pass | ❌ Fail (No File) |
| `android_counter` | 68.25s | 97.25s | **1.42x** | 48 | 52 | ✅ Pass | ✅ Pass |
| `android_intent` | 107.56s | 114.14s | **1.06x** | 42 | 42 | ✅ Pass | ✅ Pass |
| `android_login` | 91.55s | 107.76s | **1.18x** | 81 | 74 | ✅ Pass | ✅ Pass |
| **Total Time** | **802.94s (13.38m)** | **883.65s (14.73m)** | **1.10x overall** | **463** | **241** | **100% Success** | **80% Success** |

---

## Detailed Analysis

### Why is dcode Consistently Faster and More Reliable?

The benchmark execution showed that `dcode` completed the entire suite in **802.94 seconds** compared to Claude Code's **883.65 seconds**, representing a **1.10x overall speedup** (about 1.3 minutes faster), and achieved a **100% success rate** compared to Claude's **80% success rate**.

#### 1. File Writing and Tool Execution Consistency
In two tests (`dir_tree_bash` and `search_replace`), Claude Code failed to create any files on disk (0 lines of code generated). Instead of calling its file-writing tools, Claude Code simply printed the code block output in its text response. 
Under print mode (`-p`) on a local open-weights model (`gemma4:26b`), the model occasionally fails to match Claude's strict tool schemas, leading to a breakdown in agentic tool-calling. In contrast, `dcode`'s streamlined ReAct executor enforced tool calling successfully for all 10 tasks, ensuring that every script was correctly written to the workspace.

#### 2. Lower Startup and Bootstrap Overhead
Claude Code performs extensive workspace scanning, git history verification, npm dependency checking, plugin synchronization, and configuration mapping at startup. While very useful in active interactive developer environments, it introduces a fixed latency penalty for short headless runs. `dcode` initiates its agentic server loop immediately, making it faster to dispatch its first model prompts.

#### 3. Prompt Layout and Local Weight Alignment
Claude Code's internal prompts and system instructions are heavily tailored for Anthropic's cloud-hosted Claude 3.5 Sonnet. When redirected to local open-weights models like Gemma, the model occasionally struggles to digest Sonnet-optimized schemas, resulting in longer thinking pauses or extra validation rounds. `dcode`'s default system prompts are lightweight and align exceptionally well with local models, avoiding turn overhead.

---

## Conclusion

Both `dcode` and `claude` are highly capable local coding tools, successfully generating correct solutions for simple Android app configurations.

- **dcode (Deep Agents Code)** is the clear winner for **raw performance, speed, and tool execution reliability** under a local Ollama setup. It achieved **100% correctness** across all python, bash, and Android tasks, making it highly suitable for developer pipelines, headless scripts, and CI runners.
- **Claude Code** remains a feature-rich client with deep integration (e.g. git worktree automation, enterprise telemetry, and sequential thinking MCPs), but struggles with tool-calling consistency and higher overhead when running on local open-weights models due to its prompt structures being tailored for Anthropic's proprietary APIs.

*All raw data from this benchmark can be found in `benchmark_results.csv`.*

---

> [!NOTE]
> **Disclaimer**: This benchmark is conducted purely for sharing data and findings with the developer community. It does not promote or endorse any particular harness or tool.

