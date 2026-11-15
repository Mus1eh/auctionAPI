from sqlalchemy import or_

from app import models
from app.core.config import SeedSettings
from app.core.database import sessionLocal
from app.core.security import Hash
from app.seeders.rbac import PERMISSIONS, ROLE_PERMISSIONS, ROLES

seed_settings = SeedSettings()

SUPERADMIN_USERNAME = seed_settings.superadmin_username
SUPERADMIN_EMAIL = seed_settings.superadmin_email
SUPERADMIN_PASSWORD = seed_settings.superadmin_password

ADMIN_USERNAME = seed_settings.admin_username
ADMIN_EMAIL = seed_settings.admin_email
ADMIN_PASSWORD = seed_settings.admin_password


def seed_database():
    db = sessionLocal()

    try:
        role_names = ROLES

        for role_name in role_names:
            role = db.query(models.Role).filter(models.Role.name == role_name).first()

            if not role:
                db.add(models.Role(name=role_name))

        db.flush()

        permissions_definitions = PERMISSIONS

        for permission_name in permissions_definitions:
            permission = (
                db.query(models.Permission)
                .filter(models.Permission.name == permission_name)
                .first()
            )
            if not permission:
                db.add(models.Permission(name=permission_name))

        db.flush()

        role_permission_map = ROLE_PERMISSIONS

        for role_name, permission_names in role_permission_map.items():
            role = db.query(models.Role).filter(models.Role.name == role_name).first()

            for permission_name in permission_names:
                permission = (
                    db.query(models.Permission)
                    .filter(models.Permission.name == permission_name)
                    .first()
                )

                if permission not in role.permissions:
                    role.permissions.append(permission)
                    print(
                        f"Permission '{permission_name}' assigned to role '{role_name}'."
                    )

        db.flush()

        admin_role = db.query(models.Role).filter(models.Role.name == "admin").first()

        superadmin_role = (
            db.query(models.Role).filter(models.Role.name == "superadmin").first()
        )

        existing_admin = (
            db.query(models.User)
            .filter(
                or_(
                    models.User.username == ADMIN_USERNAME,
                    models.User.email == ADMIN_EMAIL,
                )
            )
            .first()
        )

        existing_superadmin = (
            db.query(models.User)
            .filter(
                or_(
                    models.User.username == SUPERADMIN_USERNAME,
                    models.User.email == SUPERADMIN_EMAIL,
                )
            )
            .first()
        )

        if existing_superadmin:
            if not any(role.name == "superadmin" for role in existing_superadmin.roles):
                existing_superadmin.roles.append(superadmin_role)

            print("Superadmin already exists. Role assignment checked.")

        else:
            new_superadmin = models.User(
                username=SUPERADMIN_USERNAME,
                email=SUPERADMIN_EMAIL,
                password=Hash.crypt_password(SUPERADMIN_PASSWORD),
                roles=[superadmin_role],
            )

            db.add(new_superadmin)
            print("Superadmin user created successfully.")

        if existing_admin:
            if not any(role.name == "admin" for role in existing_admin.roles):
                existing_admin.roles.append(admin_role)

            print("Admin already exists. Role assignment checked.")

        else:
            new_admin = models.User(
                username=ADMIN_USERNAME,
                email=ADMIN_EMAIL,
                password=Hash.crypt_password(ADMIN_PASSWORD),
                roles=[admin_role],
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
