from fastapi import APIRouter, HTTPException, status, Request, Depends, UploadFile, File

from sqlmodel import select
from models import *
from database import DbSession
from typing import List
from fastapi.responses import FileResponse


import os
from utils import *
from shutil import copyfileobj
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

memo_router = APIRouter(prefix="/memo", tags=["memo"])
security = HTTPBasic()

load_dotenv("secrets.env")


def verify_upload_user(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = os.getenv("UPLOAD_USERNAME")
    passwords_match = bcrypt.checkpw(
        credentials.password.encode('utf-8'),hash
    )
    if not (
        secrets.compare_digest(credentials.username, correct_username)
        and passwords_match
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


# Create a new memo
@memo_router.post(
    "/upload",
    response_model=MemoRead,
    dependencies=[Depends(verify_upload_user)],
    status_code=status.HTTP_201_CREATED,
)
async def create_memo(
    db: DbSession,
    file: UploadFile = File(...),
    memo: MemoCreate = Depends(MemoCreate.as_form),
) -> MemoRead:
    """
    Upload a new memo PDF file with metadata.
    Only valid PDF files under 10 MB are accepted.
    """

    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, detail="File exceeds maximum allowed size (10 MB)"
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, detail="File exceeds maximum allowed size (10 MB)"
        )

    if not content.startswith(b"%PDF"):
        raise HTTPException(status_code=400, detail="Invalid PDF file")

    # Reset file pointer for saving
    await file.seek(0)

    # name = os.path.splitext(file.filename)[0]

    # rename the file using its original name (without extension) plus a timestamp, and sets the .pdf extension.
    new_file_name = "{}_{}.pdf".format(
        sanitize_filename(os.path.splitext(file.filename)[0]), timestr
    )
    save_path = os.path.join(UPLOAD_DIR, new_file_name)

    # saves the uploaded file to disk.
    try:
        with open(save_path, "wb") as buffer:
            copyfileobj(file.file, buffer)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

    db_memo = Memo(
        title=memo.title.strip().title(),
        file_name=new_file_name,
        tags=memo.tags or "public",
        file_path=os.path.join("memo_uploads", new_file_name),  # ← Save relative path
    )
    try:
        db.add(db_memo)
        db.commit()
        db.refresh(db_memo)
    except SQLAlchemyError:
        db.rollback()
        if os.path.exists(save_path):
            os.remove(save_path)
        raise HTTPException(status_code=500, detail="Database error")

    return MemoRead(title=db_memo.title, file_name=db_memo.file_name, tags=db_memo.tags)


@memo_router.get("/memos", response_model=List[MemoListItem])
async def get_memos(db: DbSession, request: Request):
    """
    Returns a list of all public and non-archived memos with download links
    """
    memos = db.exec(
        select(Memo).where(Memo.is_archived == False, Memo.tags == "public")
    ).all()

    # Gets the base URL of the current request (e.g., http://127.0.0.1:8000/) without any trailing slash /
    base_url = str(request.base_url).rstrip("/")

    return [
        MemoListItem(
            id=m.id,
            title=m.title,
            uploaded_at=m.uploaded_at,
            download_url=f"{base_url}/memo/{m.id}/pdf",
            download_name=m.file_name,  # download_url labelled using download_name
        )
        for m in memos
    ]


@memo_router.get(
    "/memos/search/{query}",
    response_model=List[MemoListItem],
    status_code=status.HTTP_200_OK,
)
async def search_memos(query: str, db: DbSession, request: Request = None):
    """
    Search memos by title or file name (case-insensitive).
    Returns only non-archived and public memos.
    """
    query_str = f"%{query.lower()}%"

    stmt = select(Memo).where(
        Memo.is_archived == False,
        Memo.tags == "public",
        or_(Memo.title.ilike(query_str), Memo.file_name.ilike(query_str)),
    )

    results = db.exec(stmt).all()

    if not results:
        raise HTTPException(
            status_code=404, detail="No memos found matching your search."
        )

    base_url = str(request.base_url).rstrip("/")

    return [
        MemoListItem(
            id=m.id,
            title=m.title,
            uploaded_at=m.uploaded_at,
            download_url=f"{base_url}/memo/{m.id}/pdf",
            download_name=m.file_name,
        )
        for m in results
    ]


@memo_router.get("/{memo_id}/pdf")
async def download_pdf(memo_id: int, db: DbSession):
    """
    Download a specific memo PDF by ID.
    Only available for public and non-archived memos.
    """
    memo = db.get(Memo, memo_id)
    if not memo:
        raise HTTPException(status_code=404, detail="Memo not found")

    if memo.is_archived or memo.tags != "public":
        raise HTTPException(status_code=403, detail="Access denied")

    full_path = os.path.join(BASE_DIR, memo.file_path)
    if not memo or not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=full_path, media_type="application/pdf", filename=memo.file_name
    )

# update a memo
@memo_router.patch(
    "/{memo_id}",
    response_model=MemoRead,
    dependencies=[Depends(verify_upload_user)],
    status_code=status.HTTP_200_OK,
)
async def update_memo(
    memo_id: int,
    db: DbSession,
    updated_memo: MemoUpdate = Depends(MemoUpdate.as_form),
):
    """
    Update a memo’s title, tag, or filename.
    Only the provided fields will be changed.
    """
    memo = db.get(Memo, memo_id)
    if not memo:
        raise HTTPException(status_code=404, detail="Memo not found")

    if updated_memo.title:
        memo.title = updated_memo.title.strip().title()

    if updated_memo.tags:
        memo.tags = updated_memo.tags

    if updated_memo.file_name:
        memo.file_name = "{}_{}.pdf".format(
            os.path.splitext(updated_memo.file_name)[0], timestr
        )

    db.add(memo)
    db.commit()
    db.refresh(memo)

    return memo


# Delete a memo
@memo_router.delete(
    "/{memo_id}",
    dependencies=[Depends(verify_upload_user)],
    status_code=status.HTTP_200_OK,
)
async def delete_memo(memo_id: int, db: DbSession):
    """Soft delete a memo by marking it as archived."""
    memo = db.get(Memo, memo_id)
    if not memo:
        raise HTTPException(status_code=404, detail="Memo not found")

    memo.is_archived = True
    db.add(memo)
    db.commit()

    return {"message": f"{memo.title} deleted successfully."}
