
import pytest

from java_qa_agent.project_manager import ProjectManager


@pytest.fixture
def temp_config_dir(tmp_path):
    return tmp_path / ".java_qa_agent"


@pytest.fixture
def project_manager(temp_config_dir):
    return ProjectManager(config_dir=temp_config_dir)


def test_register_project(project_manager):
    project_manager.register_project("test-proj", "/path/to/proj")
    project = project_manager.get_project("test-proj")
    assert project["path"] == "/path/to/proj"


def test_list_projects(project_manager):
    project_manager.register_project("p1", "/path/1")
    project_manager.register_project("p2", "/path/2")
    projects = project_manager.list_projects()
    assert "p1" in projects
    assert "p2" in projects
    assert projects["p1"]["path"] == "/path/1"


def test_delete_project(project_manager):
    project_manager.register_project("del-proj", "/path/del")
    project_manager.delete_project("del-proj")
    with pytest.raises(ValueError):
        project_manager.get_project("del-proj")


def test_get_non_existent_project(project_manager):
    with pytest.raises(ValueError):
        project_manager.get_project("no-proj")
