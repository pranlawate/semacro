"""Shared test fixtures for semacro test suite."""
import os
import sys
import pytest
from pathlib import Path

# Add parent dir to path so we can import semacro
sys.path.insert(0, str(Path(__file__).parent.parent))

import semacro as sm


FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures_dir():
    """Path to test fixtures directory."""
    return FIXTURES_DIR


@pytest.fixture
def synthetic_index():
    """Build index from synthetic fixture files only."""
    index = {}
    for f in FIXTURES_DIR.glob("*.if"):
        for macro in sm.parse_file(str(f), str(f.relative_to(FIXTURES_DIR))):
            index[macro.name] = macro
    for f in FIXTURES_DIR.glob("*.spt"):
        for macro in sm.parse_file(str(f), str(f.relative_to(FIXTURES_DIR))):
            index[macro.name] = macro
    return index


@pytest.fixture
def real_index():
    """Build index from real policy (skip if selinux-policy-devel not installed)."""
    include_path = sm.detect_include_path()
    if not include_path:
        pytest.skip("selinux-policy-devel not installed")
    return sm.load_or_build_index(include_path)


@pytest.fixture
def myapp_te():
    """Path to sample myapp.te file."""
    return FIXTURES_DIR / "myapp.te"


@pytest.fixture
def tmp_output(tmp_path):
    """Temporary output directory."""
    return tmp_path
