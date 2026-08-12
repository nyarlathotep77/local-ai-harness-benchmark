import os
import re
import sys
import time
import csv
import subprocess
import shutil
import argparse
from pathlib import Path

# 10 test cases (7 original + 3 Android)
TESTS = [
    {
        "id": "fizzbuzz",
        "prompt": "Write a python script fizzbuzz.py that prints FizzBuzz for numbers 1 to 100.",
        "target_file": "fizzbuzz.py",
        "verification_cmd": "python3 fizzbuzz.py",
        "expected_kw": "FizzBuzz"
    },
    {
        "id": "weather_client",
        "prompt": "Write a python script weather.py that makes a GET request to https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current_weather=true and prints the current temperature from the JSON response. Do not use external libraries, use the standard urllib library.",
        "target_file": "weather.py",
        "verification_cmd": "python3 weather.py",
        "expected_kw": "temperature"
    },
    {
        "id": "reverse_words",
        "prompt": "Write a python script reverse_words.py that contains a function reverse_words(sentence: str) -> str that reverses the order of words in a sentence (e.g. 'hello world' -> 'world hello'). Include assertions in a main block to verify it.",
        "target_file": "reverse_words.py",
        "verification_cmd": "python3 reverse_words.py",
        "expected_kw": ""
    },
    {
        "id": "prime_generator",
        "prompt": "Write a python script primes.py that contains a function is_prime(n: int) -> bool and prints the first 20 prime numbers.",
        "target_file": "primes.py",
        "verification_cmd": "python3 primes.py",
        "expected_kw": "2"
    },
    {
        "id": "fibonacci",
        "prompt": "Write a python script fibonacci.py that contains a function fib(n: int) -> int returning the n-th Fibonacci number. Print the first 15 Fibonacci numbers.",
        "target_file": "fibonacci.py",
        "verification_cmd": "python3 fibonacci.py",
        "expected_kw": "0"
    },
    {
        "id": "search_replace",
        "prompt": "Write a python script replace_text.py that takes three command line arguments: a file path, a target string and a replacement string. It should replace the target string with the replacement string in that file. It should handle basic errors like file not found.",
        "target_file": "replace_text.py",
        "verification_cmd": "echo 'hello world' > test.txt && python3 replace_text.py test.txt 'world' 'earth' && cat test.txt",
        "expected_kw": "hello earth"
    },
    {
        "id": "dir_tree_bash",
        "prompt": "Write a bash script dir_tree.sh that lists all files and directories recursively starting from a given directory path in a tree-like visual format, without using the 'tree' command. The script must take an optional directory argument (defaulting to the current directory).",
        "target_file": "dir_tree.sh",
        "verification_cmd": "bash dir_tree.sh",
        "expected_kw": ""
    },
    {
        "id": "android_counter",
        "prompt": "Create a simple Android Jetpack Compose app source file structure. In app/src/main/java/com/example/counterapp/MainActivity.kt, write a MainActivity class extending ComponentActivity and a @Composable screen containing a Button and a Text. Clicking the Button should increment a counter shown in the Text. Also create a basic app/src/main/AndroidManifest.xml declaring the activity.",
        "target_file": "app/src/main/java/com/example/counterapp/MainActivity.kt",
        "verification_cmd": "grep -q 'package com.example.counterapp' app/src/main/java/com/example/counterapp/MainActivity.kt && grep -q '@Composable' app/src/main/java/com/example/counterapp/MainActivity.kt && grep -q '<manifest' app/src/main/AndroidManifest.xml",
        "expected_kw": ""
    },
    {
        "id": "android_login",
        "prompt": "Create a simple Android Jetpack Compose login screen app structure. Write LoginActivity.kt in app/src/main/java/com/example/loginapp/LoginActivity.kt with fields for Username and Password and a Login button. The Login button should show a Toast message on click saying 'Logging in...'. Also write a basic app/src/main/AndroidManifest.xml.",
        "target_file": "app/src/main/java/com/example/loginapp/LoginActivity.kt",
        "verification_cmd": "grep -q 'package com.example.loginapp' app/src/main/java/com/example/loginapp/LoginActivity.kt && grep -q 'Toast.makeText' app/src/main/java/com/example/loginapp/LoginActivity.kt && grep -q '<manifest' app/src/main/AndroidManifest.xml",
        "expected_kw": ""
    },
    {
        "id": "android_intent",
        "prompt": "Create a simple Android app that handles incoming SEND intents (sharing text). Write ShareActivity.kt in app/src/main/java/com/example/shareapp/ShareActivity.kt which extracts the shared text from the intent extra Intent.EXTRA_TEXT and displays it in a Compose Text component. Also write app/src/main/AndroidManifest.xml showing the intent filter for action SEND and mimeType text/plain.",
        "target_file": "app/src/main/java/com/example/shareapp/ShareActivity.kt",
        "verification_cmd": "grep -q 'package com.example.shareapp' app/src/main/java/com/example/shareapp/ShareActivity.kt && grep -q 'Intent.EXTRA_TEXT' app/src/main/java/com/example/shareapp/ShareActivity.kt && grep -q 'action.SEND' app/src/main/AndroidManifest.xml",
        "expected_kw": ""
    }
]

def load_existing_results(csv_path):
    results = []
    if not csv_path.exists():
        return results
    try:
        with open(csv_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # If 'model' column is missing, default it to 'gemma4:26b'
                if "model" not in row:
                    row["model"] = "gemma4:26b"
                row["duration_sec"] = float(row["duration_sec"]) if row.get("duration_sec") else 0.0
                row["file_created"] = row["file_created"] == "True"
                row["verified_correct"] = row["verified_correct"] == "True"
                row["lines_of_code"] = int(row["lines_of_code"]) if row.get("lines_of_code") else 0
                row["exit_code"] = int(row["exit_code"]) if row.get("exit_code") else 0
                row["harness_output_length"] = int(row["harness_output_length"]) if row.get("harness_output_length") else 0
                results.append(row)
    except Exception as e:
        print(f"Warning: Could not read existing CSV at {csv_path}: {e}")
    return results

def save_results(csv_path, results):
    fields = [
        "harness", "model", "test_id", "duration_sec", "file_created", 
        "verified_correct", "lines_of_code", "exit_code", 
        "harness_output_length"
    ]
    try:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for r in results:
                row = {
                    "harness": r["harness"],
                    "model": r.get("model", "gemma4:26b"),
                    "test_id": r["test_id"],
                    "duration_sec": r["duration_sec"],
                    "file_created": str(r["file_created"]),
                    "verified_correct": str(r["verified_correct"]),
                    "lines_of_code": r["lines_of_code"],
                    "exit_code": r["exit_code"],
                    "harness_output_length": r["harness_output_length"]
                }
                writer.writerow(row)
        print(f"Results successfully saved to {csv_path}")
    except Exception as e:
        print(f"Error: Could not save CSV at {csv_path}: {e}")

def run_test(harness, model, test_case):
    test_id = test_case["id"]
    prompt = test_case["prompt"]
    target_file = test_case["target_file"]
    ver_cmd = test_case["verification_cmd"]
    expected_kw = test_case["expected_kw"]
    
    test_dir = Path(f"/tmp/benchmark_{harness}_{model.replace(':', '_')}_{test_id}")
    if test_dir.exists():
        shutil.rmtree(test_dir)
    test_dir.mkdir(parents=True)
    
    print(f"\n==========================================")
    print(f"Running {harness.upper()} ({model}) on task: {test_id}")
    print(f"Directory: {test_dir}")
    print(f"==========================================")
    
    # Select command line
    if harness in ("dcode", "dcode-dev"):
        cmd = [harness, "-n", prompt, "-S", "all"]
        if model:
            cmd += ["-M", f"ollama:{model}"]
    else:  # claude
        cmd = ["claude", "-p", prompt, "--dangerously-skip-permissions"]
        
    start_time = time.time()
    try:
        env = os.environ.copy()
        if harness == "claude" and model:
            env["ANTHROPIC_MODEL"] = model
            
        res = subprocess.run(
            cmd,
            cwd=str(test_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=600,
            env=env
        )
        duration = time.time() - start_time
        exit_code = res.returncode
        stdout = res.stdout
        stderr = res.stderr
    except subprocess.TimeoutExpired as exc:
        duration = 600.0
        exit_code = 124
        stdout = exc.stdout if exc.stdout else ""
        stderr = exc.stderr if exc.stderr else ""
        print("Task timed out!")
        
    # Check if target file exists
    target_path = test_dir / target_file
    file_created = target_path.exists()
    
    # Run verification command
    verified = False
    ver_output = ""
    actual_target_path = target_path
    if not file_created:
        # Let's search if the file was created at some different subpath
        found = list(test_dir.glob(f"**/{Path(target_file).name}"))
        if found:
            actual_target_path = found[0]
            file_created = True
            
    if file_created:
        try:
            run_cmd = ver_cmd
            ver_res = subprocess.run(
                run_cmd,
                shell=True,
                cwd=str(test_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            ver_output = ver_res.stdout + "\n" + ver_res.stderr
            if ver_res.returncode == 0:
                if not expected_kw or expected_kw in ver_output:
                    verified = True
        except Exception as e:
            ver_output = f"Verification exception: {e}"
            
    # Measure lines of code
    loc = 0
    if file_created:
        try:
            loc = len(actual_target_path.read_text().splitlines())
        except Exception:
            pass
            
    print(f"Harness: {harness}")
    print(f"Model: {model}")
    print(f"Duration: {duration:.2f}s")
    print(f"File Created: {file_created}")
    print(f"Verified Correct: {verified}")
    print(f"Lines of Code: {loc}")
        
    return {
        "harness": harness,
        "model": model,
        "test_id": test_id,
        "duration_sec": round(duration, 2),
        "file_created": file_created,
        "verified_correct": verified,
        "lines_of_code": loc,
        "exit_code": exit_code,
        "harness_output_length": len(stdout + stderr)
    }

def generate_comparison_report(all_results, workspace_dir=None):
    # Group results by (harness, model)
    configs = {}
    for r in all_results:
        cfg_key = (r["harness"], r["model"])
        if cfg_key not in configs:
            configs[cfg_key] = {}
        configs[cfg_key][r["test_id"]] = r
        
    # Build Markdown report
    report = "# Local AI Coding Assistant Benchmarks: Performance Comparison\n\n"
    report += "This report compares different local AI coding assistant setups running on local hardware.\n\n"
    
    # Workstation Specs (hardcoded as reference)
    report += "## 💻 Workstation Reference\n"
    report += "- **OS**: Ubuntu 24.04.1 LTS\n"
    report += "- **CPU**: AMD Ryzen 7 8845HS (8 Cores, 16 Threads)\n"
    report += "- **RAM**: 64 GB DDR5\n"
    report += "- **GPU**: NVIDIA GeForce RTX 5060 Ti (16 GB VRAM)\n\n"
    
    # Table of configurations
    report += "## 📊 Evaluated Configurations\n\n"
    report += "| Harness | Model | Tasks Completed | Success Rate |\n"
    report += "| :--- | :--- | :---: | :---: |\n"
    for (harness, model), tasks in sorted(configs.items()):
        success_count = sum(1 for t in tasks.values() if t["verified_correct"])
        total_tasks = len(TESTS)
        rate = f"{(success_count / total_tasks * 100):.1f}%" if total_tasks > 0 else "0.0%"
        report += f"| `{harness}` | `{model}` | {success_count}/{total_tasks} | **{rate}** |\n"
    report += "\n---\n\n"
    
    # Detailed Task Performance
    report += "## ⏱️ Detailed Task Times (seconds)\n\n"
    
    # Build headers dynamically based on configurations
    sorted_cfgs = sorted(configs.keys())
    headers = [f"`{h}` + `{m}`" for h, m in sorted_cfgs]
    report += "| Test ID | " + " | ".join(headers) + " |\n"
    report += "| :--- | " + " | ".join([":---:" for _ in headers]) + " |\n"
    
    # For each task, list duration for each configuration
    for t_case in TESTS:
        tid = t_case["id"]
        row_str = f"| `{tid}`"
        for cfg in sorted_cfgs:
            task_res = configs[cfg].get(tid)
            if task_res:
                status_icon = "✅" if task_res["verified_correct"] else "❌"
                row_str += f" | {task_res['duration_sec']:.2f}s ({status_icon})"
            else:
                row_str += " | N/A"
        row_str += " |"
        report += row_str + "\n"
        
    # Totals Row
    total_row = "| **Total Time**"
    for cfg in sorted_cfgs:
        task_list = configs[cfg].values()
        total_time = sum(t["duration_sec"] for t in task_list)
        success_count = sum(1 for t in task_list if t["verified_correct"])
        total_tasks = len(TESTS)
        rate = f"{(success_count / total_tasks * 100):.0f}%" if total_tasks > 0 else "0%"
        total_row += f" | **{total_time:.2f}s** ({rate} Success)"
    total_row += " |"
    report += total_row + "\n\n"
    
    # Save report
    report_paths = [Path("~/Documents/benchmark_report.md").expanduser()]
    if workspace_dir:
        report_paths.append(workspace_dir / "benchmark_report.md")
        
    for report_path in report_paths:
        try:
            report_path.write_text(report, encoding="utf-8")
            print(f"Markdown report written to {report_path}")
        except Exception as e:
            print(f"Error saving report at {report_path}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Run local AI coding assistant benchmarks.")
    parser.add_argument("--harness", type=str, default="dcode", choices=["dcode", "dcode-dev", "claude"],
                        help="Harness command to benchmark (default: dcode)")
    parser.add_argument("--model", type=str, default="muse-glimmer:30b",
                        help="Model name in Ollama (default: muse-glimmer:30b)")
    parser.add_argument("--run-legacy-all", action="store_true",
                        help="If set, run the full hardcoded gemma4 benchmark suite (original behavior)")
    args = parser.parse_args()

    workspace_dir = Path(__file__).resolve().parent
    local_csv_path = workspace_dir / "benchmark_results.csv"
    doc_csv_path = Path("~/Documents/benchmark_results.csv").expanduser()
    
    # Load existing results from local workspace CSV or Documents CSV
    existing_results = []
    if local_csv_path.exists():
        existing_results = load_existing_results(local_csv_path)
    elif doc_csv_path.exists():
        existing_results = load_existing_results(doc_csv_path)
        
    if args.run_legacy_all:
        results = []
        # Legacy behavior: run dcode (gemma4) and claude (gemma4) from scratch
        for t in TESTS:
            res = run_test("dcode", "gemma4:26b", t)
            results.append(res)
            time.sleep(2)
        for t in TESTS:
            res = run_test("claude", "gemma4:26b", t)
            results.append(res)
            time.sleep(2)
            
        # Overwrite all results
        save_results(doc_csv_path, results)
        save_results(local_csv_path, results)
        generate_comparison_report(results, workspace_dir)
    else:
        # Run specific harness and model
        harness = args.harness
        model = args.model
        
        print(f"\nStarting benchmark for configuration: {harness} with model: {model}\n")
        new_results = []
        for t in TESTS:
            res = run_test(harness, model, t)
            new_results.append(res)
            time.sleep(2)
            
        # Merge new results with existing ones
        # Remove any existing rows matching the current (harness, model) configuration
        merged = [r for r in existing_results if not (r["harness"] == harness and r["model"] == model)]
        merged.extend(new_results)
        
        # Save merged results back to CSV files
        save_results(doc_csv_path, merged)
        save_results(local_csv_path, merged)
        
        # Generate the multi-configuration report
        generate_comparison_report(merged, workspace_dir)

if __name__ == "__main__":
    main()
