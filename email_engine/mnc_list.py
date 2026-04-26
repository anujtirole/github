import json
from core.config import config


def load_mnc_list() -> list[dict]:
    if config.MNC_LIST_PATH.exists():
        return json.loads(config.MNC_LIST_PATH.read_text())
    return []
