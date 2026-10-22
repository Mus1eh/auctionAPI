from enum import Enum


class ProductStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    SOLD = "sold"
    REJECTED = "rejected"


class BidStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApproveBidding(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"


# creating new enum seperated to avoid circular import issues !
