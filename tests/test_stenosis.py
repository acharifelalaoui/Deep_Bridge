"""NASCET / ECST calculation tests."""

from __future__ import annotations

import pytest

from app.carotid.stenosis import compute_ecst, compute_nascet


def test_nascet_basic():
    # Ds=2, Dref=5 => 60%
    r = compute_nascet(2.0, 5.0)
    assert r.percentage == pytest.approx(60.0)
    assert "NASCET" in r.display()
    assert "60.0%" in r.display()


def test_nascet_zero_stenosis():
    r = compute_nascet(5.0, 5.0)
    assert r.percentage == pytest.approx(0.0)


def test_nascet_invalid():
    with pytest.raises(ValueError):
        compute_nascet(1.0, 0.0)
    with pytest.raises(ValueError):
        compute_nascet(-1.0, 5.0)


def test_ecst_basic():
    r = compute_ecst(2.0, 8.0)
    assert r.percentage == pytest.approx(75.0)
    assert r.method.value == "ECST"
