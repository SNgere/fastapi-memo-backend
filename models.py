from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from forms import as_form
from fastapi import Form


class Memo(SQLModel, table=True):
    "Memo table"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    file_name: str
    file_path: str
    uploaded_at: datetime = Field(
        default_factory=lambda: datetime.now().replace(second=0, microsecond=0),
        nullable=False,
    )
    tags: str = Field(default="public")
    is_archived: bool = Field(default=False)


@as_form
class MemoCreate(SQLModel):
    title: str
    tags: Optional[str] = "public"


class MemoRead(SQLModel):
    title: str
    file_name: str
    tags: str


@as_form
class MemoUpdate(SQLModel):
    title: Optional[str] = Form(None)
    file_name: Optional[str] = Form(None)
    tags: Optional[str] = Form(None)


class MemoListItem(SQLModel):
    id: int
    title: str
    uploaded_at: datetime
    download_url: str
    download_name: str

    # compare home page with that of heroes

    # If uploads should persist, back up or mount the uploads folder on the host or a shared volume.
    # checkout best ways to backup up the memos in a production server

    # handling multiple outputs

    # add file size
    # deadlines
    # pin a memo
    # Add pagination to avoid loading all memos
