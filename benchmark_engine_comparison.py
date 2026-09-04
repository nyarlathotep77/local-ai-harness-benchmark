import time
import json
import requests
import subprocess
import statistics
import os
import sys

def get_gpu_memory():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu", "--format=csv,nounits,noheader"],
            text=True
        ).strip()
        used, total, util = [x.strip() for x in out.split(",")]
        return float(used), float(total), float(util)
    except Exception as e:
        return 0.0, 0.0, 0.0

def test_inference_streaming(base_url, model_name, prompt, max_tokens=150, temperature=0.1):
    url = f"{base_url}/chat/completions"
    headers = {"Content-Type": "application/json", "Authorization": "Bearer dummy"}
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a concise programming assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "stream": True
    }
    
    t_start = time.time()
    t_first_token = None
    token_count = 0
    full_text = ""
    
    try:
        r = requests.post(url, headers=headers, json=payload, stream=True, timeout=120)
        r.raise_for_status()
        
        for line in r.iter_lines():
            if not line:
                continue
            line_str = line.decode('utf-8')
            if line_str.startswith("data: "):
                data_str = line_str[6:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    data = json.loads(data_str)
                    delta = data["choices"][0].get("delta", {})
                    content = delta.get("content", "") or delta.get("reasoning_content", "") or delta.get("reasoning", "")
                    if content:
                        if t_first_token is None:
                            t_first_token = time.time()
                        token_count += 1
                        full_text += content
                except Exception:
                    pass
                    
        t_end = time.time()
        ttft = (t_first_token - t_start) if t_first_token else (t_end - t_start)
        gen_time = (t_end - t_first_token) if t_first_token else (t_end - t_start)
        tps = (token_count / gen_time) if gen_time > 0 and token_count > 0 else 0.0
        total_duration = t_end - t_start
        
        return {
            "success": True,
            "total_duration": round(total_duration, 3),
            "ttft": round(ttft, 3),
            "tps": round(tps, 2),
            "tokens_generated": token_count,
            "sample_output": full_text[:120].replace('\n', ' ')
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "total_duration": round(time.time() - t_start, 3),
            "ttft": 0,
            "tps": 0,
            "tokens_generated": 0
        }

def run_suite():
    print("=== STARTING OLLAMA VS LM STUDIO ENGINE COMPARISON ===")
    vram_used, vram_total, _ = get_gpu_memory()
    print(f"System GPU VRAM: Total {vram_total} MB | Currently Used: {vram_used} MB\n")
    
    test_prompts = [
        ("Short Prompt (Code Generation)", "Write a python function to compute the Levenshtein distance between two strings with explanation."),
        ("Medium Prompt (Algorithm + Reasoning)", "Explain the Raft Consensus Algorithm in detail, focusing on leader election, log replication, and how split-brain scenarios are mitigated. Provide pseudo-code."),
        ("Synthetic 2K-Token Context QA", ("In a distributed database system with multi-version concurrency control (MVCC), " * 60) + "Explain how garbage collection of obsolete row versions is handled without blocking read operations.")
    ]
    
    configs = [
        {
            "name": "LM Studio",
            "base_url": "http://localhost:1234/v1",
            "model": "qwen3.8-27b"
        },
        {
            "name": "Ollama",
            "base_url": "http://localhost:11434/v1",
            "model": "qwen3.8:27b"
        }
    ]
    
    results = {cfg["name"]: [] for cfg in configs}
    
    # Warmup
    print("Performing warmup queries...")
    for cfg in configs:
        print(f"Warming up {cfg['name']}...")
        test_inference_streaming(cfg["base_url"], cfg["model"], "Hello, ready?", max_tokens=10)
        time.sleep(1)
        
    print("\nStarting benchmark runs (3 iterations per prompt)...")
    
    for label, prompt in test_prompts:
        print(f"\n--- Running: {label} ---")
        for cfg in configs:
            name = cfg["name"]
            print(f"Testing {name} ({cfg['model']})...")
            runs = []
            for i in range(3):
                vram_before, _, _ = get_gpu_memory()
                res = test_inference_streaming(cfg["base_url"], cfg["model"], prompt, max_tokens=150)
                vram_after, _, _ = get_gpu_memory()
                res["vram_used_mb"] = vram_after
                runs.append(res)
                print(f"  Run {i+1}: TTFT={res['ttft']}s | TPS={res['tps']} tok/s | Total={res['total_duration']}s | GenTokens={res['tokens_generated']} | VRAM={vram_after}MB")
                time.sleep(1)
                
            avg_ttft = statistics.mean([r["ttft"] for r in runs if r["success"]])
            avg_tps = statistics.mean([r["tps"] for r in runs if r["success"]])
            avg_tot = statistics.mean([r["total_duration"] for r in runs if r["success"]])
            avg_vram = statistics.mean([r["vram_used_mb"] for r in runs if r["success"]])
            
            results[name].append({
                "prompt_label": label,
                "avg_ttft": round(avg_ttft, 3),
                "avg_tps": round(avg_tps, 2),
                "avg_duration": round(avg_tot, 3),
                "avg_vram_mb": round(avg_vram, 1),
                "runs": runs
            })
            
    # Summary JSON output
    out_file = "engine_benchmark_results.json"
    with open(out_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nBenchmark completed! Raw results saved to {out_file}")

if __name__ == "__main__":
    run_suite()
