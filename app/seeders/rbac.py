"""Roles and permissions, shared by the seeder and the test fixtures."""

ROLES = ["superadmin", "admin", "user"]

PERMISSIONS = {
    "admin.access": "Access admin endpoints",
    "user.role.assign": "Assign roles to users",
    "user.role.remove": "Remove roles from users",
    "product.status_request.view": "View pending product status requests",
    "product.status_request.approve": "Approve product status requests",
    "product.status_request.reject": "Reject product status requests",
    "product.status.change": "Change a product's status directly",
    "product.view_all": "View products of any status from all users",
    "product.update_any": "Update any user's product",
    "product.delete_any": "Delete any user's product",
    "user.view_any": "View any user's profile",
    "user.delete": "Delete regular users",
    "user.delete_admin": "Delete admin users",
    "bid.approve_any": "Approve bids on products owned by others",
}

ROLE_PERMISSIONS = {
    "admin": [
        "admin.access",
        "product.status_request.view",
        "product.status_request.approve",
        "product.status_request.reject",
        "product.status.change",
        "product.view_all",
        "product.update_any",
        "product.delete_any",
        "user.view_any",
        "user.delete",
    ],
    # require_permission bypasses superadmin, but keep the full list so
    # the DB stays accurate if the bypass is ever removed.
    "superadmin": list(PERMISSIONS),
    "user": [],
}
