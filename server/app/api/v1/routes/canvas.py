from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.core.security import get_current_user
from app.models.user import User
from app.services.canvas_auth import canvas_auth_service
from app.services.canvas_client import canvas_client
from app.services.canvas_sync import canvas_sync_service
from app.services.canvas_dap import canvas_dap_ingest


router = APIRouter(tags=["Canvas"], prefix="/canvas")


@router.get("/oauth2/authorize")
async def canvas_oauth_authorize(state: str = Query("state"), current_user: User = Depends(get_current_user)):
    url = canvas_auth_service.authorize_url(state=state)
    return RedirectResponse(url)


@router.get("/oauth2/callback")
async def canvas_oauth_callback(code: str, state: str = Query(None), current_user: User = Depends(get_current_user)):
    try:
        tokens = await canvas_auth_service.exchange_code(code)
        await canvas_auth_service.save_tokens(current_user.id, tokens)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/courses")
async def list_courses(db: AsyncSession = Depends(get_async_session), current_user: User = Depends(get_current_user)):
    try:
        data = await canvas_client.list_paginated("/api/v1/courses", user_id=current_user.id)
        return {"courses": data}
    except PermissionError:
        raise HTTPException(status_code=401, detail="Canvas access not authorized for user")


@router.post("/sync/dap")
async def trigger_dap_ingest(current_user: User = Depends(get_current_user)):
    ok = await canvas_dap_ingest.ingest_once()
    return {"started": ok}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/me")
async def canvas_me(current_user: User = Depends(get_current_user)):
    try:
        me = await canvas_client.get_json("/api/v1/users/self/profile", user_id=current_user.id)
        return me
    except PermissionError:
        raise HTTPException(status_code=401, detail="Canvas access not authorized for user")


@router.post("/sync/courses")
async def sync_courses(current_user: User = Depends(get_current_user)):
    try:
        count = await canvas_sync_service.sync_courses(current_user.id)
        return {"synced_courses": count}
    except PermissionError:
        raise HTTPException(status_code=401, detail="Canvas access not authorized for user")


@router.post("/sync/courses/{course_id}/enrollments")
async def sync_course_enrollments(course_id: int, current_user: User = Depends(get_current_user)):
    try:
        n = await canvas_sync_service.sync_course_enrollments(current_user.id, course_id)
        return {"synced_enrollments": n}
    except PermissionError:
        raise HTTPException(status_code=401, detail="Canvas access not authorized for user")


@router.post("/sync/courses/{course_id}/assignments")
async def sync_course_assignments(course_id: int, current_user: User = Depends(get_current_user)):
    try:
        n = await canvas_sync_service.sync_course_assignments(current_user.id, course_id)
        return {"synced_assignments": n}
    except PermissionError:
        raise HTTPException(status_code=401, detail="Canvas access not authorized for user")


@router.post("/sync/courses/{course_id}/assignments/{assignment_id}/submissions")
async def sync_assignment_submissions(course_id: int, assignment_id: int, current_user: User = Depends(get_current_user)):
    try:
        n = await canvas_sync_service.sync_assignment_submissions(current_user.id, course_id, assignment_id)
        return {"synced_submissions": n}
    except PermissionError:
        raise HTTPException(status_code=401, detail="Canvas access not authorized for user")


@router.get("/courses/{course_id}/enrollments")
async def course_enrollments(course_id: int, current_user: User = Depends(get_current_user)):
    try:
        data = await canvas_client.list_paginated(f"/api/v1/courses/{course_id}/enrollments", user_id=current_user.id)
        return {"enrollments": data}
    except PermissionError:
        raise HTTPException(status_code=401, detail="Canvas access not authorized for user")


@router.get("/courses/{course_id}/assignments")
async def course_assignments(course_id: int, current_user: User = Depends(get_current_user)):
    try:
        data = await canvas_client.list_paginated(f"/api/v1/courses/{course_id}/assignments", user_id=current_user.id)
        return {"assignments": data}
    except PermissionError:
        raise HTTPException(status_code=401, detail="Canvas access not authorized for user")


@router.get("/courses/{course_id}/assignments/{assignment_id}/submissions")
async def course_assignment_submissions(course_id: int, assignment_id: int, current_user: User = Depends(get_current_user)):
    try:
        data = await canvas_client.list_paginated(
            f"/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions",
            user_id=current_user.id
        )
        return {"submissions": data}
    except PermissionError:
        raise HTTPException(status_code=401, detail="Canvas access not authorized for user")


