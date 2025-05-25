import os
import re
import sqlite3

import torch
from sentence_transformers import util
from sqlalchemy import and_, func, or_
from sqlalchemy.engine import result

from db.database import db
from models import Policy
from semantic_model import SemanticModel


def clean_text(text):
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="ignore")
    text = text.strip()
    text = re.sub(
        r"[^\w\s.,!?]", " ", text
    )  # remove special characters except common punctuation
    text = re.sub(r"[\n\r]+", " ", text)  # remove newlines
    text = re.sub(r"\s+", " ", text)  # normalize spaces
    return text


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


def split_sentences(text):
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="ignore")
    # Split sentences on ., !, ?, or linebreak, keeping sentence length
    return re.findall(r"[^.!?\n]+[.!?\n]", text.strip())


# Query Search with some improvement
# def query_search(query):
#     query = query.strip()

#     stmt = db.select(Policy).where(build_keyword_filter(query))
#     results = db.session.execute(stmt).scalars().all()

#     return results


# SEMANTIC SEARCH with HYBRID Query SQL + LLM Matching Similarity
def semantic_search(query, top_k=5):
    model = SemanticModel.get()
    query = query.strip()

    # Determine if keyword-style query
    is_keyword_like = (
        len(query.split()) <= 3
        or re.search(r"\d{4}", query)
        or re.search(r"\d", query)
    )

    # SQL keyword-based match
    stmt = db.select(Policy).where(build_keyword_filter(query))
    sql_rows = db.session.execute(stmt).scalars().all()
    sql_ids = {r.id for r in sql_rows}

    # Return SQL-only for keyword-like queries
    if is_keyword_like:
        return [
            {
                "id": r.id,
                "title": r.title,
                "score": 1.0,
                "excerpt": r.content[:300],
            }
            for r in sql_rows[:top_k]
        ]

    # Semantic search fallback
    all_rows = db.session.execute(
        db.select(Policy).order_by(Policy.id)
    ).scalars()
    valid_rows = [r for r in all_rows if r.content]

    if not valid_rows:
        return []

    titles = [r.title for r in valid_rows]
    contents = [clean_text(r.content) for r in valid_rows]
    ids = [r.id for r in valid_rows]

    # Blend embeddings
    doc_embs = []
    for title, content in zip(titles, contents):
        title_emb = model.encode(title, convert_to_tensor=True)
        content_emb = model.encode(content, convert_to_tensor=True)
        blended_emb = 0.7 * title_emb + 0.3 * content_emb
        doc_embs.append(blended_emb)

    doc_embs = torch.stack(doc_embs)
    query_emb = model.encode(query, convert_to_tensor=True)

    scores = util.pytorch_cos_sim(query_emb, doc_embs)[0]
    top_results = scores.topk(min(top_k, len(valid_rows)))

    results = []
    for score, idx in zip(top_results[0], top_results[1]):
        i = int(idx)
        full_text = contents[i]
        sentences = split_sentences(full_text)

        if not sentences or float(score) < 0.4:
            excerpt = full_text[:300]
        else:
            sent_embs = model.encode(sentences, convert_to_tensor=True)
            sent_scores = util.pytorch_cos_sim(query_emb, sent_embs)[0]
            top_n = min(10, len(sentences))
            top_idxs = torch.topk(sent_scores, k=top_n).indices.tolist()
            top_idxs.sort()
            top_sentences = [sentences[j] for j in top_idxs]
            excerpt = " ".join(top_sentences)

        result_score = float(score)

        # Hybrid score bonus
        if ids[i] in sql_ids:
            result_score += 0.1
        if query.lower() in full_text.lower():
            result_score += 0.1

        results.append(
            {
                "id": ids[i],
                "title": titles[i],
                "score": round(result_score, 4),
                "excerpt": excerpt,
            }
        )

    return sorted(results, key=lambda x: x["score"], reverse=True)
