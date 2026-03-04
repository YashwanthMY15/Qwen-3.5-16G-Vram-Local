"""
Comprehensive Benchmark Suite for Qwen3.5 LLM Servers
Tests speed, context scaling, concurrent handling, and quality.
"""

import asyncio
import json
import time
import sys
import base64
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from config.config_loader import get_config, ServerConfig

# Results directory
RESULTS_DIR = Path(__file__).parent.parent / "results"
RESULTS_DIR.mkdir(exist_ok=True)


@dataclass
class BenchmarkResult:
    """Single benchmark result"""

    server_key: str
    server_name: str
    port: int
    test_type: str
    test_name: str
    prompt: str
    success: bool
    response_text: str = ""
    error: str = ""
    total_time_seconds: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    prompt_speed_tps: float = 0.0
    gen_speed_tps: float = 0.0
    context_size: int = 0
    timestamp: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class BenchmarkSummary:
    """Summary of benchmark results"""

    server_key: str
    server_name: str
    test_type: str
    total_tests: int
    successful_tests: int
    failed_tests: int
    avg_total_time: float
    avg_prompt_speed: float
    avg_gen_speed: float
    avg_tokens_per_response: float

    def to_dict(self) -> Dict:
        return asdict(self)


class LLMBenchmark:
    """Comprehensive LLM benchmark suite"""

    def __init__(self):
        self.config = get_config()
        self.results: List[BenchmarkResult] = []

    def _make_request(
        self,
        server: ServerConfig,
        messages: List[Dict],
        max_tokens: int = 512,
        timeout: int = 120,
    ) -> Dict:
        """Make a request to a server"""
        payload = {
            "model": server.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": server.temp,
            "top_p": server.top_p,
        }

        try:
            start_time = time.time()
            response = requests.post(server.api_url, json=payload, timeout=timeout)
            elapsed = time.time() - start_time

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response": data["choices"][0]["message"]["content"],
                    "total_time": elapsed,
                    "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                    "completion_tokens": data.get("usage", {}).get(
                        "completion_tokens", 0
                    ),
                    "timings": data.get("timings", {}),
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text[:200]}",
                    "total_time": elapsed,
                }
        except requests.exceptions.Timeout:
            return {"success": False, "error": "Request timeout", "total_time": timeout}
        except Exception as e:
            return {"success": False, "error": str(e), "total_time": 0}

    def test_server_health(self, server: ServerConfig) -> bool:
        """Check if server is running"""
        try:
            response = requests.get(server.health_url, timeout=5)
            return response.status_code == 200
        except:
            return False

    def run_speed_test(
        self, server: ServerConfig, prompts: List[str], warmup: int = 2, runs: int = 5
    ) -> List[BenchmarkResult]:
        """Run speed benchmark on a server"""
        results = []

        # Warmup runs
        print(f"    Warming up ({warmup} runs)...")
        for _ in range(warmup):
            self._make_request(
                server, [{"role": "user", "content": "Hello"}], max_tokens=50
            )

        # Actual tests
        print(f"    Running speed tests ({runs} runs per prompt)...")
        for prompt in prompts:
            for run in range(runs):
                result_data = self._make_request(
                    server, [{"role": "user", "content": prompt}], max_tokens=256
                )

                result = BenchmarkResult(
                    server_key=server.use_case,
                    server_name=server.name,
                    port=server.port,
                    test_type="speed",
                    test_name=f"run_{run + 1}",
                    prompt=prompt[:100],
                    success=result_data.get("success", False),
                    response_text=result_data.get("response", "")[:200]
                    if result_data.get("success")
                    else "",
                    error=result_data.get("error", ""),
                    total_time_seconds=result_data.get("total_time", 0),
                    prompt_tokens=result_data.get("prompt_tokens", 0),
                    completion_tokens=result_data.get("completion_tokens", 0),
                    prompt_speed_tps=result_data.get("timings", {}).get(
                        "prompt_per_second", 0
                    ),
                    gen_speed_tps=result_data.get("timings", {}).get(
                        "predicted_per_second", 0
                    ),
                    timestamp=datetime.now().isoformat(),
                )
                results.append(result)

                status = "[OK]" if result.success else "[X]"
                print(
                    f"      {status} {prompt[:30]}... - {result.total_time_seconds:.2f}s"
                )

        return results

    def run_context_scaling_test(
        self, server: ServerConfig, context_sizes: List[int]
    ) -> List[BenchmarkResult]:
        """Test performance at different context sizes"""
        results = []

        # Generate prompts of different lengths
        base_text = "This is a test sentence for context scaling. " * 10

        print(f"    Testing context scaling...")
        for ctx_size in context_sizes:
            if ctx_size > server.context:
                print(
                    f"      Skipping {ctx_size} (exceeds server limit {server.context})"
                )
                continue

            # Create a prompt that fills the context
            tokens_approx = ctx_size // 4  # Rough token estimation
            prompt = (base_text * (tokens_approx // len(base_text.split()) + 1))[
                :tokens_approx
            ]
            prompt += "\n\nSummarize the above text in one sentence."

            result_data = self._make_request(
                server,
                [{"role": "user", "content": prompt}],
                max_tokens=100,
                timeout=180,
            )

            result = BenchmarkResult(
                server_key=server.use_case,
                server_name=server.name,
                port=server.port,
                test_type="context_scaling",
                test_name=f"context_{ctx_size}",
                prompt=f"[{len(prompt)} chars prompt]",
                success=result_data.get("success", False),
                response_text=result_data.get("response", "")[:200]
                if result_data.get("success")
                else "",
                error=result_data.get("error", ""),
                total_time_seconds=result_data.get("total_time", 0),
                prompt_tokens=result_data.get("prompt_tokens", 0),
                completion_tokens=result_data.get("completion_tokens", 0),
                prompt_speed_tps=result_data.get("timings", {}).get(
                    "prompt_per_second", 0
                ),
                gen_speed_tps=result_data.get("timings", {}).get(
                    "predicted_per_second", 0
                ),
                context_size=ctx_size,
                timestamp=datetime.now().isoformat(),
            )
            results.append(result)

            status = "[OK]" if result.success else "[X]"
            print(
                f"      {status} Context {ctx_size}: {result.total_time_seconds:.2f}s, {result.gen_speed_tps:.1f} t/s"
            )

        return results

    def run_concurrent_test(
        self, server: ServerConfig, prompts: List[str], num_concurrent: int = 5
    ) -> List[BenchmarkResult]:
        """Test concurrent request handling"""
        results = []

        print(f"    Testing {num_concurrent} concurrent requests...")

        def make_single_request(prompt: str, idx: int) -> BenchmarkResult:
            result_data = self._make_request(
                server, [{"role": "user", "content": prompt}], max_tokens=128
            )

            return BenchmarkResult(
                server_key=server.use_case,
                server_name=server.name,
                port=server.port,
                test_type="concurrent",
                test_name=f"concurrent_{idx}",
                prompt=prompt[:50],
                success=result_data.get("success", False),
                response_text=result_data.get("response", "")[:100]
                if result_data.get("success")
                else "",
                error=result_data.get("error", ""),
                total_time_seconds=result_data.get("total_time", 0),
                prompt_tokens=result_data.get("prompt_tokens", 0),
                completion_tokens=result_data.get("completion_tokens", 0),
                prompt_speed_tps=result_data.get("timings", {}).get(
                    "prompt_per_second", 0
                ),
                gen_speed_tps=result_data.get("timings", {}).get(
                    "predicted_per_second", 0
                ),
                timestamp=datetime.now().isoformat(),
            )

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = {
                executor.submit(make_single_request, prompt, i): i
                for i, prompt in enumerate(prompts[:num_concurrent])
            }

            for future in as_completed(futures):
                result = future.result()
                results.append(result)
                status = "[OK]" if result.success else "[X]"
                print(
                    f"      {status} Request completed: {result.total_time_seconds:.2f}s"
                )

        total_time = time.time() - start_time
        print(f"    Total time for {num_concurrent} requests: {total_time:.2f}s")
        print(f"    Throughput: {num_concurrent / total_time:.2f} requests/second")

        return results

    def run_vision_test(
        self, server: ServerConfig, image_path: str, prompts: List[str]
    ) -> List[BenchmarkResult]:
        """Test vision capabilities"""
        results = []

        if not server.mmproj:
            print(f"    Skipping vision test (no mmproj configured)")
            return results

        if not Path(image_path).exists():
            print(f"    Skipping vision test (image not found: {image_path})")
            return results

        # Encode image
        with open(image_path, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        ext = Path(image_path).suffix.lower()
        mime_type = "image/png" if ext == ".png" else "image/jpeg"

        print(f"    Testing vision with {len(prompts)} prompts...")

        for prompt in prompts:
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}"
                            },
                        },
                    ],
                }
            ]

            result_data = self._make_request(
                server, messages, max_tokens=200, timeout=60
            )

            result = BenchmarkResult(
                server_key=server.use_case,
                server_name=server.name,
                port=server.port,
                test_type="vision",
                test_name=f"vision_{prompt[:20]}",
                prompt=prompt,
                success=result_data.get("success", False),
                response_text=result_data.get("response", "")[:300]
                if result_data.get("success")
                else "",
                error=result_data.get("error", ""),
                total_time_seconds=result_data.get("total_time", 0),
                prompt_tokens=result_data.get("prompt_tokens", 0),
                completion_tokens=result_data.get("completion_tokens", 0),
                prompt_speed_tps=result_data.get("timings", {}).get(
                    "prompt_per_second", 0
                ),
                gen_speed_tps=result_data.get("timings", {}).get(
                    "predicted_per_second", 0
                ),
                timestamp=datetime.now().isoformat(),
            )
            results.append(result)

            status = "[OK]" if result.success else "[X]"
            print(f"      {status} {prompt[:40]}... - {result.total_time_seconds:.2f}s")

        return results

    def run_all_benchmarks(
        self,
        server_keys: List[str] = None,
        include_vision: bool = False,
        image_path: str = None,
    ) -> Dict[str, Any]:
        """Run all benchmarks on specified servers"""

        if server_keys is None:
            servers = self.config.get_enabled_servers()
        else:
            servers = [self.config.get_server(k) for k in server_keys]
            servers = [s for s in servers if s is not None]

        all_results = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "hardware": self.config._raw["hardware"],
                "servers_tested": [s.use_case for s in servers],
            },
            "results": [],
            "summaries": [],
        }

        print("\n" + "=" * 60)
        print("Qwen3.5 LLM Benchmark Suite")
        print("=" * 60)

        for server in servers:
            print(f"\n[{server.name}] - Port {server.port}")
            print("-" * 40)

            # Check server health
            if not self.test_server_health(server):
                print(f"  [!]  Server not responding, skipping...")
                continue

            print(f"  [OK] Server healthy")

            # Speed tests
            print(f"\n  1. Speed Tests")
            speed_results = self.run_speed_test(
                server,
                self.config.benchmark["prompts"]["coding"][:3],
                warmup=self.config.benchmark["warmup_runs"],
                runs=self.config.benchmark["test_runs"],
            )
            self.results.extend(speed_results)
            all_results["results"].extend([r.to_dict() for r in speed_results])

            # Context scaling tests
            print(f"\n  2. Context Scaling Tests")
            ctx_results = self.run_context_scaling_test(
                server, self.config.benchmark["context_sizes"]
            )
            self.results.extend(ctx_results)
            all_results["results"].extend([r.to_dict() for r in ctx_results])

            # Concurrent tests
            print(f"\n  3. Concurrent Request Tests")
            for num_concurrent in [1, 5]:
                concurrent_results = self.run_concurrent_test(
                    server,
                    self.config.benchmark["prompts"]["simple"],
                    num_concurrent=num_concurrent,
                )
                self.results.extend(concurrent_results)
                all_results["results"].extend([r.to_dict() for r in concurrent_results])

            # Vision tests (if enabled and server supports it)
            if include_vision and server.mmproj and image_path:
                print(f"\n  4. Vision Tests")
                vision_results = self.run_vision_test(
                    server,
                    image_path,
                    ["Describe this image.", "What objects do you see?"],
                )
                self.results.extend(vision_results)
                all_results["results"].extend([r.to_dict() for r in vision_results])

        # Generate summaries
        all_results["summaries"] = self._generate_summaries()

        return all_results

    def _generate_summaries(self) -> List[Dict]:
        """Generate summaries from collected results"""
        summaries = []

        # Group by server and test type
        grouped = {}
        for result in self.results:
            key = (result.server_key, result.test_type)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(result)

        for (server_key, test_type), results in grouped.items():
            successful = [r for r in results if r.success]
            failed = [r for r in results if not r.success]

            if successful:
                summary = BenchmarkSummary(
                    server_key=server_key,
                    server_name=results[0].server_name,
                    test_type=test_type,
                    total_tests=len(results),
                    successful_tests=len(successful),
                    failed_tests=len(failed),
                    avg_total_time=sum(r.total_time_seconds for r in successful)
                    / len(successful),
                    avg_prompt_speed=sum(r.prompt_speed_tps for r in successful)
                    / len(successful)
                    if any(r.prompt_speed_tps for r in successful)
                    else 0,
                    avg_gen_speed=sum(r.gen_speed_tps for r in successful)
                    / len(successful)
                    if any(r.gen_speed_tps for r in successful)
                    else 0,
                    avg_tokens_per_response=sum(r.completion_tokens for r in successful)
                    / len(successful),
                )
                summaries.append(summary.to_dict())

        return summaries

    def save_results(self, filename: str = None) -> str:
        """Save results to JSON file"""
        if filename is None:
            filename = f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = RESULTS_DIR / filename

        output = {
            "timestamp": datetime.now().isoformat(),
            "results": [r.to_dict() for r in self.results],
            "summaries": self._generate_summaries(),
        }

        with open(filepath, "w") as f:
            json.dump(output, f, indent=2)

        print(f"\nResults saved to: {filepath}")
        return str(filepath)

    def print_summary(self):
        """Print a summary of results"""
        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)

        summaries = self._generate_summaries()

        for summary in summaries:
            print(f"\n{summary['server_name']} - {summary['test_type']}")
            print(
                f"  Tests: {summary['successful_tests']}/{summary['total_tests']} passed"
            )
            print(f"  Avg Time: {summary['avg_total_time']:.2f}s")
            if summary["avg_gen_speed"] > 0:
                print(f"  Avg Gen Speed: {summary['avg_gen_speed']:.1f} t/s")
            if summary["avg_prompt_speed"] > 0:
                print(f"  Avg Prompt Speed: {summary['avg_prompt_speed']:.1f} t/s")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Qwen3.5 LLM Benchmark Suite")
    parser.add_argument(
        "--servers", nargs="+", help="Server keys to test (default: all enabled)"
    )
    parser.add_argument("--vision", action="store_true", help="Include vision tests")
    parser.add_argument("--image", type=str, help="Image path for vision tests")
    parser.add_argument("--output", type=str, help="Output filename")
    parser.add_argument("--quick", action="store_true", help="Quick test (fewer runs)")

    args = parser.parse_args()

    benchmark = LLMBenchmark()

    # Modify config for quick tests
    if args.quick:
        benchmark.config.benchmark["warmup_runs"] = 1
        benchmark.config.benchmark["test_runs"] = 2
        benchmark.config.benchmark["context_sizes"] = [4096, 16384]

    # Run benchmarks
    results = benchmark.run_all_benchmarks(
        server_keys=args.servers, include_vision=args.vision, image_path=args.image
    )

    # Save and print
    benchmark.save_results(args.output)
    benchmark.print_summary()


if __name__ == "__main__":
    main()
