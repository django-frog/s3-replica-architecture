from typing import Dict, Any
from app.interfaces.storage import IStorageEngine

class DocumentVaultUseCase:
    def __init__(self, storage_engine: IStorageEngine):
        self.storage_engine = storage_engine

    def store_document(self, file_bytes: bytes, filename: str, classification: str) -> Dict[str, Any]:
        # Standardize object naming paths mimicking AWS folder prefixes
        object_key = f"documents/{classification}/{filename}"

        metadata = {
            "classification": classification,
            "file_name": filename
        }

        success = self.storage_engine.upload_file(file_bytes, object_key, metadata)
        if not success:
            raise RuntimeError("Storage layer failed to persist document stream.")

        return {"object_key": object_key, "status": "persisted"}

    def get_secure_link(self, object_key: str, current_user: dict, expires_in: int) -> str:
        metadata = self.storage_engine.fetch_metadata(object_key)
        file_classification = metadata.get("classification", "public")

        # Evaluate RBAC based on Keycloak token roles
        if file_classification != "public" and file_classification not in current_user["roles"]:
            raise PermissionError(
                f"Access Denied: User '{current_user['username']}' lacks the '{file_classification}' role "
                f"required to view this document."
            )

        # 3. Authorization verified -> generate secure link
        return self.storage_engine.generate_download_url(object_key, expires_in)

    def get_document_details(self, object_key: str) -> Dict[str, str]:
        return self.storage_engine.fetch_metadata(object_key)
