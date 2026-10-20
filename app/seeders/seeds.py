import os

from dotenv import load_dotenv
from sqlalchemy import or_

from app import models
from app.database import sessionLocal
from app.hashing import Hash

load_dotenv()

SUPERADMIN_USERNAME = os.environ["SUPERADMIN_USERNAME"]
SUPERADMIN_EMAIL = os.environ["SUPERADMIN_EMAIL"]
SUPERADMIN_PASSWORD = os.environ["SUPERADMIN_PASSWORD"]

ADMIN_USERNAME = os.environ["ADMIN_USERNAME"]
ADMIN_EMAIL = os.environ["ADMIN_EMAIL"]
ADMIN_PASSWORD = os.environ["ADMIN_PASSWORD"]


def seed_database():
    db = sessionLocal()

    try:
        roles = ["superadmin", "admin", "user"]

        for role_name in roles:
            role = db.query(models.Role).filter(models.Role.name == role_name).first()
            if not role:
                new_role = models.Role(name=role_name)
                db.add(new_role)
        db.flush()

        admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()

        superadmin_role = (
            db.query(models.Role).filter(models.Role.name == "superadmin").first()
        )

        admin_username = ADMIN_USERNAME
        admin_email = ADMIN_EMAIL
        admin_password = ADMIN_PASSWORD
        superadmin_username = SUPERADMIN_USERNAME
        superadmin_email = SUPERADMIN_EMAIL
        superadmin_password = SUPERADMIN_PASSWORD

        existing_admin = (
            db.query(models.User)
            .filter(
                or_(
                    models.User.username == admin_username,
                    models.User.email == admin_email,
                )
            )
            .first()
        )

        existing_superadmin = (
            db.query(models.User)
            .filter(
                or_(
                    models.User.username == superadmin_username,
                    models.User.email == superadmin_email,
                )
            )
            .first()
        )
        if existing_superadmin:
            print("Superadmin user already exists. Skipping creation.")
        else:
            new_superadmin = models.User(
                username=superadmin_username,
                email=superadmin_email,
                password=Hash.crypt_password(superadmin_password),
                role_name=superadmin_role.name,
            )
            db.add(new_superadmin)
            print("Superadmin user created successfully.")

        if existing_admin:
            print("Admin user already exists. Skipping creation.")
        else:
            new_admin = models.User(
                username=admin_username,
                email=admin_email,
                password=Hash.crypt_password(admin_password),
                role_name=admin_role.name,
            )
            db.add(new_admin)
            print("Admin user created successfully.")

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
