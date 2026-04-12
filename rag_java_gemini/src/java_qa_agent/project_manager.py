import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class ProjectManager:
    def __init__(self, config_dir: Path):
        self.config_dir = Path(config_dir).expanduser()
        self.projects_file = self.config_dir / "projects.json"
        self._ensure_config_dir()
        self.projects: Dict[str, Any] = self._load_projects()

    def _ensure_config_dir(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        if not self.projects_file.exists():
            with open(self.projects_file, "w") as f:
                json.dump({"projects": {}}, f)

    def _load_projects(self) -> Dict[str, Any]:
        with open(self.projects_file, "r") as f:
            data = json.load(f)
            return data.get("projects", {})

    def _save_projects(self) -> None:
        with open(self.projects_file, "w") as f:
            json.dump({"projects": self.projects}, f, indent=2)

    def register_project(self, name: str, path: str) -> None:
        self.projects[name] = {
            "path": str(Path(path).absolute()),
            "registered_at": datetime.now().isoformat(),
            "indexed_at": None,
        }
        self._save_projects()

    def list_projects(self) -> Dict[str, Any]:
        return self.projects

    def get_project(self, name: str) -> Dict[str, Any]:
        if name not in self.projects:
            raise ValueError(f"Project '{name}' not found.")
        return self.projects[name]

    def delete_project(self, name: str) -> None:
        if name in self.projects:
            del self.projects[name]
            self._save_projects()
        else:
            raise ValueError(f"Project '{name}' not found.")

    def update_indexed_at(self, name: str) -> None:
        if name in self.projects:
            self.projects[name]["indexed_at"] = datetime.now().isoformat()
            self._save_projects()
        else:
            raise ValueError(f"Project '{name}' not found.")
