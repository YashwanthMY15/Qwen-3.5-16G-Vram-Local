"""
Quick model comparison test.
Runs identical prompts on all available servers and compares results.
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.config_loader import get_config, ServerConfig
import requests


def test_single_server(server: ServerConfig, prompt: str) -> dict:
    """Test a single server with a prompt"""
    url = f"http://127.0.0.1:{server.port}/v1/chat/completions"

    payload = {
        "model": server.model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 256,
        "temperature": server.temp,
    }

    try:
        start = time.time()
        response = requests.post(url, json=payload, timeout=60)
        elapsed = time.time() - start

        if response.status_code == 200:
            data = response.json()
            return {
                "server": server.name,
                "port": server.port,
                "success": True,
                "response": data["choices"][0]["message"]["content"],
                "time": elapsed,
                "tokens": data.get("usage", {}).get("completion_tokens", 0),
                "tps": data.get("timings", {}).get("predicted_per_second", 0),
            }
        else:
            return {
                "server": server.name,
                "port": server.port,
                "success": False,
                "error": f"HTTP {response.status_code}",
                "time": elapsed,
            }
    except Exception as e:
        return {
            "server": server.name,
            "port": server.port,
            "success": False,
            "error": str(e),
            "time": 0,
        }


def compare_models(prompt: str, server_keys: list = None):
    """Compare all models on the same prompt"""
    config = get_config()

    if server_keys:
        servers = [config.get_server(k) for k in server_keys]
        servers = [s for s in servers if s]
    else:
        servers = config.get_enabled_servers()

    print(f"\n{'=' * 60}")
    print(f"Comparing models on prompt: '{prompt[:50]}...'")
    print(f"{'=' * 60}\n")

    results = []

    for server in servers:
        print(f"Testing {server.name} (port {server.port})...")
        result = test_single_server(server, prompt)
        results.append(result)

        if result["success"]:
            print(f"  [OK] Time: {result['time']:.2f}s")
            if result.get("tps"):
                print(f"    Speed: {result['tps']:.1f} t/s")
            print(f"    Response: {result['response'][:100]}...")
        else:
            print(f"  [X] Error: {result.get('error', 'Unknown')}")
        print()

    # Print comparison table
    print("\n" + "=" * 60)
    print("COMPARISON TABLE")
    print("=" * 60)
    print(f"{'Server':<25} {'Time':>8} {'Speed':>10} {'Tokens':>8}")
    print("-" * 60)

    for r in results:
        if r["success"]:
            speed = f"{r.get('tps', 0):.1f} t/s" if r.get("tps") else "N/A"
            print(f"{r['server']:<25} {r['time']:>6.2f}s {speed:>10} {r['tokens']:>8}")
        else:
            print(f"{r['server']:<25} {'FAILED':>8}")

    return results


def run_comparison_suite():
    """Run a suite of comparison tests"""

    test_prompts = [
        ("Simple", "What is 2 + 2?"),
        ("Coding", "Write a Python function to check if a number is prime."),
        (
            "Reasoning",
            "If it takes 5 machines 5 minutes to make 5 widgets, how long would it take 100 machines to make 100 widgets?",
        ),
        ("Creative", "Write a haiku about artificial intelligence."),
    ]

    all_results = {}

    for category, prompt in test_prompts:
        print(f"\n\n{'#' * 60}")
        print(f"# {category.upper()} TEST")
        print(f"{'#' * 60}")

        results = compare_models(prompt)
        all_results[category] = results

    return all_results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Compare LLM models")
    parser.add_argument("--prompt", type=str, help="Single prompt to test")
    parser.add_argument("--servers", nargs="+", help="Server keys to test")
    parser.add_argument(
        "--suite", action="store_true", help="Run full comparison suite"
    )

    args = parser.parse_args()

    if args.suite:
        run_comparison_suite()
    elif args.prompt:
        compare_models(args.prompt, args.servers)
    else:
        # Default: run a quick comparison
        compare_models("Write a Python function to calculate fibonacci numbers.")
