# backend/app/schemas_message.py

from marshmallow import Schema, fields

class MessageSchema(Schema):
    id_msg = fields.Int(dump_only=True)
    contenu_chiffre = fields.Str(required=True)
    ts_msg = fields.DateTime(dump_only=True)
    sender_id = fields.Int(dump_only=True)
    conv_id = fields.Int(dump_only=True)
