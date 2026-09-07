from datetime import datetime, timezone

from app.auth.models import UserRole
from app.auth.security import hash_password
from app.database import users_collection


email = "admin@example.com"

user = {
    "email": email,
    "full_name": "System Admin",
    "password_hash": hash_password(
        "AdminUser"
    ),
    "role": UserRole.ADMIN.value,
    "is_active": True,
    "created_at": datetime.now(
        timezone.utc
    ),
}

existing = users_collection.find_one(
    {"email": email}
)

if existing:
    print("Admin already exists")
else:
    users_collection.insert_one(user)
    print("Admin created")