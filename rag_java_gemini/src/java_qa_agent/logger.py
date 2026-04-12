import logging
import sys
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
            self._setup_standard_logging()

    def _setup_standard_logging(self):
        # Setup standard logging to file
        log_file = self.log_path / "system.log"
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                # We don't want to spam the CLI with logs, so we don't add StreamHandler here
            ],
        )

    def log_interaction(self, user_msg: str, assistant_msg: str) -> None:
        if not self.enabled:
            return

        with open(self.current_session_file, "a") as f:
            f.write(f"[{datetime.now().isoformat()}] USER: {user_msg}\n")
            f.write(f"[{datetime.now().isoformat()}] ASSISTANT: {assistant_msg}\n")
            f.write("-" * 40 + "\n")
