import json

import pytest

from bfi.config import Settings


@pytest.fixture
def settings(tmp_path):
    character = tmp_path / "character.json"
    character.write_text(
        json.dumps(
            {
                "name": "Test Companion",
                "description": "Test character",
                "system_prompt": "A fixed test prompt.",
            }
        ),
        encoding="utf-8",
    )
    return Settings(data_dir=tmp_path / "data", character_file=character)
