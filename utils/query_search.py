import re

from sqlalchemy import and_, desc, func, or_

from db.database import db
from models import Policy


def build_keyword_filter(query):
    words = [
        word.strip().lower()
        for word in re.findall(r"\w+", query)
        if len(word.strip()) > 1
    ]

    # Combine title + content as one virtual field
    combined_field = func.concat(Policy.title, " ", Policy.content)

    conditions = [combined_field.ilike(f"%{word}%") for word in words]

    return and_(*conditions) if conditions else True


def query_search(query):
    query = query.strip()

    stmt = (
        db.select(Policy)
        .where(build_keyword_filter(query))
        .order_by(desc(Policy.date))
        .limit(10)
    )
    results = db.session.execute(stmt).scalars().all()

    return results
