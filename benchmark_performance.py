#!/usr/bin/env python3
"""
性能基準測試腳本

測試和牌判定、聽牌判定等關鍵功能的性能。
"""

import time
import statistics
from pyriichi import Hand, parse_tiles, Tile, Suit


def benchmark_winning_hand_detection():
    """測試和牌判定性能"""
    print("=" * 60)
    print("和牌判定性能測試")
    print("=" * 60)

    # 測試用例：標準和牌型
    test_cases = [
        ("標準和牌型", "1m2m3m4p5p6p7s8s9s1z2z3z4z", Tile(Suit.MANZU, 1)),
        ("七對子", "1m1m2m2m3m3m4m4m5m5m6m6m7m7m", Tile(Suit.MANZU, 1)),
        ("國士無雙", "1m9m1p9p1s9s1z2z3z4z5z6z7z", Tile(Suit.MANZU, 1)),
        ("複雜和牌型", "1m2m3m4m5m6m7m8m9m1p2p3p4p", Tile(Suit.PINZU, 5)),
    ]

    results = []
    for name, tiles_str, winning_tile in test_cases:
        tiles = parse_tiles(tiles_str)
        hand = Hand(tiles)

        # 熱身
        for _ in range(10):
            hand.is_winning_hand(winning_tile)

        # 實際測試
        times = []
        for _ in range(1000):
            start = time.perf_counter()
            hand.is_winning_hand(winning_tile)
            end = time.perf_counter()
            times.append((end - start) * 1000)  # 轉換為毫秒

        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)

        results.append({"name": name, "avg": avg_time, "median": median_time, "min": min_time, "max": max_time})

        print(f"\n{name}:")
        print(f"  平均: {avg_time:.4f} ms")
        print(f"  中位數: {median_time:.4f} ms")
        print(f"  最小: {min_time:.4f} ms")
        print(f"  最大: {max_time:.4f} ms")

    return results


def benchmark_tenpai_detection():
    """測試聽牌判定性能"""
    print("\n" + "=" * 60)
    print("聽牌判定性能測試")
    print("=" * 60)

    # 測試用例：各種聽牌情況
    test_cases = [
        ("標準聽牌", "1m2m3m4p5p6p7s8s9s1z2z3z4z"),
        ("多面聽", "1m2m3m4m5m6m7m8m9m1p2p3p4p"),
        ("單騎聽", "1m2m3m4p5p6p7s8s9s1z2z3z4z"),
        ("複雜聽牌", "1m1m2m2m3m3m4m4m5m5m6m6m7m"),
    ]

    results = []
    for name, tiles_str in test_cases:
        tiles = parse_tiles(tiles_str)
        hand = Hand(tiles)

        # 熱身
        for _ in range(10):
            hand.is_tenpai()

        # 實際測試
        times = []
        for _ in range(100):
            start = time.perf_counter()
            hand.is_tenpai()
            end = time.perf_counter()
            times.append((end - start) * 1000)  # 轉換為毫秒

        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)

        results.append({"name": name, "avg": avg_time, "median": median_time, "min": min_time, "max": max_time})

        print(f"\n{name}:")
        print(f"  平均: {avg_time:.4f} ms")
        print(f"  中位數: {median_time:.4f} ms")
        print(f"  最小: {min_time:.4f} ms")
        print(f"  最大: {max_time:.4f} ms")

    return results


def benchmark_waiting_tiles():
    """測試聽牌列表獲取性能"""
    print("\n" + "=" * 60)
    print("聽牌列表獲取性能測試")
    print("=" * 60)

    # 測試用例
    test_cases = [
        ("標準聽牌", "1m2m3m4p5p6p7s8s9s1z2z3z4z"),
        ("多面聽", "1m2m3m4m5m6m7m8m9m1p2p3p4p"),
    ]

    results = []
    for name, tiles_str in test_cases:
        tiles = parse_tiles(tiles_str)
        hand = Hand(tiles)

        # 熱身
        for _ in range(10):
            hand.get_waiting_tiles()

        # 實際測試
        times = []
        for _ in range(100):
            start = time.perf_counter()
            hand.get_waiting_tiles()
            end = time.perf_counter()
            times.append((end - start) * 1000)  # 轉換為毫秒

        avg_time = statistics.mean(times)
        median_time = statistics.median(times)
        min_time = min(times)
        max_time = max(times)

        results.append({"name": name, "avg": avg_time, "median": median_time, "min": min_time, "max": max_time})

        print(f"\n{name}:")
        print(f"  平均: {avg_time:.4f} ms")
        print(f"  中位數: {median_time:.4f} ms")
        print(f"  最小: {min_time:.4f} ms")
        print(f"  最大: {max_time:.4f} ms")

    return results


def benchmark_tile_counts_cache():
    """測試牌計數緩存效果"""
    print("\n" + "=" * 60)
    print("牌計數緩存效果測試")
    print("=" * 60)

    tiles = parse_tiles("1m2m3m4p5p6p7s8s9s1z2z3z4z")
    hand = Hand(tiles)

    # 第一次調用（無緩存）
    start = time.perf_counter()
    for _ in range(1000):
        hand._get_tile_counts()
    first_time = (time.perf_counter() - start) * 1000

    # 後續調用（有緩存）
    start = time.perf_counter()
    for _ in range(1000):
        hand._get_tile_counts()
    cached_time = (time.perf_counter() - start) * 1000

    print(f"\n無緩存 (1000次): {first_time:.4f} ms")
    print(f"有緩存 (1000次): {cached_time:.4f} ms")
    print(f"加速比: {first_time / cached_time:.2f}x")

    return first_time, cached_time


if __name__ == "__main__":
    print("PyRiichi 性能基準測試")
    print("=" * 60)

    # 運行所有測試
    winning_results = benchmark_winning_hand_detection()
    tenpai_results = benchmark_tenpai_detection()
    waiting_results = benchmark_waiting_tiles()
    cache_results = benchmark_tile_counts_cache()

    print("\n" + "=" * 60)
    print("測試完成！")
    print("=" * 60)
