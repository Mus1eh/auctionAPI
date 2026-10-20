from fastapi import APIRouter, Depends

from app import models
from app.oauth2 import get_current_user
from app.permissions import require_role

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
    dependencies=[Depends(require_role(["admin", "superadmin"]))],
)


@router.get("dashboard")
def admin_dashboard(current_user: models.User = Depends(get_current_user)):
    return {
        "message": "Welcome to the admin dashboard!",
        "username": current_user.username,
        "role": current_user.role_name,
    }
