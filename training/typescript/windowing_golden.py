from __future__ import annotations

from dataset import build_window_ranges


def check(
    name: str,
    actual: list[tuple[int, int]],
    expected: list[tuple[int, int]],
) -> None:
    if actual != expected:
        raise AssertionError(f"{name}: {actual!r} != {expected!r}")
    print(f"✓ {name}")


def main() -> None:
    check(
        "short document uses one window",
        build_window_ranges(4000, max_length=8192, stride=6144),
        [(0, 4000)],
    )
    check(
        "two windows overlap by 2048 bytes",
        build_window_ranges(14336, max_length=8192, stride=6144),
        [(0, 8192), (6144, 14336)],
    )
    check(
        "long document keeps overlap and pins final window to tail",
        build_window_ranges(20000, max_length=8192, stride=6144),
        [(0, 8192), (6144, 14336), (11808, 20000)],
    )
    print("3/3 sliding-window golden checks passed")


if __name__ == "__main__":
    main()
