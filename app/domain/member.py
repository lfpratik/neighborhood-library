from enum import StrEnum


class MemberStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


MEMBER_STATUS_TRANSITIONS = {
    MemberStatus.ACTIVE: [MemberStatus.INACTIVE, MemberStatus.SUSPENDED],
    MemberStatus.INACTIVE: [MemberStatus.ACTIVE],
    MemberStatus.SUSPENDED: [MemberStatus.ACTIVE],
}


class MemberNotFoundError(Exception):
    """Member with given ID does not exist."""


class MemberNotActiveError(Exception):
    """Member is not active and cannot borrow books."""


class DuplicateEmailError(Exception):
    """A member with this email already exists."""


def validate_member_status_transition(current: MemberStatus, new: MemberStatus) -> None:
    """Validate that a member status transition is allowed. Raises on invalid."""
    allowed = MEMBER_STATUS_TRANSITIONS.get(current, [])
    if new not in allowed:
        raise MemberNotActiveError(f"Cannot transition from '{current.value}' to '{new.value}'")
