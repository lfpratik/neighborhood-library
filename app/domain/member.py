from enum import StrEnum


class MemberStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


MEMBER_STATUS_TRANSITIONS = {
    MemberStatus.ACTIVE: {MemberStatus.INACTIVE, MemberStatus.SUSPENDED},
    MemberStatus.INACTIVE: {MemberStatus.ACTIVE},
    MemberStatus.SUSPENDED: {MemberStatus.ACTIVE},
}


class MemberDomainError(Exception):
    """Base domain error for books."""


class MemberNotFoundError(MemberDomainError):
    """Member with given ID does not exist."""


class MemberNotActiveError(MemberDomainError):
    """Member is not active and cannot borrow books."""


class InvalidMemberStatusTransitionError(MemberDomainError):
    """Invalid status transition attempted."""


class DuplicateEmailError(MemberDomainError):
    """A member with this email already exists."""


def validate_member_status_transition(current: MemberStatus, new: MemberStatus) -> None:
    """Validate that a member status transition is allowed."""
    allowed = MEMBER_STATUS_TRANSITIONS.get(current, set())
    if new not in allowed:
        raise InvalidMemberStatusTransitionError(
            f"Cannot transition from '{current.value}' to '{new.value}'"
        )
