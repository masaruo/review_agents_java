from datetime import datetime
from pathlib import Path


class SessionLogger:
    def __init__(self, log_dir: str, project_name: str, enabled: bool = True):
        self.log_path = Path(log_dir).expanduser() / project_name
        self.enabled = enabled
        if self.enabled:
            self.log_path.mkdir(parents=True, exist_ok=True)
            self.current_session_file = (
                self.log_path
                / f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            )

    def log_interaction(self, user_msg: str, assistant_msg: str) -> None:
        if not self.enabled:
            return

        with open(self.current_session_file, "a") as f:
            f.write(f"[{datetime.now().isoformat()}] USER: {user_msg}\n")
            f.write(f"[{datetime.now().isoformat()}] ASSISTANT: {assistant_msg}\n")
            f.write("-" * 40 + "\n")
