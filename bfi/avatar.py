"""Presentation-only avatar state and bounded tools shared by chat and overlays."""

import json
import threading
import time

from bfi.config import ROOT
from bfi.tools import ToolError, definition

CATALOG = ROOT / "bfi/static/avatar/catalog.json"
DOCKS = ("bottom-right", "bottom-left", "top-right", "top-left")
SIZES = ("small", "normal", "large")
CONTRASTS = ("auto", "light", "dark")


class AvatarHub:
    def __init__(self):
        self.catalog = json.loads(CATALOG.read_text())
        self.poses = {p["id"]: p for p in self.catalog["poses"]}
        self.lock = threading.RLock()
        self.state = dict(
            revision=0,
            profile="academic",
            pose_id="academic/standing",
            visible=True,
            dock="bottom-right",
            size="normal",
            activity="idle",
            caption="",
            speaking=False,
            speech_until=0,
            motion=True,
            contrast="auto",
            source="owner",
            conversation_id=None,
        )

    def snapshot(self):
        with self.lock:
            if self.state["speaking"] and time.time() >= self.state["speech_until"]:
                self.state.update(
                    speaking=False, activity="idle", revision=self.state["revision"] + 1
                )
            return dict(self.state)

    def update(self, changes, *, profile=None, source="owner"):
        with self.lock:
            if not isinstance(changes, dict) or not changes:
                raise ToolError("Provide at least one avatar field.")
            if set(changes) - {
                "profile",
                "pose_id",
                "visible",
                "dock",
                "size",
                "caption",
                "speaking",
                "motion",
                "contrast",
            }:
                raise ToolError("Unknown avatar field.")
            role = changes.get("profile", self.state["profile"])
            if profile is not None:
                role = profile
                if changes.get("profile", role) != profile:
                    raise ToolError("This handler may control only its own character.")
            if not isinstance(role, str) or role not in self.catalog["roles"]:
                raise ToolError("Unknown avatar profile.")
            pose_id = changes.get(
                "pose_id",
                self.state["pose_id"] if role == self.state["profile"] else f"{role}/standing",
            )
            if (
                not isinstance(pose_id, str)
                or pose_id not in self.poses
                or self.poses[pose_id]["role"] != role
            ):
                raise ToolError("Choose a catalog pose belonging to this character.")
            for key in ("visible", "speaking", "motion"):
                if key in changes and type(changes[key]) is not bool:
                    raise ToolError(f"{key} must be boolean.")
            if "caption" in changes and (
                not isinstance(changes["caption"], str) or len(changes["caption"]) > 400
            ):
                raise ToolError("Avatar captions may contain up to 400 text characters.")
            if changes.get("dock", self.state["dock"]) not in DOCKS:
                raise ToolError("Unknown avatar dock.")
            if changes.get("size", self.state["size"]) not in SIZES:
                raise ToolError("Unknown avatar size.")
            if changes.get("contrast", self.state["contrast"]) not in CONTRASTS:
                raise ToolError("Choose auto, light or dark artwork contrast.")
            if role != self.state["profile"]:
                self.state.update(
                    caption="",
                    speaking=False,
                    speech_until=0,
                    activity="idle",
                    conversation_id=None,
                )
            self.state.update(
                changes,
                profile=role,
                pose_id=pose_id,
                source=source,
                revision=self.state["revision"] + 1,
            )
            if "speaking" in changes:
                self.state["speech_until"] = time.time() + 15 if changes["speaking"] else 0
                self.state["activity"] = "speaking" if changes["speaking"] else "idle"
            return self.snapshot()

    def begin(self, profile, cid):
        role = profile if profile in self.catalog["roles"] else "academic"
        self.update(
            {"profile": role, "pose_id": f"{role}/thinking", "speaking": False}, source="lifecycle"
        )
        with self.lock:
            self.state.update(activity="thinking", caption="Thinking…", conversation_id=cid)
        return self.snapshot()

    def finish(self, content=None):
        with self.lock:
            role = self.state["profile"]
            if content is None:
                self.update(
                    {
                        "pose_id": f"{role}/concerned",
                        "speaking": False,
                        "caption": "Reply unavailable. Check the handler.",
                    },
                    source="lifecycle",
                )
                self.state["activity"] = "error"
            else:
                if self.state["pose_id"] == f"{role}/thinking":
                    self.state["pose_id"] = f"{role}/standing"
                self.state.update(
                    caption=content[:400],
                    speaking=True,
                    activity="speaking",
                    speech_until=time.time() + min(25, max(4, len(content.split()) / 3)),
                    revision=self.state["revision"] + 1,
                )
        return self.snapshot()

    def search(self, role, query="", limit=8):
        if (
            not isinstance(query, str)
            or len(query) > 150
            or type(limit) is not int
            or not 1 <= limit <= 20
        ):
            raise ToolError("Use a query up to 150 characters and limit 1–20.")
        words = query.lower().split()
        rows = [p for p in self.catalog["poses"] if p["role"] == role]
        if words:
            scored = [
                (
                    sum(
                        w
                        in (p["label"] + " " + p["description"] + " " + " ".join(p["tags"])).lower()
                        for w in words
                    ),
                    p,
                )
                for p in rows
            ]
            rows = [p for score, p in sorted(scored, key=lambda item: -item[0]) if score]
        return {
            "poses": [
                {
                    **{k: p[k] for k in ("id", "label", "description", "source", "motion")},
                    "approval": p.get("approval", "existing"),
                }
                for p in rows[:limit]
            ],
            "total_for_character": len([p for p in self.poses.values() if p["role"] == role]),
        }


class AvatarTools:
    """A request-scoped wrapper: never shares another conversation's character authority."""

    def __init__(self, base, hub, profile):
        self.base, self.hub, self.profile = base, hub, profile

    @staticmethod
    def definitions():
        return [
            definition(
                "avatar_catalog",
                "Find suitable visual poses for your own character. "
                "These are presentation controls, not computer actions.",
                {
                    "query": {"type": "string", "maxLength": 150},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 20},
                },
            ),
            definition(
                "avatar_set",
                "Choose your character pose, visibility, corner, size or short "
                "text caption. Use catalog IDs. Never claim this changes a model "
                "or performs a task.",
                {
                    "pose_id": {"type": "string"},
                    "visible": {"type": "boolean"},
                    "dock": {"type": "string", "enum": list(DOCKS)},
                    "size": {"type": "string", "enum": list(SIZES)},
                    "caption": {"type": "string", "maxLength": 400},
                    "speaking": {"type": "boolean"},
                },
            ),
        ]

    async def run(self, name, arguments, allowed_names):
        if name not in allowed_names:
            raise ToolError("This tool was not enabled for this request.")
        if name == "avatar_catalog":
            if not isinstance(arguments, dict) or set(arguments) - {"query", "limit"}:
                raise ToolError("Unexpected avatar catalog arguments.")
            return self.hub.search(self.profile, **arguments)
        if name == "avatar_set":
            if not isinstance(arguments, dict) or set(arguments) & {
                "profile",
                "motion",
                "contrast",
            }:
                raise ToolError("The handler cannot change profile or owner display preferences.")
            return self.hub.update(arguments, profile=self.profile, source="model_tool")
        return await self.base.run(name, arguments, allowed_names)

    serialize = staticmethod(json.dumps)
