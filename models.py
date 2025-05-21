from sqlalchemy import Column, Integer, String
from sqlalchemy.dialects.mysql import LONGTEXT

from db.database import Base


class Policy(Base):
    __tablename__ = "policy_documents"
    id = Column(Integer, primary_key=True)
    title = Column(String(120), unique=True)
    content = Column(LONGTEXT)
    filename = Column(String(20))
    uploaded_at = Column(String(20))

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
