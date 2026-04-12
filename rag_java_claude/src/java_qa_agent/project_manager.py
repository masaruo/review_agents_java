"""プロジェクト管理モジュール

プロジェクトの登録・取得・削除・一覧表示を管理する。
プロジェクトレジストリは ~/.java_qa_agent/projects.json に保存される。
"""

import shutil
from datetime import datetime
from pathlib import Path

from java_qa_agent.schemas.models import ProjectInfo, ProjectRegistry


class ProjectNotFoundError(Exception):
    """プロジェクトが見つからないエラー"""

    def __init__(self, project_name: str, registered_projects: list[str]) -> None:
        self.project_name = project_name
        self.registered_projects = registered_projects
        projects_str = ", ".join(registered_projects) if registered_projects else "（なし）"
        super().__init__(
            f"プロジェクト '{project_name}' は登録されていません。\n"
            f"登録済みプロジェクト: {projects_str}"
        )


class ProjectManager:
    """プロジェクトのCRUDを管理するクラス"""

    def __init__(self, base_dir: str = "~/.java_qa_agent") -> None:
        """初期化

        Args:
            base_dir: ベースディレクトリパス（デフォルト: ~/.java_qa_agent）
        """
        self.base_dir = Path(base_dir).expanduser()
        self.registry_file = self.base_dir / "projects.json"
        self.index_base_dir = self.base_dir / "indexes"

    def _load_registry(self) -> ProjectRegistry:
        """レジストリファイルを読み込む

        Returns:
            ProjectRegistryインスタンス

        Raises:
            IOError: ファイルの読み込みに失敗した場合（存在しない場合は除く）
        """
        if not self.registry_file.exists():
            return ProjectRegistry()

        try:
            content = self.registry_file.read_text(encoding="utf-8")
            return ProjectRegistry.model_validate_json(content)
        except (OSError, ValueError) as e:
            raise OSError(f"プロジェクトレジストリの読み込みに失敗しました: {e}") from e

    def _save_registry(self, registry: ProjectRegistry) -> None:
        """レジストリをファイルに保存する

        Args:
            registry: 保存するProjectRegistryインスタンス
        """
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.registry_file.write_text(
            registry.model_dump_json(indent=2),
            encoding="utf-8",
        )

    def register(self, name: str, path: str) -> ProjectInfo:
        """プロジェクトを登録する

        既存プロジェクト名の場合は updated_at を更新して上書きする。

        Args:
            name: プロジェクト名（一意の識別子）
            path: Javaプロジェクトのルートディレクトリパス

        Returns:
            登録されたProjectInfoインスタンス
        """
        registry = self._load_registry()

        if name in registry.projects:
            # 既存プロジェクトを更新
            existing = registry.projects[name]
            info = ProjectInfo(
                name=name,
                path=path,
                created_at=existing.created_at,
                updated_at=datetime.now(),
            )
        else:
            info = ProjectInfo(name=name, path=path)

        registry.projects[name] = info
        self._save_registry(registry)
        return info

    def get(self, name: str) -> ProjectInfo:
        """プロジェクト情報を取得する

        Args:
            name: プロジェクト名

        Returns:
            ProjectInfoインスタンス

        Raises:
            ProjectNotFoundError: プロジェクトが登録されていない場合
        """
        registry = self._load_registry()

        if name not in registry.projects:
            registered = list(registry.projects.keys())
            raise ProjectNotFoundError(name, registered)

        return registry.projects[name]

    def delete(self, name: str) -> None:
        """プロジェクトを削除する

        レジストリからプロジェクトを削除し、インデックスディレクトリも削除する。

        Args:
            name: プロジェクト名

        Raises:
            ProjectNotFoundError: プロジェクトが登録されていない場合
        """
        registry = self._load_registry()

        if name not in registry.projects:
            registered = list(registry.projects.keys())
            raise ProjectNotFoundError(name, registered)

        # レジストリから削除
        del registry.projects[name]
        self._save_registry(registry)

        # インデックスディレクトリを削除
        index_dir = self.index_base_dir / name
        if index_dir.exists():
            shutil.rmtree(str(index_dir))

    def list_projects(self) -> list[ProjectInfo]:
        """登録済みプロジェクトの一覧を返す

        Returns:
            ProjectInfoのリスト（空の場合は空リスト）
        """
        registry = self._load_registry()
        return list(registry.projects.values())
