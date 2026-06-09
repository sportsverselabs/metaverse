"""pytest bootstrap.

Ensures the project root is on ``sys.path`` so tests can ``import core``, ``import
agents``, etc. regardless of how pytest is invoked. (pyproject also sets ``pythonpath``;
this is a belt-and-suspenders fallback for older pytest versions.)
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
