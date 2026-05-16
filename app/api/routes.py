from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, Header, status
from app.infrastructure.minio_storage import MinioStorageEngine
from app.use_cases.document_vault import DocumentVaultUseCase
from app.domain.models import USERS_DB, User
from app.core.config import settings

router = APIRouter(prefix="/v1/documents", tags=["Vault Engine"])

# Dependency Injection Factory
def get_vault_use_case() -> DocumentVaultUseCase:
    storage = MinioStorageEngine()
    return DocumentVaultUseCase(storage)

# Identity Resolver Dependency: Intercepts user context via HTTP Headers
def get_current_user(x_user: str = Header(default="alice")) -> User:
    user = USERS_DB.get(x_user.lower())
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session rejection: Unknown user identity context."
        )
    return user

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    classification: str = Form("internal"),
    use_case: DocumentVaultUseCase = Depends(get_vault_use_case)
):
    file_bytes = await file.read()
    try:
        return use_case.store_document(file_bytes, file.filename, classification)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/download-link")
def get_download_link(
    object_key: str,
    current_user: User = Depends(get_current_user), # Injected user session context
    use_case: DocumentVaultUseCase = Depends(get_vault_use_case)
):
    try:
        url = use_case.get_secure_link(object_key, current_user, settings.URL_EXPIRATION)
        return {"download_url": url}
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

@router.get("/metadata")
def get_metadata(
    object_key: str,
    use_case: DocumentVaultUseCase = Depends(get_vault_use_case)
):
    meta = use_case.get_document_details(object_key)
    if not meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset metadata not found.")
    return {"metadata": meta}
