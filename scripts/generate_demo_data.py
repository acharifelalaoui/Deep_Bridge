#!/usr/bin/env python3
"""Generate synthetic DEMO DICOM series – NOT MEDICAL DATA."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.utils.demo_data import generate_demo_series


def main() -> None:
    path = generate_demo_series()
    print(f"Generated DEMO series in {path}")
    print("DEMO DATA – NOT MEDICAL DATA")


if __name__ == "__main__":
    main()
