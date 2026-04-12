"""共通テストフィクスチャ"""

from __future__ import annotations

from pathlib import Path

import pytest

from java_review_agent.schemas.models import CodeSlot, Config

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "sample_java"


@pytest.fixture
def fixtures_dir() -> Path:
    return FIXTURES_DIR


@pytest.fixture
def simple_class_path(fixtures_dir: Path) -> str:
    return str(fixtures_dir / "SimpleClass.java")


@pytest.fixture
def large_class_path(fixtures_dir: Path) -> str:
    return str(fixtures_dir / "LargeClass.java")


@pytest.fixture
def buggy_class_path(fixtures_dir: Path) -> str:
    return str(fixtures_dir / "BuggyClass.java")


@pytest.fixture
def security_vulnerable_path(fixtures_dir: Path) -> str:
    return str(fixtures_dir / "SecurityVulnerable.java")


@pytest.fixture
def empty_class_path(fixtures_dir: Path) -> str:
    return str(fixtures_dir / "EmptyClass.java")


@pytest.fixture
def default_config() -> Config:
    return Config()


@pytest.fixture
def sample_slot() -> CodeSlot:
    return CodeSlot(
        slot_id="/path/to/Foo.java::myMethod",
        file_path="/path/to/Foo.java",
        method_name="myMethod",
        content='public void myMethod() { System.out.println("hello"); }',
    )
