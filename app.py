import sqlite3
from datetime import datetime

from cleantext import clean
from flask import Flask, flash, jsonify, render_template, request, url_for
from flask.helpers import redirect
from httplib2 import Response
from pymupdf.mupdf import os
from sqlalchemy.exc import IntegrityError
from werkzeug.utils import secure_filename

from db.database import db
from models import Policy
from utils.drive_uploader import upload_to_drive
from utils.file_reader import extract_pdf_text
from utils.search_engine import semantic_search

app = Flask(
    __name__,
    static_url_path="",
    static_folder="static",
    template_folder="templates",
)

app.secret_key = "KMZWA8AWAA"  # ← required for flash, session, CSRF

# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///policy_repository.db"
# initialize the app with the extension
db.init_app(app)

UPLOAD_FOLDER = "static/uploads"


@app.route("/")
def index():
    return redirect(url_for("get_policies"))


@app.route("/upload", methods=["POST"])
def upload_pdf():
    file = request.files["policy"]
    title = request.form["title"]

    # Simple validation
    if not title or not file:
        return jsonify(
            {"success": False, "error": "Title and file are required"}
        ), 400

    # Optional: check file type
    if not file.filename.lower().endswith(".pdf"):
        return jsonify(
            {"success": False, "error": "Only PDF files are allowed"}
        ), 400

    if file.filename:
        if not file or not file.filename.endswith(".pdf"):
            return jsonify({"error": "Invalid file"}), 400

        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)

        # Extract text from PDF
        text = extract_pdf_text(save_path)

        # Clean the text
        cleaned_text = clean(
            text,
            fix_unicode=True,
            to_ascii=False,
            lower=False,
            no_line_breaks=True,
            no_urls=True,
            no_emails=True,
            no_phone_numbers=True,
            no_numbers=False,
            no_digits=False,
            no_currency_symbols=True,
            no_punct=False,
            replace_with_punct="",
            replace_with_url="",
            replace_with_email="",
            replace_with_phone_number="",
            replace_with_number="",
            replace_with_digit="",
            replace_with_currency_symbol="",
        )

        uploaded_at = datetime.utcnow().isoformat()

        data_input = Policy(
            title=title,
            content=cleaned_text,
            filename=filename,
            uploaded_at=uploaded_at,
        )
        try:
            db.session.add(data_input)
            db.session.commit()
            return jsonify(success=True), 200
        except IntegrityError:
            db.session.rollback()
            return jsonify(
                success=False, error="Policy title already exists"
            ), 409

        # Upload to Google Drive
        drive_id = upload_to_drive(save_path, filename)

    return jsonify({"success": True})


@app.route("/policies", methods=["GET"])
def get_policies():
    # data = db.session.execute(
    #     db.select(Policy).order_by(Policy.uploaded_at)
    # ).scalars()
    data = db.paginate(
        db.select(Policy).order_by(Policy.uploaded_at.desc()), per_page=10
    )

    return render_template("index.html", policies=data)


@app.route("/policy/<int:id>/delete", methods=["GET", "POST"])
def delete_policy(id):
    policy = db.get_or_404(Policy, id)

    file_path = os.path.join(UPLOAD_FOLDER, policy.filename)

    if request.method == "POST":
        # execute delele file
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Deleted: {file_path}")
        else:
            print(f"File not found: {file_path}")

        # execute delete data on database
        db.session.delete(policy)
        db.session.commit()
        return jsonify({"redirect_url": url_for("get_policies")})

    return jsonify({"redirect_url": url_for("get_policies")})


# temporary shutdown search for fast reloading
@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query")
    if not query:
        return jsonify({"error": "Query required"}), 400
    results = semantic_search(query)
    return render_template("index.html", results=results)


if __name__ == "__main__":
    app.run(debug=True)
