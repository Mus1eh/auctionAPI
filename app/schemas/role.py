from pydantic import BaseModel


class UserRoleUpdate(BaseModel):
    role_name: str
