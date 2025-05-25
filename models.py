from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from db.database import db


class Policy(db.Model):
    __tablename__ = "policy_documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(unique=True)
    content: Mapped[str] = mapped_column(Text)  # new added
    filename: Mapped[str]
    uploaded_at: Mapped[str]
    number: Mapped[str] = mapped_column(
        String(100), nullable=True
    )  # New added later
    date: Mapped[str] = mapped_column(
        String(20), nullable=True
    )  # New added later

    def __init__(self, title, content, filename, uploaded_at, number, date):
        self.title = title
        self.content = content
        self.filename = filename
        self.uploaded_at = uploaded_at
        self.number = number  # New added later
        self.date = date  # New added later

    def __repr__(self):
        return f"<Policy {self.title!r}>"
