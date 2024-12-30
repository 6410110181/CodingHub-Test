from fastapi import APIRouter, Depends, HTTPException, Request, Response, UploadFile, status
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from fastapi import Query
from typing import Annotated
from typing import  Optional

from .. import deps
from ..models import user,get_session
from ..models.user import DBUser

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me")
def get_me(current_user: user.DBUser = Depends(deps.get_current_user)) :
    return current_user

@router.get("/users", response_model=list[DBUser])
async def get_users(
    session: AsyncSession = Depends(get_session),
    skip: int = Query(1, alias="page", ge=1),  # หน้าเริ่มต้นที่ 1
    limit: int = Query(10, le=100),  # จำกัดการแสดงผลไม่เกิน 100 รายการ
    username: Optional[str] = Query(None, alias="filter_username"),  # ฟิลเตอร์ตามชื่อผู้ใช้
    email: Optional[str] = Query(None, alias="filter_email")  # ฟิลเตอร์ตามอีเมล
):
    # เริ่มต้น query
    query = select(DBUser)

    # เพิ่ม filter ตาม username และ email
    if username:
        query = query.where(DBUser.username.ilike(f"%{username}%"))
    if email:
        query = query.where(DBUser.email.ilike(f"%{email}%"))

    # คำนวณค่า skip ที่เหมาะสม (หน้าเริ่มต้นที่ 1)
    offset_value = (skip - 1) * limit

    # เพิ่ม offset และ limit
    query = query.offset(offset_value).limit(limit)

    # Execute query
    result = await session.execute(query)
    users = result.scalars().all()

    return users


@router.post("/create")
async def create(
    user_info: user.RegisteredUser,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> user.User:

    result = await session.exec(
        select(user.DBUser).where(user.DBUser.username == user_info.username)
    )
    db_user = result.one_or_none()


    if not db_user: 
        db_user = DBUser.model_validate(user_info)
        await db_user.set_password(user_info.password)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)

        return db_user
        
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This username is exists.")

   

@router.put("/change_password")
async def change_password(

    password_update: user.ChangedPassword,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: user.User = Depends(deps.get_current_user),
) -> user.User:
    
    result = await session.exec(
        select(user.DBUser).where(user.DBUser.id == current_user.id)
    )
    db_user = result.one_or_none()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found this user",
        )

    if not await db_user.verify_password(password_update.current_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
    if db_user:
        await db_user.set_password(password_update.new_password)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        raise HTTPException(
            status_code=status.HTTP_200_OK,
            detail="Change password successfully",
        )
    



@router.put("/update")
async def update(
    request: Request,
    user_update: user.UpdatedUser,
    # password_update: user.ChangedPassword,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: user.User = Depends(deps.get_current_user),
) -> user.User:

    result = await session.exec(
        select(user.DBUser).where(user.DBUser.id == current_user.id)
    )
    db_user = result.one_or_none()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found this user",
        )

    if db_user:
        db_user.sqlmodel_update(user_update)
        # await db_user.set_password(password_update.new_password)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)


        return db_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    db_user = await session.get(user.DBUser, user_id)
    if db_user:
        await session.delete(db_user)
        await session.commit()
        
        
        return dict(message="delete success")
    raise HTTPException(status_code=404, detail="user not found")

