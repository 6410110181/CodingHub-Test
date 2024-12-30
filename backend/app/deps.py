from fastapi import Depends, HTTPException, logger, status
from fastapi.security import OAuth2PasswordBearer

import typing
import jwt

from pydantic import ValidationError

from .models import user
from . import models
from . import security
from . import config


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

settings = config.get_settings()


async def get_current_user(
    token: typing.Annotated[str, Depends(oauth2_scheme)],
    session: typing.Annotated[models.AsyncSession, Depends(models.get_session)],
) -> user.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, key=settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        user_id: int = payload.get("sub")
        

        if user_id is None:
            raise credentials_exception

    except jwt.PyJWTError as e:
        print(e)
        raise credentials_exception

    db_user = await session.get(user.DBUser, user_id)
    if db_user is None:
        raise credentials_exception

    return db_user


async def get_current_active_user(
    current_user: typing.Annotated[user.User, Depends(get_current_user)]
) -> user.User:
    if current_user.status != "active":
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_active_superuser(
    current_user: typing.Annotated[user.User, Depends(get_current_user)],
) -> user.User:
    if "admin" not in current_user.roles:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    return current_user


class RoleChecker:
    def __init__(self, *allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        db_user: typing.Annotated[user.User, Depends(get_current_active_user)],
    ):
        for role in db_user.roles:
            if role in self.allowed_roles:
                return
        logger.debug(f"User with role {db_user.roles} not in {self.allowed_roles}")
        raise HTTPException(status_code=403, detail="Role not permitted")
