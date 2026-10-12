"""Fixtures shared by the tests."""

from pathlib import Path

import pytest
from build_instance import optional_flags
from helpers import Sandbox, build, make_sandbox


@pytest.fixture
def sandbox(tmp_path: Path) -> Sandbox:
    """An empty project folder with a bare remote, an isolated git config, and the fake gh."""
    return make_sandbox(tmp_path)


@pytest.fixture
def full_build(tmp_path: Path) -> Path:
    """A project built with every module turned on."""
    target = tmp_path / "full"
    result = build(target, "--with", *sorted(optional_flags()), "--purpose", "Tests everything")
    assert result.returncode == 0, result.stderr
    return target
