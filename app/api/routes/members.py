from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response, status

from app.api.schemas.common import PaginatedResponse
from app.api.schemas.member import (
    MemberCreate,
    MemberResponse,
    MemberStatusUpdate,
    MemberUpdate,
)
from app.dependencies import get_member_service
from app.domain.member import MemberStatus
from app.services.member_service import MemberService

router = APIRouter(prefix="/members", tags=["Members"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_member(
    data: MemberCreate,
    request: Request,
    response: Response,
    service: MemberService = Depends(get_member_service),
) -> MemberResponse:
    """Register a new library member."""
    member = service.create_member(data)
    response.headers["Location"] = str(request.url_for("get_member", member_id=member.id))
    return MemberResponse.model_validate(member)


@router.get("")
def list_members(
    status: MemberStatus | None = None,
    search: str | None = None,
    page: int = 1,
    size: int = 10,
    service: MemberService = Depends(get_member_service),
) -> PaginatedResponse[MemberResponse]:
    """List members with optional status filter and search."""
    items, total = service.list_members(
        page=page,
        size=size,
        status=status.value if status else None,
        search=search,
    )
    return PaginatedResponse(
        items=[MemberResponse.model_validate(m) for m in items],
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size if size > 0 else 0,
    )


@router.get("/{member_id}", name="get_member")
def get_member(
    member_id: UUID,
    service: MemberService = Depends(get_member_service),
) -> MemberResponse:
    """Get member detail by ID."""
    member = service.get_member(member_id)
    return MemberResponse.model_validate(member)


@router.put("/{member_id}")
def replace_member(
    member_id: UUID,
    data: MemberUpdate,
    service: MemberService = Depends(get_member_service),
) -> MemberResponse:
    """Replace member information (all fields)."""
    member = service.replace_member(member_id, data)
    return MemberResponse.model_validate(member)


@router.patch("/{member_id}")
def update_member(
    member_id: UUID,
    data: MemberUpdate,
    service: MemberService = Depends(get_member_service),
) -> MemberResponse:
    """Partially update member information (only provided fields)."""
    member = service.update_member(member_id, data)
    return MemberResponse.model_validate(member)


@router.patch("/{member_id}/status")
def update_member_status(
    member_id: UUID,
    data: MemberStatusUpdate,
    service: MemberService = Depends(get_member_service),
) -> MemberResponse:
    """Change member status."""
    member = service.update_status(member_id, data)
    return MemberResponse.model_validate(member)
