# This project is licensed under the terms of the GNU GPL v3: https://www.gnu.org/licenses/
import os
import sys
import unittest

SRC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


def require(*env_vars: str) -> dict:
    """Values of the given environment variables. Skips the test if one is missing, unless
    JRP_REQUIRE_ALL is set (as in CI), in which case the test fails instead."""
    missing = [v for v in env_vars if not os.environ.get(v)]
    if missing:
        msg = f"needs environment variables {', '.join(missing)}"
        if os.environ.get("JRP_REQUIRE_ALL"):
            raise AssertionError(msg)
        raise unittest.SkipTest(msg)
    return {v: os.environ[v] for v in env_vars}
