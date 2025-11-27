from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token

from ..models.admin import find_admin_by_email
from ..models.organizations import find_org_by_id
from ..utils.security import verify_password

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
def admin_login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    admin = find_admin_by_email(email)
    if not admin or not verify_password(password, admin["password_hash"]):
        return jsonify({"error": "Invalid credentials"}), 401

    org = find_org_by_id(admin["organization_id"])
    if not org:
        return jsonify({"error": "Organization not found for this admin"}), 404

    # JWT payload: admin_id + org_id
    additional_claims = {
        "org_id": str(org["_id"]),
        "org_name": org["name"],
        "role": admin.get("role", "admin"),
    }

    access_token = create_access_token(identity=str(admin["_id"]), additional_claims=additional_claims)

    return jsonify({
        "access_token": access_token,
        "admin_id": str(admin["_id"]),
        "organization_id": str(org["_id"]),
        "organization_name": org["name"],
    }), 200
