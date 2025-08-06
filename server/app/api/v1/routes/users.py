from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_async_session
from app.schemas.user import UserCreate, UserUpdate, UserRead
from app.crud.user import get_user_by_id, get_all_users, create_user, update_user, delete_user
from app.core.security import get_current_user, require_role
from app.models.user import UserRole
from sqlalchemy.exc import IntegrityError

router = APIRouter()

@router.get("/", response_model=List[UserRead], summary="Получить всех пользователей", status_code=200)
async def read_users(db: AsyncSession = Depends(get_async_session), current_user = Depends(require_role(UserRole.admin))):
    return await get_all_users(db)

@router.get("/me", response_model=UserRead, summary="Get current user", description="Returns the current authenticated user.")
async def read_current_user(current_user = Depends(get_current_user)):
    print("current_user:", current_user)
    print("current_user dict:", current_user.__dict__)
    return UserRead.from_orm(current_user)

@router.get("/{user_id}", response_model=UserRead, summary="Получить пользователя по ID", status_code=200)
async def read_user(user_id: int, db: AsyncSession = Depends(get_async_session), current_user = Depends(require_role(UserRole.admin))):
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

@router.post("/", response_model=UserRead, summary="Создать пользователя", status_code=201)
async def create_new_user(user_in: UserCreate, db: AsyncSession = Depends(get_async_session), current_user = Depends(require_role(UserRole.admin))):
    try:
        print("create_new_user input:", user_in)
        from app.core.security import pwd_context
        user_data = user_in.dict()
        user_data["hashed_password"] = pwd_context.hash(user_data.pop("password"))
        from app.models.user import User
        new_user = User(**user_data)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        print("created user:", new_user)
        return UserRead.from_orm(new_user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Пользователь с именем '{user_in.username}' уже существует.",
        )
    except Exception as e:
        import traceback
        print("Exception in create_new_user:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"EXCEPTION: {e}\nTRACEBACK: {traceback.format_exc()}")

@router.put("/{user_id}", response_model=UserRead, summary="Обновить пользователя по ID", status_code=200)
async def update_existing_user(user_id: int, user_in: UserUpdate, db: AsyncSession = Depends(get_async_session), current_user = Depends(require_role(UserRole.admin))):
    user = await update_user(db, user_id, user_in)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return user

@router.delete("/{user_id}", summary="Удалить пользователя по ID", status_code=204)
async def delete_existing_user(user_id: int, db: AsyncSession = Depends(get_async_session), current_user = Depends(require_role(UserRole.admin))):
    success = await delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    return None

@router.post("/users", response_model=UserRead, status_code=201)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_async_session), current_user = Depends(require_role(UserRole.admin))):
    from app.core.security import pwd_context
    try:
        print("create_user input:", user)
        # Set a default password for new users (e.g., 'defaultpassword')
        hashed_password = pwd_context.hash("defaultpassword")
        user_dict = user.dict()
        user_dict["hashed_password"] = hashed_password
        from app.models.user import User
        new_user = User(**user_dict)
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        print("created user:", new_user)
        return UserRead.from_orm(new_user)
    except Exception as e:
        import traceback
        print("Exception in create_user:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))