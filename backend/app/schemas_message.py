# backend/app/schemas_message.py

from __future__ import annotations

from typing import Any

from flask import url_for
from marshmallow import Schema, fields


def _original_name(path: str) -> str:
    if not path:
        return ""
    _, _, original = path.partition("_")
    return original or path


class FileSchema(Schema):
    id_file = fields.Int(dump_only=True)
    mime = fields.Str()
    taille = fields.Int()
    sha256 = fields.Str()
    filename = fields.Method("get_filename")
    url = fields.Method("get_url")

    def get_filename(self, obj: Any) -> str:
        return _original_name(getattr(obj, "path", ""))

    def get_url(self, obj: Any) -> str:
        try:
            return url_for("messages.download_file", file_id=getattr(obj, "id_file", 0))
        except RuntimeError:
            return f"/api/messages/files/{getattr(obj, 'id_file', 0)}"


class ReactionSchema(Schema):
    emoji = fields.Str(required=True)
    id_user = fields.Int(required=True)
    ts = fields.DateTime(dump_only=True)
    is_mine = fields.Method("get_is_mine")

    def get_is_mine(self, obj: Any) -> bool:
        context = self.context if isinstance(self.context, dict) else {}
        current_user = context.get("user_id")
        return bool(current_user and getattr(obj, "id_user", None) == current_user)


class MessageSchema(Schema):
    id_msg = fields.Int(dump_only=True)
    contenu_chiffre = fields.Str(required=True)
    ts_msg = fields.DateTime(dump_only=True)
    sender_id = fields.Int(dump_only=True)
    conv_id = fields.Int(dump_only=True)
    files = fields.Nested(FileSchema, many=True, dump_only=True)
    reactions = fields.Nested(ReactionSchema, many=True, dump_only=True)
    reaction_summary = fields.Method("get_reaction_summary")

    def get_reaction_summary(self, obj: Any) -> list[dict[str, Any]]:
        summary: dict[str, dict[str, Any]] = {}
        context = self.context if isinstance(self.context, dict) else {}
        current_user = context.get("user_id")
        for reaction in getattr(obj, "reactions", []) or []:
            info = summary.setdefault(
                getattr(reaction, "emoji", ""),
                {"emoji": getattr(reaction, "emoji", ""), "count": 0, "mine": False},
            )
            info["count"] += 1
            if current_user and getattr(reaction, "id_user", None) == current_user:
                info["mine"] = True
        return list(summary.values())
