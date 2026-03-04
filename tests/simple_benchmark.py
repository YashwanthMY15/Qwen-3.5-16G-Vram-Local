"""
Simple single-server benchmark.
Run one server at a time for clean results.
"""

import requests
import time
import json
from datetime import datetime

# Test prompts
PROMPTS = {
    "simple": [
        "What is 2+2?",
        "Say 'hello'",
    ],
    "coding": [
        "Write a Python function to calculate fibonacci numbers",
        "Write a function to check if a string is a palindrome",
    ],
    "reasoning": [
        "If it takes 5 machines 5 minutes to make 5 widgets, how long for 100 machines to make 100 widgets?",
    ],
}


def benchmark_server(port, warmup=True, runs=3):
    """Benchmark a single server"""
    url = f"http://127.0.0.1:{port}/v1/chat/completions"

    # Check health
    try:
        r = requests.get(f"http://127.0.0.1:{port}/health", timeout=5)
        if r.status_code != 200:
            return {"error": "Server not healthy"}
    except:
        return {"error": "Server not responding"}

    results = {"port": port, "timestamp": datetime.now().isoformat(), "tests": {}}

    # Warmup
    if warmup:
        print("  Warming up...")
        for _ in range(2):
            try:
                requests.post(
                    url,
                    json={
                        "model": "test",
                        "messages": [{"role": "user", "content": "Hi"}],
                        "max_tokens": 10,
                    },
                    timeout=30,
                )
            except:
                pass

    # Run tests
    for category, prompts in PROMPTS.items():
        print(f"  Testing {category}...")
        category_results = []

        for prompt in prompts:
            for run in range(runs):
                try:
                    start = time.time()
                    r = requests.post(
                        url,
                        json={
                            "model": "test",
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 256,
                            "temperature": 0.7,
                        },
                        timeout=60,
                    )
                    elapsed = time.time() - start

                    if r.status_code == 200:
                        data = r.json()
                        tokens = data.get("usage", {}).get("completion_tokens", 0)
                        timings = data.get("timings", {})

                        result = {
                            "prompt": prompt[:50],
                            "time": round(elapsed, 2),
                            "tokens": tokens,
                            "gen_tps": timings.get("predicted_per_second", 0),
                            "prompt_tps": timings.get("prompt_per_second", 0),
                            "success": True,
                        }
                        print(
                            f"    [OK] {prompt[:30]}... {elapsed:.2f}s, {result['gen_tps']:.1f} t/s"
                        )
                    else:
                        result = {
                            "prompt": prompt[:50],
                            "success": False,
                            "error": r.status_code,
                        }
                        print(f"    [X] {prompt[:30]}... HTTP {r.status_code}")

                    category_results.append(result)
                except Exception as e:
                    print(f"    [X] {prompt[:30]}... Error: {e}")
                    category_results.append(
                        {"prompt": prompt[:50], "success": False, "error": str(e)}
                    )

        results["tests"][category] = category_results

    # Calculate averages
    all_successful = []
    for cat_results in results["tests"].values():
        all_successful.extend([r for r in cat_results if r.get("success")])

    if all_successful:
        results["summary"] = {
            "total_tests": len(all_successful),
            "avg_time": round(
                sum(r["time"] for r in all_successful) / len(all_successful), 2
            ),
            "avg_gen_tps": round(
                sum(r["gen_tps"] for r in all_successful) / len(all_successful), 1
            ),
            "avg_prompt_tps": round(
                sum(r["prompt_tps"] for r in all_successful) / len(all_successful), 1
            ),
            "avg_tokens": round(
                sum(r["tokens"] for r in all_successful) / len(all_successful), 1
            ),
        }

    return results


if __name__ == "__main__":
    import sys

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8003

    print(f"\n{'=' * 50}")
    print(f"Benchmarking server on port {port}")
    print(f"{'=' * 50}\n")

    results = benchmark_server(port)

    if "error" in results:
        print(f"\nError: {results['error']}")
        sys.exit(1)

    print(f"\n{'=' * 50}")
    print("SUMMARY")
    print(f"{'=' * 50}")

    if "summary" in results:
        s = results["summary"]
        print(f"  Total tests: {s['total_tests']}")
        print(f"  Avg time: {s['avg_time']}s")
        print(f"  Avg gen speed: {s['avg_gen_tps']} t/s")
        print(f"  Avg prompt speed: {s['avg_prompt_tps']} t/s")

    # Save results
    filename = f"benchmark_port{port}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {filename}")
