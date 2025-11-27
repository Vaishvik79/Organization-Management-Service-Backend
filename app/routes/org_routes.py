from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
)
from pymongo.errors import CollectionInvalid

from ..extensions import mongo
from ..models.organizations import (
    create_organization,
    find_org_by_name,
    find_org_by_slug,
    update_org_metadata,
    delete_organization,
)
from ..models.admin import create_admin, find_admin_by_id, delete_admins_by_org_id
from ..utils.validators import normalize_org_name, validate_required_fields
from ..utils.security import hash_password

org_bp = Blueprint("org", __name__)


# -------------------------
# POST /org/create
# -------------------------
@org_bp.post("/create")
def create_org():
    """
    Body:
    {
      "organization_name": "My Company",
      "email": "admin@example.com",
      "password": "strongpass"
    }
    """
    data = request.get_json() or {}
    try:
        validate_required_fields(data, ["organization_name", "email", "password"])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    org_name = data["organization_name"].strip()
    email = data["email"].strip().lower()
    password = data["password"]

    # Check if org already exists
    existing = find_org_by_name(org_name)
    if existing:
        return jsonify({"error": "Organization name already exists"}), 400

    # Normalize to build collection name
    slug = normalize_org_name(org_name)
    collection_name = f"org_{slug}"

    # Extra safety: check slug not already used
    if find_org_by_slug(slug):
        return jsonify({"error": "Organization slug already exists"}), 400

    # Create empty collection for this org
    try:
        mongo.db.create_collection(collection_name)
    except CollectionInvalid:
        return jsonify({"error": "Collection for this organization already exists"}), 400

    # 1) Create organization metadata doc WITHOUT admin yet
    org_doc = create_organization(
        name=org_name,
        slug=slug,
        collection_name=collection_name,
        admin_id=None,
    )

    org_id = org_doc["_id"]

    # 2) Create admin with org reference
    admin_doc = create_admin(email=email, plain_password=password, org_id=org_id)

    # 3) Update organization with admin_id
    update_org_metadata(org_id, {"admin_id": admin_doc["_id"]})

    return jsonify({
        "message": "Organization created successfully",
        "organization": {
            "id": str(org_id),
            "name": org_name,
            "slug": slug,
            "collection_name": collection_name,
            "admin_email": email,
        }
    }), 201


# -------------------------
# GET /org/get
# -------------------------
@org_bp.get("/get")
def get_org():
    """
    Prefer: GET /org/get?organization_name=My%20Company

    (If you really want, you can also send JSON:
     { "organization_name": "My Company" })
    """
    org_name = request.args.get("organization_name")

    # Optional: support JSON body too
    if not org_name:
        data = request.get_json(silent=True) or {}
        org_name = data.get("organization_name")

    if not org_name:
        return jsonify({"error": "organization_name is required"}), 400

    org = find_org_by_name(org_name)
    if not org:
        return jsonify({"error": "Organization not found"}), 404

    return jsonify({
        "id": str(org["_id"]),
        "name": org["name"],
        "slug": org["slug"],
        "collection_name": org["collection_name"],
        "connection_details": org.get("connection_details", {}),
        "admin_id": str(org["admin_id"]) if org.get("admin_id") else None,
        "created_at": org.get("created_at").isoformat() if org.get("created_at") else None,
    }), 200


# -------------------------
# PUT /org/update
# -------------------------
@org_bp.put("/update")
@jwt_required()
def update_org():
    """
    Auth required.
    Body:
    {
      "organization_name": "Current Name",        # required
      "new_organization_name": "New Name",        # optional
      "email": "new_admin_email@example.com",     # optional
      "password": "new_password"                  # optional
    }
    """
    current_admin_id = get_jwt_identity()

    data = request.get_json() or {}
    org_name = data.get("organization_name")

    if not org_name:
        return jsonify({"error": "organization_name is required"}), 400

    admin = find_admin_by_id(current_admin_id)
    if not admin:
        return jsonify({"error": "Admin not found"}), 404

    org = find_org_by_name(org_name)
    if not org:
        return jsonify({"error": "Organization not found"}), 404

    # Ensure this admin belongs to this organization
    if admin["organization_id"] != org["_id"]:
        return jsonify({"error": "Not authorized to update this organization"}), 403

    updates = {}

    # ---- 1) Handle organization rename + collection migration ----
    new_org_name = data.get("new_organization_name")
    if new_org_name and new_org_name.strip() != org["name"]:
        new_org_name = new_org_name.strip()
        new_slug = normalize_org_name(new_org_name)

        # Check uniqueness
        existing = find_org_by_name(new_org_name)
        existing_slug = find_org_by_slug(new_slug)
        if (existing and existing["_id"] != org["_id"]) or \
           (existing_slug and existing_slug["_id"] != org["_id"]):
            return jsonify({"error": "New organization name already exists"}), 400

        old_collection_name = org["collection_name"]
        new_collection_name = f"org_{new_slug}"

        db = mongo.db

        # Create new collection and copy data
        try:
            db.create_collection(new_collection_name)
        except CollectionInvalid:
            # If already exists, you could either error or still try to merge
            return jsonify({"error": "Target collection already exists"}), 400

        src = db[old_collection_name]
        dest = db[new_collection_name]

        docs = list(src.find())
        if docs:
            dest.insert_many(docs)

        # Drop old collection
        src.drop()

        updates["name"] = new_org_name
        updates["slug"] = new_slug
        updates["collection_name"] = new_collection_name

    # ---- 2) Handle admin email/password update ----
    new_email = data.get("email")
    new_password = data.get("password")

    admin_updates = {}
    if new_email:
        admin_updates["email"] = new_email.strip().lower()
    if new_password:
        admin_updates["password_hash"] = hash_password(new_password)

    if admin_updates:
        mongo.db["admins"].update_one({"_id": admin["_id"]}, {"$set": admin_updates})

    if updates:
        update_org_metadata(org["_id"], updates)

    return jsonify({"message": "Organization updated successfully"}), 200


# -------------------------
# DELETE /org/delete
# -------------------------
@org_bp.delete("/delete")
@jwt_required()
def delete_org():
    """
    Auth required (admin).
    Body:
    {
      "organization_name": "My Company"
    }
    """
    current_admin_id = get_jwt_identity()
    data = request.get_json() or {}
    org_name = data.get("organization_name")

    if not org_name:
        return jsonify({"error": "organization_name is required"}), 400

    admin = find_admin_by_id(current_admin_id)
    if not admin:
        return jsonify({"error": "Admin not found"}), 404

    org = find_org_by_name(org_name)
    if not org:
        return jsonify({"error": "Organization not found"}), 404

    # Check ownership
    if admin["organization_id"] != org["_id"]:
        return jsonify({"error": "Not authorized to delete this organization"}), 403

    # Drop dynamic org collection
    collection_name = org["collection_name"]
    mongo.db[collection_name].drop()

    # Delete admin(s) of this org
    delete_admins_by_org_id(org["_id"])

    # Delete organization metadata
    delete_organization(org["_id"])

    return jsonify({"message": "Organization deleted successfully"}), 200
