import re
import sqlite3

import torch
from sentence_transformers import SentenceTransformer, util
from sqlalchemy.engine import result

from db.database import db
from models import Policy

# Load lightweight LLM once
# model = SentenceTransformer("all-MiniLM-L6-v2")
model = SentenceTransformer("distiluse-base-multilingual-cased-v1")


def split_sentences(text):
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="ignore")
    # Split sentences on ., !, ?, or linebreak, keeping sentence length
    return re.findall(r"[^.!?\n]+[.!?\n]", text.strip())


def semantic_search(query, top_k=5):
    rows = db.session.execute(db.select(Policy).order_by(Policy.id)).scalars()

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
        full_text = documents[i]
        sentences = split_sentences(full_text)

        if not sentences:
            excerpt = full_text[:300]
        else:
            sent_embs = model.encode(sentences, convert_to_tensor=True)
            sent_scores = util.pytorch_cos_sim(query_emb, sent_embs)[0]
            top_n = min(10, len(sentences))  # Return 10 Sentence
            top_idxs = torch.topk(sent_scores, k=top_n).indices.tolist()
            top_sentences = [sentences[j] for j in top_idxs]
            excerpt = " ".join(top_sentences)

        results.append(
            {
                "id": ids[i],
                "title": titles[i],
                "score": round(float(score), 4),
                "excerpt": excerpt,
            }
        )

    return results
