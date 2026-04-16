import pytest
from src.java_review_agent.main import parse_args

def test_parse_args_basic():
    args = parse_args(["my_project"])
    assert args.dir == "my_project"
    assert args.config == "config.yaml"
    assert args.files is None
    assert args.instruction is None

def test_parse_args_full():
    args = parse_args([
        "my_project", 
        "--config", "my_config.yaml", 
        "--files", "File1.java", "File2.java", 
        "--instruction", "Focus on boundary conditions"
    ])
    assert args.dir == "my_project"
    assert args.config == "my_config.yaml"
    assert args.files == ["File1.java", "File2.java"]
    assert args.instruction == "Focus on boundary conditions"
