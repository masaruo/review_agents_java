from pathlib import Path
from typing import Union

import yaml

from .schemas.models import Config


def load_config(config_path: Union[str, Path]) -> Config:
    config_path = Path(config_path).expanduser()
    if not config_path.exists():
        return Config()

    with open(config_path, "r") as f:
        data = yaml.safe_load(f) or {}

    return Config.model_validate(data)
