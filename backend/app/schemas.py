# backend/app/schemas.py

from marshmallow import Schema, fields, validates, ValidationError, validate

class RegisterSchema(Schema):
    email = fields.Email(
        required=True,
        error_messages={"required": "Email requis", "invalid": "Format email invalide"}
    )
    pseudo = fields.Str(
        required=True,
        validate=[
            validate.Length(min=2, max=50, error="Le pseudo doit faire entre 2 et 50 caractères"),
            validate.Regexp(r"^[a-zA-Z0-9_\-.]+$", error="Le pseudo doit être alphanumérique")
        ],
        error_messages={"required": "Pseudo requis"}
    )
    password = fields.Str(
        required=True,
        validate=[
            validate.Length(min=8, max=128, error="Le mot de passe doit faire entre 8 et 128 caractères"),
        ],
        error_messages={"required": "Mot de passe requis"}
    )

    # Ajout du champ role, optionnel, default=member (pour sécurité)
    role = fields.Str(
        required=False,
        validate=validate.OneOf(["admin", "member"], error="Rôle invalide"),
        missing="member"
    )

    @validates("password")
    def validate_password(self, value):
        import re
        if not re.search(r'[A-Z]', value):
            raise ValidationError("Le mot de passe doit contenir au moins une majuscule")
        if not re.search(r'[a-z]', value):
            raise ValidationError("Le mot de passe doit contenir au moins une minuscule")
        if not re.search(r'\d', value):
            raise ValidationError("Le mot de passe doit contenir au moins un chiffre")
        if not re.search(r'[@$!%*?&.,;:+=_-]', value):
            raise ValidationError("Le mot de passe doit contenir au moins un caractère spécial (@$!%*?&.,;:+=_-)")

class LoginSchema(Schema):
    email = fields.Email(
        required=True,
        error_messages={"required": "Email requis", "invalid": "Format email invalide"}
    )
    password = fields.Str(
        required=True,
        error_messages={"required": "Mot de passe requis"}
    )
    # Si tu veux déjà permettre le TOTP dès le login, ajoute le champ ici (optionnel)
    code = fields.Str(required=False)
