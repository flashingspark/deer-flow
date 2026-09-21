"""Reuse the existing skill storage without duplicating its schema or SQL."""

import importlib
import sys
import types
from pathlib import Path

_PACKAGE = "_deerflow_city_statistics"
if _PACKAGE not in sys.modules:
    package = types.ModuleType(_PACKAGE)
    package.__path__ = [str(Path(__file__).resolve().parent.parent / "skills/custom/china-city-statistics/scripts")]
    sys.modules[_PACKAGE] = package
models = importlib.import_module(f"{_PACKAGE}.models")
database = importlib.import_module(f"{_PACKAGE}.database")
