import re
import sqlite3

import torch
from sentence_transformers import SentenceTransformer, util
from sqlalchemy.engine import result

from db.database import db_session
from models import Policy

# Load lightweight LLM once
# model = SentenceTransformer("all-MiniLM-L6-v2")
model = SentenceTransformer("distiluse-base-multilingual-cased-v1")


def semantic_search(query, top_k=5):
    rows = Policy.query.all()

    # Filter rows with valid content
    valid_rows = [r for r in rows if r.content]

    documents = [r.content for r in valid_rows]
    titles = [r.title for r in valid_rows]
    ids = [r.id for r in valid_rows]

    if not documents:
        return []  # avoid embedding empty list

    # Encode
    query_emb = model.encode(query, convert_to_tensor=True)
    doc_embs = model.encode(documents, convert_to_tensor=True)

    # Similarity
    scores = util.pytorch_cos_sim(query_emb, doc_embs)[0]
    top_results = scores.topk(min(top_k, len(documents)))

    results = []
    for score, idx in zip(top_results[0], top_results[1]):
        i = int(idx)
        results.append(
            {
                "id": ids[i],
                "title": titles[i],
                "score": float(score),
                "excerpt": documents[i][:300],
            }
        )

    return results
