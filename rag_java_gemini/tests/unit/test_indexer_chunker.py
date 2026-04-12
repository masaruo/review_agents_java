from java_qa_agent.indexer import Chunker

JAVA_CODE = """
package com.example;

import java.util.*;

public class MyService {
    private String name;
    
    public MyService(String name) {
        this.name = name;
    }
    
    public void sayHello() {
        System.out.println("Hello " + name);
    }
}
"""


def test_chunker_small_file():
    # Small file should be one chunk
    chunker = Chunker(threshold=1000)
    chunks = chunker.chunk("Main.java", "public class Main {}")
    assert len(chunks) == 1
    assert chunks[0].metadata.chunk_type == "full_file"
    assert chunks[0].content == "public class Main {}"


def test_chunker_method_split():
    # Large file threshold low to force split
    chunker = Chunker(threshold=10)  # Force split
    chunks = chunker.chunk("MyService.java", JAVA_CODE)

    assert len(chunks) >= 2
    # Check if metadata is populated
    for chunk in chunks:
        assert chunk.metadata.file_path == "MyService.java"
        assert "import java.util.*;" in chunk.metadata.imports
        assert "public class MyService" in chunk.metadata.class_signature
        assert "private String name;" in chunk.metadata.member_variables


def test_chunker_extract_context():
    chunker = Chunker()
    imports, sig, members = chunker._extract_context(JAVA_CODE)
    assert "import java.util.*;" in imports
    assert "public class MyService" in sig
    assert "private String name;" in members
