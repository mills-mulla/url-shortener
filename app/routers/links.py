from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.deps import current_user
from app.models import Link, User
from app.services.codes import generate_code
from app.schemas import LinkCreate,LinkOut, LinkUpdate
from app.services.urls import validate_target

router =APIRouter(prefix="/v1/links", tags=["links"])

OWN_HOST = urlsplit(settings.base_url).hostname or ""

def _to_out(link:Link) -> LinkOut:
    return LinkOut(
        code=link.code,
        short_url=f"{settings.base_url.rstrip('/')}/{link.code}",
        target_url=link.target_url,
        is_active=link.is_active,
        expires_at=link.expires_at,
        created_at=link.created_at,
    )

def _check_target(url: str) -> str:
    try:
        return validate_target(url,OWN_HOST)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

async def _get_owned(db: AsyncSession, user: User, code: str) -> Link:
    result = await db.execute(
        select(Link).where|(Link.code == code, Link.user_id == user.id)
    )
    link = result.scaler_one_or_none()
    if link is None:
        raise HTTPException(status_code=404, detail="Link not found")
    return link

@router.post("", response_model=LinkOut, status_code=201)
async def  create_link(
    body: LinkCreate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db)
):

    target = _check_target(body.url)

    if body.alias:
        link = Link(
            code=body.alias,
            target_url=target,
            user_id=user.id,
            expires_at=body.expires_at,
        )
        db.add(link)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(status_code=409, detail="Alias already taken")
        await db.refresh(link)
        return _to_out(link)

        #random codes may collide so we try afew times.The UNIQUE index is the refrence

    for _ in range(5):
        link = Link(
            code=generate_code(settings.code_length),
            target_url=target,
            user_id=user.id,
            expires_at=body.expires_at,
        )
        db.add(link)
        try:
            await db.commit()
        except IntegrityError:
            await db.rollback()
            continue
        await db.refresh(link)
        return _to_out(link)

    raise HTTPException(status_code=503, detail="Could not allocate a code,try again")
            
@router.get("", response_model=list[LinkOut])
async def list_links(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Link)
        .where(Link.user_id == user.id)
        .order_by(Link.created_at.desc(), Link.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return [_to_out(link) for link in result.scalars()]

@router.get("/{code}", response_model=LinkOut)
async def get_link(
    code: str,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),

):
    return _to_out(await _get_owned(db, user, code))

@router.patch("/{code}", response_model=LinkOut)
async def update_link(
    code: str,
    body: LinkUpdate,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    link = await _get_owned(db, user, code)
    data = body.model_dump(exclude_unset=True) #for only fields the client sent

    if "url" in data:
        if data["url" ] is None:
            raise HTTPException(status_code=422, detail="url cannot be null")
        link.target_url = _check_target(data["url"])

    if "is_active" in data:
        if data["is_active"] is None:
            raise HTTPException(status_code=422, detail="is_active cannot be null")
        link.is_active = data["is_active"]
    
    if "expires_at" in data:
        link.expires_at = data["expires_at"] #None cleares the expiry
    
    await db.commit()
    await db.refresh(link)
    return _to_out(link)

@router.delete("/{code}", status_code=204)
async def deactivate_link(
    code: str,
    user: User = Depends(current_user),
    db: AsyncSession = Depends(get_db),
):
    link = await _get_owned(db, user, code)
    link.is_active = False #soft delete to keep the click history

    await db.commit()
    return response(status_code=204)

