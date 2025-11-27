from datetime import datetime
from bson import ObjectId
from ..extensions import mongo
from ..utils.security import hash_password


ADMIN_COLLECTION = "admins"


def get_admin_collection():
    return mongo.db[ADMIN_COLLECTION]


def create_admin(email: str, plain_password: str, org_id: ObjectId):
    admin_col = get_admin_collection()
    doc = {
        "email": email,
        "password_hash": hash_password(plain_password),
        "organization_id": org_id,
        "role": "admin",
        "created_at": datetime.utcnow(),
    }
    result = admin_col.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def find_admin_by_email(email: str):
    admin_col = get_admin_collection()
    return admin_col.find_one({"email": email})


def find_admin_by_id(admin_id: str | ObjectId):
    admin_col = get_admin_collection()
    if isinstance(admin_id, str):
        admin_id = ObjectId(admin_id)
    return admin_col.find_one({"_id": admin_id})


def delete_admins_by_org_id(org_id: ObjectId):
    admin_col = get_admin_collection()
    admin_col.delete_many({"organization_id": org_id})
