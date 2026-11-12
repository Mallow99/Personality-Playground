"""The desktop calls the application in process, including error handling."""

import asyncio
import json

import pytest

from bfi.config import Settings
from bfi.desktop import DesktopApp
from bfi.main import create_app


def test_desktop_request_creates_and_reopens_conversation(tmp_path):
    character = tmp_path / "character.json"
    character.write_text(
        json.dumps({"name": "Test", "description": "Test", "system_prompt": "Be helpful."}),
        encoding="utf-8",
    )
    desktop = DesktopApp.__new__(DesktopApp)
    desktop.app = create_app(Settings(data_dir=tmp_path / "data", character_file=character))

    async def scenario():
        conversation = await desktop.request("POST", "/conversations")
        path = f"/conversations/{conversation['id']}"
        result = await desktop.request("POST", path + "/messages", json={"content": "Hello"})
        assert "no model inference" in result["messages"][-1]["content"]
        assert await desktop.request("GET", path) == result
        with pytest.raises(RuntimeError, match="Conversation not found"):
            await desktop.request("GET", "/conversations/missing")

    asyncio.run(scenario())
