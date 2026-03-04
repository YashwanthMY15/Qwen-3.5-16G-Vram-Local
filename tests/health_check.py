"""
Server health check and status monitoring.
"""

import sys
import time
import requests
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.config_loader import get_config, ServerConfig


def check_server_health(server: ServerConfig) -> dict:
    """Check if a server is running and healthy"""
    result = {
        "name": server.name,
        "port": server.port,
        "use_case": server.use_case,
        "healthy": False,
        "response_time_ms": 0,
        "error": None,
    }

    try:
        start = time.time()
        response = requests.get(server.health_url, timeout=5)
        elapsed = (time.time() - start) * 1000

        result["response_time_ms"] = round(elapsed, 2)
        result["healthy"] = response.status_code == 200

        if result["healthy"]:
            try:
                data = response.json()
                result["details"] = data
            except:
                pass
    except requests.exceptions.Timeout:
        result["error"] = "Timeout (5s)"
    except requests.exceptions.ConnectionError:
        result["error"] = "Connection refused (server not running)"
    except Exception as e:
        result["error"] = str(e)

    return result


def check_all_servers():
    """Check health of all configured servers"""
    config = get_config()

    print("\n" + "=" * 60)
    print("Qwen3.5 Server Health Check")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60 + "\n")

    results = []

    for key, server in config.servers.items():
        result = check_server_health(server)
        results.append(result)

        status = "[OK] HEALTHY" if result["healthy"] else "[X] DOWN"
        print(f"[{result['port']}] {server.name}")
        print(f"      Status: {status}")

        if result["healthy"]:
            print(f"      Response: {result['response_time_ms']}ms")
        else:
            print(f"      Error: {result['error']}")

        print()

    # Summary
    healthy = sum(1 for r in results if r["healthy"])
    total = len(results)

    print("-" * 60)
    print(f"Summary: {healthy}/{total} servers healthy")
    print("-" * 60)

    return results


def monitor_servers(interval: int = 10):
    """Continuously monitor servers"""
    print(f"Monitoring servers every {interval} seconds. Press Ctrl+C to stop.\n")

    try:
        while True:
            check_all_servers()
            print(f"\nNext check in {interval}s...\n")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Server health check")
    parser.add_argument("--monitor", action="store_true", help="Continuous monitoring")
    parser.add_argument(
        "--interval", type=int, default=10, help="Monitoring interval (seconds)"
    )

    args = parser.parse_args()

    if args.monitor:
        monitor_servers(args.interval)
    else:
        check_all_servers()
