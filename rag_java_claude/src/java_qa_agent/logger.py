"""セッションログモジュール

セッションの会話ログをJSONL形式で保存する。
"""

from datetime import datetime
from pathlib import Path

from java_qa_agent.schemas.models import ConversationTurn


class SessionLogger:
    """セッションログをJSONLファイルに保存するクラス"""

    def __init__(
        self,
        project_name: str,
        log_base_dir: str = "~/.java_qa_agent/logs",
        save_logs: bool = True,
    ) -> None:
        """初期化

        Args:
            project_name: プロジェクト名（ログディレクトリのサブディレクトリ名）
            log_base_dir: ログ保存ディレクトリのベースパス
            save_logs: ログを保存するかどうか
        """
        self.project_name = project_name
        self.log_base_dir = Path(log_base_dir).expanduser()
        self.save_logs = save_logs
        self._log_file: Path | None = None

    def _get_log_file(self) -> Path:
        """ログファイルのパスを返す（初回呼び出し時に決定する）

        Returns:
            ログファイルのパス
        """
        if self._log_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_dir = self.log_base_dir / self.project_name
            log_dir.mkdir(parents=True, exist_ok=True)
            self._log_file = log_dir / f"{timestamp}.jsonl"
        return self._log_file

    def log_turn(self, turn: ConversationTurn) -> None:
        """会話ターンをJSONL形式でログに保存する

        Args:
            turn: 保存するConversationTurnインスタンス
        """
        if not self.save_logs:
            return

        log_file = self._get_log_file()
        json_line = turn.model_dump_json()

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json_line + "\n")
