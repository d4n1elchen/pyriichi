"""Shared pytest fixtures and configuration."""

import random

import pytest


@pytest.fixture(autouse=True)
def _seed_random():
    """Seed the global ``random`` before each test for deterministic deals.

    The engine and player code both call into ``random.shuffle`` /
    ``random.choice`` / ``random.randint``, and several tests inherit state
    from ``RuleEngine.deal()`` without fully overriding it (e.g. dora
    indicators, wall order). Without a fixed seed the suite is order- and
    timing-dependent and produces intermittent failures. Seeding per-test
    with a fixed value makes the suite deterministic.
    """
    random.seed(0)
