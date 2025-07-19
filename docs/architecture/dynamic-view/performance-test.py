#!/usr/bin/env python3
"""
Performance test script for InnoAlias game flow
Measures execution time of the complete game creation and gameplay scenario
"""

import argparse
import asyncio
import statistics
import time
from typing import Any

import aiohttp


class InnoAliasPerformanceTest:
    def __init__(self, base_url: str = "http://localhost"):
        self.base_url = base_url
        self.session = None
        self.results = {
            "authentication": [],
            "game_creation": [],
            "game_start": [],
            "gameplay_round": [],
            "game_end": [],
            "leaderboard": [],
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_authentication(self) -> dict[str, Any]:
        """Test user authentication flow"""
        start_time = time.time()

        login_data = {"username": "test@example.com", "password": "testpassword123"}

        if not self.session:
            return {
                "success": False,
                "duration_ms": 0,
                "error": "Session not initialized",
            }

        try:
            async with self.session.post(
                f"{self.base_url}/api/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            ) as response:
                end_time = time.time()
                duration = (end_time - start_time) * 1000  # Convert to milliseconds

                if response.status == 200:
                    token_data = await response.json()
                    return {
                        "success": True,
                        "duration_ms": duration,
                        "token": token_data.get("access_token"),
                    }
                else:
                    return {
                        "success": False,
                        "duration_ms": duration,
                        "error": f"HTTP {response.status}",
                    }
        except Exception as e:
            end_time = time.time()
            duration = (end_time - start_time) * 1000
            return {"success": False, "duration_ms": duration, "error": str(e)}

    async def test_game_creation(self, token: str) -> dict[str, Any]:
        """Test game creation flow"""
        start_time = time.time()

        game_data = {
            "host_id": "test_host_123",
            "number_of_teams": 2,
            "deck": ["apple", "banana", "cherry", "date", "elderberry"],
            "words_amount": 5,
            "time_for_guessing": 60,
            "tries_per_player": 3,
            "right_answers_to_advance": 2,
            "rotate_masters": True,
        }

        headers = {"Authorization": f"Bearer {token}"}

        if not self.session:
            return {
                "success": False,
                "duration_ms": 0,
                "error": "Session not initialized",
            }

        try:
            async with self.session.post(
                f"{self.base_url}/api/game/create", json=game_data, headers=headers
            ) as response:
                end_time = time.time()
                duration = (end_time - start_time) * 1000

                if response.status == 200:
                    game_response = await response.json()
                    return {
                        "success": True,
                        "duration_ms": duration,
                        "game_id": game_response.get("id"),
                    }
                else:
                    return {
                        "success": False,
                        "duration_ms": duration,
                        "error": f"HTTP {response.status}",
                    }
        except Exception as e:
            end_time = time.time()
            duration = (end_time - start_time) * 1000
            return {"success": False, "duration_ms": duration, "error": str(e)}

    async def test_leaderboard(self, game_id: str) -> dict[str, Any]:
        """Test leaderboard retrieval"""
        start_time = time.time()

        if not self.session:
            return {
                "success": False,
                "duration_ms": 0,
                "error": "Session not initialized",
            }

        try:
            async with self.session.get(
                f"{self.base_url}/api/game/leaderboard/{game_id}"
            ) as response:
                end_time = time.time()
                duration = (end_time - start_time) * 1000

                if response.status == 200:
                    return {"success": True, "duration_ms": duration}
                else:
                    return {
                        "success": False,
                        "duration_ms": duration,
                        "error": f"HTTP {response.status}",
                    }
        except Exception as e:
            end_time = time.time()
            duration = (end_time - start_time) * 1000
            return {"success": False, "duration_ms": duration, "error": str(e)}

    async def run_performance_test(self, iterations: int = 10) -> dict[str, Any]:
        """Run complete performance test suite"""
        print(f"Running performance test with {iterations} iterations...")

        for i in range(iterations):
            print(f"Iteration {i + 1}/{iterations}")

            # Test authentication
            auth_result = await self.test_authentication()
            self.results["authentication"].append(auth_result)

            if not auth_result["success"]:
                print(f"Authentication failed: {auth_result['error']}")
                continue

            # Test game creation
            game_result = await self.test_game_creation(auth_result["token"])
            self.results["game_creation"].append(game_result)

            if not game_result["success"]:
                print(f"Game creation failed: {game_result['error']}")
                continue

            # Test leaderboard
            leaderboard_result = await self.test_leaderboard(game_result["game_id"])
            self.results["leaderboard"].append(leaderboard_result)

            # Add delays to simulate real usage
            await asyncio.sleep(0.1)

        return self.analyze_results()

    def analyze_results(self) -> dict[str, Any]:
        """Analyze test results and generate statistics"""
        analysis = {}

        for test_name, results in self.results.items():
            successful_results = [r for r in results if r["success"]]

            if successful_results:
                durations = [r["duration_ms"] for r in successful_results]
                analysis[test_name] = {
                    "total_tests": len(results),
                    "successful_tests": len(successful_results),
                    "success_rate": len(successful_results) / len(results) * 100,
                    "min_duration_ms": min(durations),
                    "max_duration_ms": max(durations),
                    "avg_duration_ms": statistics.mean(durations),
                    "median_duration_ms": statistics.median(durations),
                    "std_deviation_ms": statistics.stdev(durations)
                    if len(durations) > 1
                    else 0,
                }
            else:
                analysis[test_name] = {
                    "total_tests": len(results),
                    "successful_tests": 0,
                    "success_rate": 0,
                    "error": "No successful tests",
                }

        return analysis


async def main():
    """Main function to run performance tests"""
    parser = argparse.ArgumentParser(
        description="Performance test script for InnoAlias game flow",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Prerequisites:
  # 1. Start the backend server: python -m uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
  # 2. Ensure MongoDB is running: sudo systemctl start mongodb
  # 3. Install dependencies: pip install aiohttp
  
  python docs/architecture/dynamic-view/performance-test.py                    # Test localhost:80 (requires nginx)
  python docs/architecture/dynamic-view/performance-test.py http://localhost:8000  # Test backend directly
  python docs/architecture/dynamic-view/performance-test.py --iterations 5    # Run 5 iterations
  python docs/architecture/dynamic-view/performance-test.py --help            # Show this help
        """,
    )

    parser.add_argument(
        "base_url",
        nargs="?",
        default="http://localhost",
        help="Base URL of the InnoAlias backend (default: http://localhost)",
    )

    parser.add_argument(
        "--iterations",
        "-i",
        type=int,
        default=10,
        help="Number of test iterations (default: 10)",
    )

    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose output"
    )

    args = parser.parse_args()

    print(f"Testing InnoAlias performance at: {args.base_url}")
    print("=" * 50)

    async with InnoAliasPerformanceTest(args.base_url) as tester:
        results = await tester.run_performance_test(iterations=args.iterations)

        print("\nPerformance Test Results:")
        print("=" * 50)

        for test_name, stats in results.items():
            print(f"\n{test_name.upper()}:")
            print(f"  Total Tests: {stats['total_tests']}")
            print(f"  Successful: {stats['successful_tests']}")
            print(f"  Success Rate: {stats['success_rate']:.1f}%")

            if "error" not in stats:
                print(f"  Min Duration: {stats['min_duration_ms']:.2f}ms")
                print(f"  Max Duration: {stats['max_duration_ms']:.2f}ms")
                print(f"  Avg Duration: {stats['avg_duration_ms']:.2f}ms")
                print(f"  Median Duration: {stats['median_duration_ms']:.2f}ms")
                print(f"  Std Deviation: {stats['std_deviation_ms']:.2f}ms")
            else:
                print(f"  Error: {stats['error']}")

        # Calculate total scenario time
        total_avg = 0
        for test_name, stats in results.items():
            if "error" not in stats:
                total_avg += stats["avg_duration_ms"]

        print(f"\nTOTAL SCENARIO TIME (Average): {total_avg:.2f}ms")


if __name__ == "__main__":
    asyncio.run(main())
