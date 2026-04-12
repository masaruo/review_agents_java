import pytest
from src.java_review_agent.agents.preprocessor import Preprocessor

def test_preprocess_small_file():
    code = """
    package com.example;
    import java.util.List;
    public class App {
        public void hello() {
            System.out.println("Hello");
        }
    }
    """
    preprocessor = Preprocessor(chunk_threshold=1000)
    slots = preprocessor.preprocess(code)
    
    assert len(slots) == 1
    assert slots[0]["slot_id"] == "full_file"
    assert "public void hello()" in slots[0]["content"]

def test_preprocess_large_file_chunking():
    # 意図的に閾値を下げてチャンキングをテスト
    code = """
    package com.example;
    import java.util.List;
    public class App {
        private String name;
        public void method1() {
            // content 1
        }
        public void method2() {
            // content 2
        }
    }
    """
    preprocessor = Preprocessor(chunk_threshold=10) # 非常に小さい閾値
    slots = preprocessor.preprocess(code)
    
    assert len(slots) >= 2
    # 各スロットにクラス情報やインポートが含まれているか
    for slot in slots:
        assert "package com.example;" in slot["context"]
        assert "import java.util.List;" in slot["context"]
        assert "public class App" in slot["context"]
        assert "private String name;" in slot["context"]
