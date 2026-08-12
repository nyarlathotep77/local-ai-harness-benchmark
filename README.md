# Local AI Coding Assist Benchmarks

An index of performance and correctness benchmarks comparing local AI coding assistants (such as `dcode` and `claude` CLI) running on local open-weights models via Ollama.

## 📊 Benchmark Reports

1. **[gemma4:26b Local Coding Benchmark](dcode_vs_claude_gemma4_26b.md)**
   * **Date**: July 31, 2026
   * **Model**: `gemma4:26b` via Ollama
   * **Harnesses**: [dcode](https://github.com/langchain-ai/deepagents) (v0.1.44, based on the open-source `deepagents` framework) vs. [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview) CLI (v2.1.220)
   * **Summary**: A comparison of 10 sequential tasks (including Python, Bash and Android Jetpack Compose setups). `dcode` achieved a 100% success rate with an overall 1.10x speedup, while Claude Code had an 80% success rate due to tool-calling limitations under local weights.

2. **[dcode Local Model Comparison: gemma4:26b vs. muse-glimmer:30b](dcode_gemma4_vs_muse_glimmer_30b.md)**
   * **Date**: August 12, 2026
   * **Models**: `gemma4:26b` vs. `muse-glimmer:30b` via Ollama
   * **Harness**: `dcode` (editable fork of deepagents-code CLI)
   * **Summary**: An evaluation comparing the newly released agentic-optimized `muse-glimmer:30b` model against the general-purpose `gemma4:26b`. Muse Glimmer achieved a 100% functional success rate (9/10 passing verification due to a strict keyword check), proving highly correct and reliable in multi-file Android Compose and script setups, but suffered a 3.5x wall-clock slowdown due to CPU offloading on a 16 GB GPU.

---

## 💻 Hardware Environment Reference

All benchmarks are executed on the following workstation:
- **Operating System**: Ubuntu 24.04.1 LTS (Linux Kernel 7.0.0-28-generic)
- **CPU**: AMD Ryzen 7 8845HS w/ Radeon 780M Graphics (8 Cores, 16 Threads)
- **RAM**: 64 GB DDR5 System Memory
- **GPU**: NVIDIA GeForce RTX 5060 Ti (16 GB GDDR6 VRAM)
- **CUDA/Driver**: CUDA 13.0 / NVIDIA Driver 580.159.03

---

## 🔮 Upcoming Benchmarks

The next scheduled benchmark will evaluate:
* **Model**: `qwen3.6:27b` (via Ollama)
* **Goal**: Measure how a code-specialized model affects tool-calling consistency and execution speed.

If there are specific local open-weights models or configurations you would like to see compared, please open an issue or share your suggestions!

---

> [!NOTE]
> **Disclaimer**: This benchmark is conducted purely for sharing data and findings with the developer community. It does not promote or endorse any particular harness or tool.


