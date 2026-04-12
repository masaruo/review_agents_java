from java_qa_agent.indexer import Chunker
from java_qa_agent.schemas.models import JavaChunkMetadata

def test_chunker_recursive_split():
    # Large content with no methods, should be split by characters
    large_content = "X" * 15000
    chunker = Chunker(threshold=1000, max_chars=6000)
    chunks = chunker.chunk("Large.java", large_content)
    
    # Expected: ceil(15000 / 6000) = 3 chunks
    assert len(chunks) == 3
    for chunk in chunks:
        assert len(chunk.content) <= 6000
        assert chunk.metadata.chunk_type == "full_file_split"

def test_chunker_method_split_with_large_method():
    # One method header, and a very large body
    method_sig = "public void largeMethod() {"
    large_body = "System.out.println(\"test\");\n" * 500
    large_content = f"public class Test {{\n{method_sig}\n{large_body}\n}}"
    
    chunker = Chunker(threshold=10, max_chars=2000)
    chunks = chunker.chunk("Test.java", large_content)
    
    # Should split header and then the large method
    assert len(chunks) > 1
    # Check if some chunks are of type "method_split" or "header"
    has_method_split = any("split" in c.metadata.chunk_type for c in chunks)
    assert has_method_split
