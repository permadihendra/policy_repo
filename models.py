from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from db.database import db


class Policy(db.Model):
    __tablename__ = "policy_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(unique=True)
    content: Mapped[str]
    filename: Mapped[str]
    uploaded_at: Mapped[str]

    def __init__(self, title, content, filename, uploaded_at):
        self.title = title
        self.content = content
        self.filename = filename
        self.uploaded_at = uploaded_at

    def __repr__(self):
        return f"<Policy {self.title!r}>"


# "policy_documents",
# {
#     "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
#     "title": "TEXT",
#     "content": "TEXT",
#     "filename": "TEXT",
#     "uploaded_at": "TEXT",
# },
