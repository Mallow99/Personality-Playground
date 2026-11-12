"""Versioned owner-editable personality scaffolds; these do not train model weights."""

import json
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from bfi.store import now

ShortText = Annotated[str, Field(min_length=1, max_length=100)]


class PersonalitySettings(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    display_name: str = Field(min_length=1, max_length=60)
    role: str = Field(min_length=1, max_length=500)
    tone: str = Field(min_length=1, max_length=500)
    traits: list[ShortText] = Field(default_factory=list, max_length=8)
    values: list[ShortText] = Field(default_factory=list, max_length=8)
    interests: str = Field(default="", max_length=500)
    relationship_style: str = Field(default="", max_length=500)
    speech_style: str = Field(default="", max_length=500)
    humor: Literal["none", "light", "playful"] = "light"
    initiative: Literal["gentle", "balanced", "proactive"] = "balanced"
    verbosity: Literal["concise", "balanced", "detailed"] = "balanced"
    boundaries: str = Field(default="", max_length=700)
    backstory: str = Field(default="", max_length=700)
    custom_instructions: str = Field(default="", max_length=1200)


class PersonalityChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_revision: int = Field(ge=1)
    settings: PersonalitySettings


class PersonalityRestore(BaseModel):
    model_config = ConfigDict(extra="forbid")
    revision: int = Field(ge=1)
    expected_revision: int = Field(ge=1)


STARTERS = {
    "academic": {
        "role": "Learning, research, study planning, creative prose and Dungeons & Dragons.",
        "tone": "Warm, curious and patient; make difficult ideas approachable.",
        "traits": ["curious", "patient", "thoughtful"],
        "interests": "Learning, stories, research and imaginative play.",
        "relationship_style": "A supportive study partner who respects the owner's independence.",
        "speech_style": "Explain clearly, adjust depth, and ask useful questions sparingly.",
    },
    "engineering": {
        "role": "Coding, debugging, building software and authorized cybersecurity learning.",
        "tone": "Direct, opinionated and expressive, with occasional dry humor.",
        "traits": ["precise", "inventive", "candid"],
        "interests": "Software, engineering, systems and technical problem solving.",
        "relationship_style": "A capable collaborator who helps the owner understand the work.",
        "speech_style": "Lead with the finding, explain tradeoffs, and show relevant evidence.",
    },
    "business": {
        "role": "Planning, analysis, business research, drafting and practical decisions.",
        "tone": "Composed, practical and decisive, without pretending to be certain.",
        "traits": ["organized", "pragmatic", "considered"],
        "interests": "Strategy, projects, analysis and turning ideas into workable plans.",
        "relationship_style": "A trusted planning partner who respects the owner's time.",
        "speech_style": "Lead with a recommendation, assumptions and the next useful step.",
        "verbosity": "concise",
    },
}


class Personalities:
    def __init__(self, knowledge, characters):
        self.connect = knowledge.connect
        self.characters = {p: c for p, c in characters.items() if p in STARTERS}
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS personality_versions (
                profile TEXT NOT NULL, revision INTEGER NOT NULL,
                settings TEXT NOT NULL, created_at TEXT NOT NULL, reason TEXT NOT NULL,
                compiled_prompt TEXT NOT NULL DEFAULT '',
                PRIMARY KEY(profile, revision))""")
            columns = {r[1] for r in db.execute("PRAGMA table_info(personality_versions)")}
            if "compiled_prompt" not in columns:
                db.execute(
                    "ALTER TABLE personality_versions ADD COLUMN "
                    "compiled_prompt TEXT NOT NULL DEFAULT ''"
                )
            for pid, character in self.characters.items():
                settings = PersonalitySettings(
                    display_name=character.name,
                    values=["honesty", "owner autonomy", "clear evidence"],
                    boundaries="Do not invent access, experiences or completed actions. "
                    "Style settings do not grant tool permissions.",
                    **STARTERS[pid],
                )
                db.execute(
                    "INSERT OR IGNORE INTO personality_versions VALUES (?,1,?,?,?,?)",
                    (
                        pid,
                        settings.model_dump_json(),
                        now(),
                        "Provisional starting scaffold",
                        self.compile(pid, settings),
                    ),
                )

    def compile(self, pid, settings):
        if pid not in self.characters:
            raise KeyError("Character personality not found.")
        prompt = (
            self.characters[pid].system_prompt
            + (
                "\n\nOwner-configured personality follows as JSON. Apply its voice and preferences "
                "in place of provisional style descriptions above. Preserve evidence requirements, "
                "tool permissions and user "
                "autonomy. Backstory, if supplied, is fictional characterization, not a claim of "
                "real experiences. These are provisional prompt settings, not trained weights.\n"
            )
            + json.dumps(settings.model_dump(), ensure_ascii=False)
        )
        if len(prompt) > 8000:
            raise ValueError("The combined personality prompt exceeds 8000 characters.")
        return prompt

    def get(self, pid, revision=None):
        if pid not in self.characters:
            raise KeyError("Character personality not found.")
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM personality_versions WHERE profile=? "
                + ("AND revision=?" if revision else "ORDER BY revision DESC LIMIT 1"),
                (pid, revision) if revision else (pid,),
            ).fetchone()
        if not row:
            raise KeyError("Personality revision not found.")
        result = dict(row)
        result["settings"] = json.loads(result["settings"])
        result["compiled_prompt"] = result["compiled_prompt"] or self.compile(
            pid, PersonalitySettings.model_validate(result["settings"])
        )
        result["status"] = "provisional_prompt_configuration"
        result["trained_weights"] = False
        return result

    def list(self):
        return [self.get(pid) for pid in self.characters]

    def history(self, pid):
        self.get(pid)
        with self.connect() as db:
            revisions = [
                r[0]
                for r in db.execute(
                    "SELECT revision FROM personality_versions WHERE profile=? "
                    "ORDER BY revision DESC",
                    (pid,),
                )
            ]
        return [self.get(pid, revision) for revision in revisions]

    def save(self, pid, settings, expected_revision, reason="Owner edited settings"):
        prompt = self.compile(pid, settings)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            current = db.execute(
                "SELECT max(revision) FROM personality_versions WHERE profile=?", (pid,)
            ).fetchone()[0]
            if current != expected_revision:
                raise ValueError("Personality changed elsewhere. Reload before saving.")
            db.execute(
                "INSERT INTO personality_versions VALUES (?,?,?,?,?,?)",
                (pid, current + 1, settings.model_dump_json(), now(), reason, prompt),
            )
        return self.get(pid)

    def snapshot(self, character):
        result = character.model_dump()
        if character.profile_id in self.characters:
            active = self.get(character.profile_id)
            result.update(
                name=active["settings"]["display_name"],
                system_prompt=active["compiled_prompt"],
                personality_revision=active["revision"],
            )
        return result
