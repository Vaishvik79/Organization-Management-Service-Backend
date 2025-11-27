📦 Organization Management Service — Flask + MongoDB (Multi-Tenant Architecture)

This project is a backend service designed for managing multiple organizations in a multi-tenant architecture using Flask and MongoDB.
Each organization gets its own dynamic MongoDB collection, while the master database stores all global metadata and admin credentials.

This project is created as part of a Backend Developer Intern Assignment.

🚀 Tech Stack

Python 3
Flask (App Factory Pattern)
MongoDB (PyMongo)
Flask-JWT-Extended (Authentication)
Flask-Bcrypt (Password Hashing)
python-dotenv (Environment Variables)

⚙️ Core Features Implemented
✅ 1. Create Organization

POST /org/create
Validates unique organization
Generates a safe slug
Creates dynamic MongoDB collection: org_<slug>
Creates admin user with hashed password
Stores org metadata in master DB

✅ 2. Get Organization

GET /org/get?organization_name=<name>
(or body JSON)
Returns all metadata: slug, collection name, admin_id, created_at

✅ 3. Admin Login

POST /admin/login
Validates admin email/password
Returns JWT token with:
admin_id
org_id
organization_name
role

✅ 4. Update Organization

PUT /org/update (JWT required)
Update admin email/password
Rename organization
Dynamic migration:
Create new collection
Copy old documents
Drop old collection

✅ 5. Delete Organization

DELETE /org/delete (JWT required)
Only the admin of that organization can delete
Deletes:
Dynamic org collection
Admin users
Organization metadata

🗂 Project Folder Structure
backend_org_service/
│── main.py
│── requirements.txt
│── .env
└── app/
    ├── __init__.py
    ├── config.py
    ├── extensions.py
    ├── models/
    │   ├── organization.py
    │   └── admin.py
    ├── routes/
    │   ├── org_routes.py
    │   └── auth_routes.py
    └── utils/
        ├── security.py
        └── validators.py

🔧 Installation & Setup
1. Create Virtual Environment
Windows:
python -m venv venv
venv\Scripts\activate

Mac/Linux:
python3 -m venv venv
source venv/bin/activate

2. Install Dependencies
pip install -r requirements.txt

3. Create .env File

Inside your project root:
SECRET_KEY=<random hex>
JWT_SECRET_KEY=<random hex>
MONGO_URI=mongodb://localhost:27017/org_service_db

Generate random keys:
import secrets
print(secrets.token_hex(32))

4. Run the Server
python main.py

API base URL:
http://localhost:5000/

📐 High-Level Architecture
Master Database
organizations collection
admins collection
Dynamic Collections (Per Organization)

Created automatically:
org_<slug>
Authentication
JWT tokens (Bearer tokens)
Admin-specific access for update and delete operations
Password Security
All admin passwords are hashed with bcrypt

⚖️ Design Choices & Tradeoffs
Slug ensures safe and valid Mongo collection names
Storing admins separately supports future multi-admin roles
Dynamic MongoDB collections allow simple tenant isolation
Designed for scalability and modularity using Flask app factory

Can be extended to:
Per-tenant databases
Sharding
API rate-limiting
Multi-role authorization
