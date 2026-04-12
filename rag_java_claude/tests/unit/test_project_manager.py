"""ProjectManagerのユニットテスト"""

from pathlib import Path

import pytest

from java_qa_agent.project_manager import ProjectManager, ProjectNotFoundError


class TestProjectManager:
    def test_register_new_project(self, tmp_path: Path) -> None:
        """新規プロジェクトが正しく登録されることを確認する"""
        manager = ProjectManager(base_dir=str(tmp_path))
        info = manager.register("my-project", "/path/to/project")

        assert info.name == "my-project"
        assert info.path == "/path/to/project"

        # projects.jsonが作成されていることを確認
        registry_file = tmp_path / "projects.json"
        assert registry_file.exists()

    def test_register_updates_existing_project(self, tmp_path: Path) -> None:
        """既存プロジェクト名で登録するとupdated_atが更新されることを確認する"""
        manager = ProjectManager(base_dir=str(tmp_path))
        info1 = manager.register("my-project", "/path/to/project")
        info2 = manager.register("my-project", "/new/path/to/project")

        assert info2.path == "/new/path/to/project"
        # updated_atが更新されていることを確認（作成時間以降であること）
        assert info2.updated_at >= info1.created_at

    def test_get_registered_project(self, tmp_path: Path) -> None:
        """登録済みプロジェクトを取得できることを確認する"""
        manager = ProjectManager(base_dir=str(tmp_path))
        manager.register("my-project", "/path/to/project")

        info = manager.get("my-project")
        assert info.name == "my-project"
        assert info.path == "/path/to/project"

    def test_get_unknown_project_raises_error(self, tmp_path: Path) -> None:
        """未登録プロジェクトでProjectNotFoundErrorを発生させることを確認する"""
        manager = ProjectManager(base_dir=str(tmp_path))

        with pytest.raises(ProjectNotFoundError):
            manager.get("unknown-project")

    def test_get_unknown_project_error_includes_list(self, tmp_path: Path) -> None:
        """エラーメッセージに登録済みリストが含まれることを確認する"""
        manager = ProjectManager(base_dir=str(tmp_path))
        manager.register("project-a", "/path/a")
        manager.register("project-b", "/path/b")

        with pytest.raises(ProjectNotFoundError) as exc_info:
            manager.get("unknown-project")

        error_message = str(exc_info.value)
        assert "project-a" in error_message
        assert "project-b" in error_message

    def test_delete_project_removes_from_registry(self, tmp_path: Path) -> None:
        """削除後にレジストリから除外されることを確認する"""
        manager = ProjectManager(base_dir=str(tmp_path))
        manager.register("my-project", "/path/to/project")
        manager.delete("my-project")

        with pytest.raises(ProjectNotFoundError):
            manager.get("my-project")

    def test_delete_project_removes_index_directory(self, tmp_path: Path) -> None:
        """削除後にインデックスディレクトリが削除されることを確認する"""
        manager = ProjectManager(base_dir=str(tmp_path))
        manager.register("my-project", "/path/to/project")

        # インデックスディレクトリを作成
        index_dir = tmp_path / "indexes" / "my-project"
        index_dir.mkdir(parents=True)
        (index_dir / "chroma.sqlite3").write_text("dummy")

        manager.delete("my-project")

        assert not index_dir.exists()

    def test_delete_unknown_project_raises_error(self, tmp_path: Path) -> None:
        """未登録プロジェクトでProjectNotFoundErrorを発生させることを確認する"""
        manager = ProjectManager(base_dir=str(tmp_path))

        with pytest.raises(ProjectNotFoundError):
            manager.delete("unknown-project")

    def test_list_projects_returns_all(self, tmp_path: Path) -> None:
        """全プロジェクトのリストを返すことを確認する"""
        manager = ProjectManager(base_dir=str(tmp_path))
        manager.register("project-a", "/path/a")
        manager.register("project-b", "/path/b")
        manager.register("project-c", "/path/c")

        projects = manager.list_projects()
        assert len(projects) == 3
        names = [p.name for p in projects]
        assert "project-a" in names
        assert "project-b" in names
        assert "project-c" in names

    def test_list_projects_empty(self, tmp_path: Path) -> None:
        """プロジェクトなしで空リストを返すことを確認する"""
        manager = ProjectManager(base_dir=str(tmp_path))
        projects = manager.list_projects()
        assert projects == []

    def test_registry_persisted_across_instances(self, tmp_path: Path) -> None:
        """レジストリがファイルに永続化されることを確認する"""
        # 最初のインスタンスでプロジェクトを登録
        manager1 = ProjectManager(base_dir=str(tmp_path))
        manager1.register("my-project", "/path/to/project")

        # 新しいインスタンスで取得できることを確認
        manager2 = ProjectManager(base_dir=str(tmp_path))
        info = manager2.get("my-project")
        assert info.name == "my-project"
        assert info.path == "/path/to/project"

    def test_no_registry_file_returns_empty(self, tmp_path: Path) -> None:
        """projects.jsonが存在しない場合に空のレジストリとして扱うことを確認する"""
        manager = ProjectManager(base_dir=str(tmp_path))
        projects = manager.list_projects()
        assert projects == []
