from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status
from app.infrastructure.minio_storage import MinioStorageEngine
from app.use_cases.document_vault import DocumentVaultUseCase
from app.core.config import settings
from app.core.security import get_current_user
from typing import Dict, Any

router = APIRouter(prefix="/v1/documents", tags=["Vault Engine"])

# Dependency Injection Factory
def get_vault_use_case() -> DocumentVaultUseCase:
    storage = MinioStorageEngine()
    return DocumentVaultUseCase(storage)

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    classification: str = Form("internal"),
    current_user: Dict[str, Any] = Depends(get_current_user), # Secure upload route
    use_case: DocumentVaultUseCase = Depends(get_vault_use_case)
):
    if classification != "public" and classification not in current_user["roles"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You lack clearance to upload {classification} files."
        )

    file_bytes = await file.read()

    # Extract the username from the validated Keycloak token
    publisher_name = current_user.get("username", "unknown")

    try:
        # Pass the publisher_name down to the Use Case
        return await use_case.store_document(file_bytes, file.filename, classification, publisher_name)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/download-link")
async def get_download_link(
    object_key: str,
    current_user: Dict[str, Any] = Depends(get_current_user), # Injects the JWT payload
    use_case: DocumentVaultUseCase = Depends(get_vault_use_case)
):
    try:
        url = await use_case.get_secure_link(object_key, current_user, settings.URL_EXPIRATION)
        return {"download_url": url}
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get("/metadata")
async def get_metadata(
    object_key: str,
    use_case: DocumentVaultUseCase = Depends(get_vault_use_case)
):
    meta = await use_case.get_document_details(object_key)
    if not meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset metadata not found.")
    return {"metadata": meta}

@router.get("/list")
async def list_documents(
    current_user: Dict[str, Any] = Depends(get_current_user),
    use_case: DocumentVaultUseCase = Depends(get_vault_use_case)
):
    try:
        keys = await use_case.list_accessible_documents(current_user)
        return {"files": keys}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
