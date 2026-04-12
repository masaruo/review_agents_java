from java_qa_agent.chat_session import ChatSession


def test_chat_session_add_message():
    session = ChatSession(max_history=2)
    session.add_message("user", "hi")
    session.add_message("assistant", "hello")
    session.add_message("user", "how are you?")

    history = session.get_history()
    assert len(history) == 2
    assert history[0].content == "hello"
    assert history[1].content == "how are you?"


def test_chat_session_clear():
    session = ChatSession()
    session.add_message("user", "hi")
    session.clear_history()
    assert len(session.get_history()) == 0
