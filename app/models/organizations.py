from datetime import datetime
from bson import ObjectId
from ..extensions import mongo

ORG_COLLECTION = "organizations"


def get_org_collection():
    return mongo.db[ORG_COLLECTION]


def create_organization(name: str, slug: str, collection_name: str, admin_id: ObjectId):
    org_col = get_org_collection()
    doc = {
        "name": name.strip(),
        "slug": slug,
        "collection_name": collection_name,
        "connection_details": {"database": mongo.db.name},
        "admin_id": admin_id,
        "created_at": datetime.utcnow(),
    }
    result = org_col.insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc


def find_org_by_name(name: str):
    org_col = get_org_collection()
    return org_col.find_one({"name": name.strip()})


def find_org_by_slug(slug: str):
    org_col = get_org_collection()
    return org_col.find_one({"slug": slug})


def update_org_metadata(org_id: ObjectId, update_dict: dict):
    org_col = get_org_collection()
    org_col.update_one({"_id": org_id}, {"$set": update_dict})


def delete_organization(org_id: ObjectId):
    org_col = get_org_collection()
    org_col.delete_one({"_id": org_id})
