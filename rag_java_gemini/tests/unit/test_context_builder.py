from java_qa_agent.context_builder import ContextBuilder
from java_qa_agent.schemas.models import ChatMessage, JavaChunk, JavaChunkMetadata


def test_context_builder_build_prompt():
    builder = ContextBuilder(java_version=17, max_tokens=3000)

    chunks = [
        JavaChunk(
            content="public void test() {}",
            metadata=JavaChunkMetadata(
                file_path="Test.java", class_signature="class Test"
            ),
        )
    ]
    history = [
        ChatMessage(role="user", content="hello"),
        ChatMessage(role="assistant", content="hi"),
    ]

    prompt = builder.build_prompt(chunks, history, "how to test?")

    assert "Java Version: 17" in prompt
    assert "Test.java" in prompt
    assert "public void test() {}" in prompt
    assert "user: hello" in prompt
    assert "assistant: hi" in prompt
    assert "how to test?" in prompt


def test_context_builder_token_limit():
    # Very small limit to force truncation
    builder = ContextBuilder(java_version=17, max_tokens=50)

    chunks = [
        JavaChunk(
            content="A very long piece of code " * 10,
            metadata=JavaChunkMetadata(file_path="Long.java"),
        )
    ]

    prompt = builder.build_prompt(chunks, [], "question")
    # Exact token count is hard, but prompt should be shorter than original content + metadata
    assert len(prompt.split()) < 100
