import sqlite3
from datetime import datetime

from flask import Flask, jsonify, render_template, request, url_for
from flask.helpers import redirect
from pymupdf.mupdf import os
from werkzeug.utils import secure_filename

from db.database import db
from models import Policy
from utils.drive_uploader import upload_to_drive
from utils.file_reader import extract_pdf_text

# from utils.search_engine import semantic_search

app = Flask(
    __name__,
    static_url_path="",
    static_folder="static",
    template_folder="templates",
)

# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///policy_repository.db"
# initialize the app with the extension
db.init_app(app)

UPLOAD_FOLDER = "static/uploads"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload_pdf():
    file = request.files["policy"]
    title = request.form["title"]
    if not file or not file.filename.endswith(".pdf"):
        return {"error": "Invalid file"}, 400
    if file.filename:
        filename = secure_filename(file.filename)
        save_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(save_path)

        # Extract text from PDF
        text = extract_pdf_text(save_path)

        uploaded_at = datetime.utcnow().isoformat()

        data_input = Policy(
            title=title,
            content=text,
            filename=filename,
            uploaded_at=uploaded_at,
        )

        db.session.add(data_input)
        db.session.commit()

        # Upload to Google Drive
        drive_id = upload_to_drive(save_path, filename)

    return redirect(url_for("get_policies"))


@app.route("/policies", methods=["GET"])
def get_policies():
    data = db.session.execute(
        db.select(Policy).order_by(Policy.uploaded_at)
    ).scalars()

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
# @app.route("/search", methods=["GET"])
# def search():
#     query = request.args.get("query")
#     if not query:
#         return jsonify({"error": "Query required"}), 400
#     results = semantic_search(query)
#     return render_template("index.html", results=results)


if __name__ == "__main__":
    app.run(debug=True)
