"""
Unified Vision Test for all vision-capable Qwen3.5 servers.
Tests image understanding across different models.
"""

import base64
import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from config.config_loader import get_config, ServerConfig
import requests


# Test images directory
TEST_IMAGES_DIR = Path(__file__).parent.parent / "test_images"


def encode_image(image_path: str) -> str:
    """Encode an image file to base64"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def get_mime_type(image_path: str) -> str:
    """Get MIME type from file extension"""
    ext = Path(image_path).suffix.lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    return mime_map.get(ext, "image/png")


def test_vision(
    server: ServerConfig, image_path: str, prompt: str, max_tokens: int = 200
) -> dict:
    """Test vision capabilities on a server"""

    if not server.mmproj:
        return {
            "server": server.name,
            "port": server.port,
            "success": False,
            "error": "No mmproj configured for this server",
        }

    if not Path(image_path).exists():
        return {
            "server": server.name,
            "port": server.port,
            "success": False,
            "error": f"Image not found: {image_path}",
        }

    # Encode image
    image_data = encode_image(image_path)
    mime_type = get_mime_type(image_path)

    # Build message with image
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:{mime_type};base64,{image_data}"},
                },
            ],
        }
    ]

    payload = {
        "model": server.model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": server.temp,
    }

    try:
        start = time.time()
        response = requests.post(server.api_url, json=payload, timeout=120)
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
                "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                "tps": data.get("timings", {}).get("predicted_per_second", 0),
                "prompt_tps": data.get("timings", {}).get("prompt_per_second", 0),
            }
        else:
            return {
                "server": server.name,
                "port": server.port,
                "success": False,
                "error": f"HTTP {response.status_code}: {response.text[:200]}",
                "time": elapsed,
            }
    except Exception as e:
        return {
            "server": server.name,
            "port": server.port,
            "success": False,
            "error": str(e),
        }


def get_vision_servers():
    """Get all servers with vision capability"""
    config = get_config()
    return [s for s in config.servers.values() if s.mmproj]


def run_vision_comparison(
    image_path: str, prompt: str = "Describe this image in detail."
):
    """Compare vision capabilities across all vision-capable servers"""

    vision_servers = get_vision_servers()

    if not vision_servers:
        print("No vision-capable servers configured!")
        return []

    print("\n" + "=" * 60)
    print("Vision Comparison Test")
    print("=" * 60)
    print(f"Image: {image_path}")
    print(f"Prompt: {prompt}")
    print(f"Servers: {len(vision_servers)}")
    print("=" * 60 + "\n")

    results = []

    for server in vision_servers:
        print(f"Testing {server.name} (port {server.port})...")
        result = test_vision(server, image_path, prompt)
        results.append(result)

        if result["success"]:
            print(f"  ✓ Time: {result['time']:.2f}s")
            if result.get("tps"):
                print(f"    Gen Speed: {result['tps']:.1f} t/s")
                print(f"    Prompt Speed: {result['prompt_tps']:.1f} t/s")
            print(f"    Response: {result['response'][:150]}...")
        else:
            print(f"  ✗ Error: {result['error']}")
        print()

    # Print comparison table
    print("\n" + "=" * 60)
    print("VISION COMPARISON RESULTS")
    print("=" * 60)
    print(f"{'Server':<25} {'Time':>8} {'Gen t/s':>10} {'Tokens':>8}")
    print("-" * 60)

    for r in results:
        if r["success"]:
            tps = f"{r.get('tps', 0):.1f}" if r.get("tps") else "N/A"
            print(f"{r['server']:<25} {r['time']:>6.2f}s {tps:>10} {r['tokens']:>8}")
        else:
            print(f"{r['server']:<25} {'FAILED':>8}")

    return results


def run_vision_suite(image_path: str = None):
    """Run a suite of vision tests"""

    # Use default test image if none provided
    if image_path is None:
        # Check for existing test images
        test_image = Path(__file__).parent.parent / "test_image.png"
        if not test_image.exists():
            test_image = Path(__file__).parent.parent / "complex_test.png"

        if not test_image.exists():
            print("No test image found!")
            print("Please provide an image path: python vision_test.py <image_path>")
            return

        image_path = str(test_image)

    test_prompts = [
        ("Basic Description", "Describe this image briefly."),
        (
            "Detailed Analysis",
            "Describe this image in detail, including all objects, colors, and any text you can see.",
        ),
        (
            "Object Count",
            "How many distinct objects can you identify in this image? List them.",
        ),
        ("Context", "What is happening in this image? What story does it tell?"),
    ]

    all_results = {}

    for category, prompt in test_prompts:
        print(f"\n\n{'#' * 60}")
        print(f"# {category.upper()}")
        print(f"{'#' * 60}")

        results = run_vision_comparison(image_path, prompt)
        all_results[category] = results

    return all_results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Vision test for Qwen3.5 models")
    parser.add_argument("image", nargs="?", help="Image file path")
    parser.add_argument(
        "--prompt",
        type=str,
        default="Describe this image in detail.",
        help="Prompt to use",
    )
    parser.add_argument("--suite", action="store_true", help="Run full test suite")
    parser.add_argument("--port", type=int, help="Test specific server by port")

    args = parser.parse_args()

    if args.suite:
        run_vision_suite(args.image)
    elif args.port:
        # Test specific server
        config = get_config()
        server = config.get_server_by_port(args.port)
        if server:
            if args.image:
                result = test_vision(server, args.image, args.prompt)
                if result["success"]:
                    print(f"\nResponse:\n{result['response']}")
                else:
                    print(f"Error: {result['error']}")
            else:
                print("Please provide an image path")
        else:
            print(f"No server found on port {args.port}")
    elif args.image:
        run_vision_comparison(args.image, args.prompt)
    else:
        # Run with default test image
        run_vision_suite()
