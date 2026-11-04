from pydantic import BaseModel, ConfigDict


class RoleShow(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


class UserRoleUpdate(BaseModel):
    role_name: str
