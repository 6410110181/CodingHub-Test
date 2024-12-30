from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import (OAuth2PasswordRequestForm,)


from sqlmodel import select
from typing import Annotated
import datetime
from ..models import user
from .. import config
from .. import models
from .. import security

router = APIRouter(tags=["authentication"])

settings = config.get_settings()


@router.post(
    "/token",
)
async def authentication(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[models.AsyncSession, Depends(models.get_session)],
) -> user.Token:

    result = await session.exec(
        select(user.DBUser).where(user.DBUser.username == form_data.username)
    )

    db_user = result.one_or_none()

    if not db_user or not await db_user.verify_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    db_user.last_login_date = datetime.datetime.now()

    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)

    access_token_expires = datetime.timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return user.Token(
        access_token=security.create_access_token(
            data={"sub": str(db_user.id)},
            expires_delta=access_token_expires,
        ),
        refresh_token=security.create_refresh_token(
            data={"sub":str(db_user.id)},
            expires_delta=access_token_expires,
        ),
        token_type="Bearer",
        scope="",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        expires_at=datetime.datetime.now() + access_token_expires,
        issued_at=db_user.last_login_date,
        user_id=db_user.id,
    )
