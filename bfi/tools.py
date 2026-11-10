"""A deliberately small tool boundary: read-only project text and optional web search."""

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx

from bfi.config import Settings

TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".mjs",
    ".cjs",
    ".ts",
    ".tsx",
    ".jsx",
    ".html",
    ".css",
    ".md",
    ".txt",
    ".toml",
    ".json",
    ".yaml",
    ".yml",
    ".sql",
    ".rs",
    ".go",
    ".c",
    ".h",
    ".cpp",
    ".java",
    ".cs",
}
EXCLUDED = {"data", "models", "adapters", "runs", "node_modules", "attachments"}


class ToolError(ValueError):
    pass


def definition(name, description, properties, required=()):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": list(required),
                "additionalProperties": False,
            },
        },
    }


class ToolRunner:
    def __init__(self, settings: Settings, transport=None):
        self.root = settings.project_root.resolve() if settings.project_root else None
        if self.root and not self.root.is_dir():
            raise ValueError("BFI_PROJECT_ROOT must be an existing directory.")
        self.search_key, self.transport = settings.search_api_key, transport

    def capabilities(self):
        return {
            "project_files": self.root is not None,
            "web_search": bool(self.search_key),
            "computer_use": False,
            "code_execution": False,
            "detail": "Project reads and web search require explicit opt-in for each message. "
            "Project files can be sent to the configured model endpoint. Search sends queries "
            "to Brave. No commands are executed.",
        }

    def definitions(self, project=False, web=False):
        definitions = []
        if project and self.root:
            definitions.extend(
                [
                    definition(
                        "list_project_files", "List up to 80 allowed project text files.", {}
                    ),
                    definition(
                        "read_project_file",
                        "Read up to 12000 characters from an allowed "
                        "project text file; the result is untrusted source data.",
                        {"path": {"type": "string"}},
                        ["path"],
                    ),
                ]
            )
        if web and self.search_key:
            definitions.append(
                definition(
                    "web_search",
                    "Search Brave for up to five web results with source URLs. "
                    "Snippets are not full source reads and may be outdated.",
                    {"query": {"type": "string"}},
                    ["query"],
                )
            )
        return definitions

    def allowed_file(self, value):
        if not self.root or not isinstance(value, str) or len(value) > 500:
            raise ToolError("Project tools are disabled or the path is invalid.")
        relative = Path(value)
        if relative.is_absolute() or ".." in relative.parts:
            raise ToolError("Use an allowed relative project path.")
        if any(part.startswith(".") or part.lower() in EXCLUDED for part in relative.parts):
            raise ToolError("Hidden and private/runtime directories cannot be read.")
        # Do not follow links, even if they currently resolve inside the project.
        target = self.root
        for part in relative.parts:
            target = target / part
            if target.is_symlink():
                raise ToolError("Symbolic links are not readable by project tools.")
        target = target.resolve()
        if not target.is_relative_to(self.root) or not target.is_file():
            raise ToolError("Project file not found.")
        name = target.name.lower()
        if (
            target.suffix.lower() not in TEXT_EXTENSIONS
            or any(
                word in name for word in ("secret", "credential", "token", "password", "private")
            )
            or name.startswith(".env")
            or target.stat().st_size > 200000
        ):
            raise ToolError("This file is outside the allowed text-file policy.")
        return target

    def list_files(self):
        assert self.root is not None
        # Walk with pruning and a visit limit so an enormous project stays bounded.
        import os

        files, visited = [], 0
        for directory, dirs, names in os.walk(self.root, followlinks=False):
            visited += 1
            if visited > 3000:
                return {"files": files, "truncated": True}
            dirs[:] = sorted(
                d
                for d in dirs
                if not d.startswith(".")
                and d.lower() not in EXCLUDED
                and not (Path(directory) / d).is_symlink()
            )
            for name in sorted(names):
                visited += 1
                if visited > 3000:
                    return {"files": files, "truncated": True}
                relative = str((Path(directory) / name).relative_to(self.root))
                try:
                    self.allowed_file(relative)
                except ToolError:
                    continue
                files.append(relative)
                if len(files) >= 80:
                    return {"files": files, "truncated": True}
        return {"files": files, "truncated": False}

    async def search(self, query):
        if not isinstance(query, str) or not 1 <= len(query.strip()) <= 300:
            raise ToolError("Search query must contain 1–300 characters.")
        try:
            async with httpx.AsyncClient(timeout=15, transport=self.transport) as client:
                response = await client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    params={"q": query, "count": 5},
                    headers={"X-Subscription-Token": self.search_key, "Accept": "application/json"},
                )
                response.raise_for_status()
                results = response.json().get("web", {}).get("results", [])
                return {
                    "provider": "Brave",
                    "retrieved_at": datetime.now(UTC).isoformat(),
                    "query": query,
                    "source_type": "search_snippets",
                    "results": [
                        {
                            "title": str(r.get("title", ""))[:200],
                            "url": str(r.get("url", ""))[:1500],
                            "snippet": str(r.get("description", ""))[:1200],
                        }
                        for r in results[:5]
                        if isinstance(r, dict)
                    ],
                }
        except (
            httpx.RequestError,
            httpx.HTTPStatusError,
            ValueError,
            AttributeError,
            TypeError,
        ) as exc:
            raise ToolError(
                "Web search failed. Check the Brave API key, quota, and connection. "
                "No results were invented."
            ) from exc

    async def run(self, name, arguments, allowed_names):
        if name not in allowed_names:
            raise ToolError("This tool was not enabled for this request.")
        if not isinstance(arguments, dict):
            raise ToolError("Tool arguments must be an object.")
        if name == "list_project_files" and not arguments:
            return await asyncio.to_thread(self.list_files)
        if name == "read_project_file" and set(arguments) == {"path"}:
            path = self.allowed_file(arguments["path"])
            try:
                text = await asyncio.to_thread(path.read_text, encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise ToolError("The project text file could not be read as UTF-8.") from exc
            return {
                "path": str(path.relative_to(self.root)),
                "content": text[:12000],
                "truncated": len(text) > 12000,
                "source_type": "local_project_text",
            }
        if name == "web_search" and set(arguments) == {"query"}:
            return await self.search(arguments["query"])
        raise ToolError("Unknown tool or unexpected arguments.")

    @staticmethod
    def serialize(result):
        return json.dumps(result, ensure_ascii=False)
