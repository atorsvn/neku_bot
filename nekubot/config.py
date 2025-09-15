"""Configuration helpers for Neku Bot."""

import json


def load_json(file_name: str):
    """Load a JSON file and return the parsed object."""
    with open(file_name, encoding="utf-8") as json_file:
        return json.load(json_file)


def save_json(file_name: str, object_name) -> None:
    """Serialize *object_name* as JSON to ``file_name``."""
    with open(file_name, "w", encoding="utf-8") as outfile:
        json.dump(object_name, outfile)
