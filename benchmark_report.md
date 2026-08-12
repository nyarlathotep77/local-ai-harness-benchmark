# Local AI Coding Assistant Benchmarks: Performance Comparison

This report compares different local AI coding assistant setups running on local hardware.

## 💻 Workstation Reference
- **OS**: Ubuntu 24.04.1 LTS
- **CPU**: AMD Ryzen 7 8845HS (8 Cores, 16 Threads)
- **RAM**: 64 GB DDR5
- **GPU**: NVIDIA GeForce RTX 5060 Ti (16 GB VRAM)

## 📊 Evaluated Configurations

| Harness | Model | Tasks Completed | Success Rate |
| :--- | :--- | :---: | :---: |
| `claude` | `gemma4:26b` | 8/10 | **80.0%** |
| `dcode` | `gemma4:26b` | 10/10 | **100.0%** |
| `dcode` | `muse-glimmer:30b` | 9/10 | **90.0%** |

---

## ⏱️ Detailed Task Times (seconds)

| Test ID | `claude` + `gemma4:26b` | `dcode` + `gemma4:26b` | `dcode` + `muse-glimmer:30b` |
| :--- | :---: | :---: | :---: |
| `fizzbuzz` | 70.83s (✅) | 49.76s (✅) | 178.60s (✅) |
| `weather_client` | 86.66s (✅) | 54.29s (✅) | 186.78s (❌) |
| `reverse_words` | 77.41s (✅) | 52.10s (✅) | 192.77s (✅) |
| `prime_generator` | 83.16s (✅) | 55.05s (✅) | 241.15s (✅) |
| `fibonacci` | 94.12s (✅) | 50.49s (✅) | 183.10s (✅) |
| `search_replace` | 77.04s (❌) | 67.03s (✅) | 250.40s (✅) |
| `dir_tree_bash` | 75.28s (❌) | 206.86s (✅) | 600.00s (✅) |
| `android_counter` | 97.25s (✅) | 68.25s (✅) | 376.28s (✅) |
| `android_login` | 107.76s (✅) | 91.55s (✅) | 277.26s (✅) |
| `android_intent` | 114.14s (✅) | 107.56s (✅) | 343.69s (✅) |
| **Total Time** | **883.65s** (80% Success) | **802.94s** (100% Success) | **2830.03s** (90% Success) |

