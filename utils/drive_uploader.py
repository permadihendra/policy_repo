from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Load service account credentials
SERVICE_ACCOUNT_FILE = "credentials/rlegs-collectives-data-6d5ebc5bbd01.json"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]


def upload_to_drive(filepath, filename, folder_id=None):
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build("drive", "v3", credentials=creds)

    file_metadata = {"name": filename}

    if folder_id:
        file_metadata["parents"] = [folder_id]

        media = MediaFileUpload(filepath, mimetype="application/pdf")

        file = (
            service.files()
            .create(body=file_metadata, media_body=media, fields="id")
            .execute()
        )

        return file.get("id")
