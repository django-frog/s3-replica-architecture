import asyncio
import logging
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError

from app.core.config import settings
from app.infrastructure.minio_storage import MinioStorageEngine

logger = logging.getLogger(__name__)

async def seed_sandbox():
    """
    Automated sandbox initialization for SnapDeploy free-tier containers.
    Creates demo Keycloak users and dummy MinIO documents upon wake-up.
    """
    logger.info("Initializing Sandbox Seeder...")

    # 1. Seed Keycloak Identity Provider
    try:
        # Connect to the local Keycloak Admin API
        keycloak_admin = KeycloakAdmin(
            server_url=settings.KEYCLOAK_URL,
            username="admin",        # Make sure these match your container ENV
            password="admin",
            realm_name="master",
            verify=True,
        )

        # Switch to your application's realm
        keycloak_admin.realm_name = settings.KEYCLOAK_REALM

        demo_user = {
            "email": "recruiter@demo.com",
            "username": "recruiter@demo.com",
            "enabled": True,
            "firstName": "Senior",
            "lastName": "Recruiter",
            "credentials": [{"value": "hireme123", "type": "password"}],
        }

        # Create user via the API (exist_ok=True prevents crashes if the container didn't fully sleep)
        # Using a threaded execution since KeycloakAdmin is synchronous
        await asyncio.to_thread(keycloak_admin.create_user, demo_user, exist_ok=True)
        logger.info("Demo user 'recruiter@demo.com' successfully seeded.")

    except KeycloakError as e:
        logger.warning(f"Keycloak seeding skipped or failed: {e}")

    # 2. Seed MinIO Object Storage
    try:
        storage_engine = MinioStorageEngine()

        # MinioStorageEngine.__init__ already calls _ensure_bucket_exists()
        # So we just need to upload a dummy file
        dummy_file_bytes = b"Welcome to the Cloud-Native Object Storage Demo!"
        metadata = {"Author": "Mohammad", "Project": "S3-Replica Sandbox"}

        await storage_engine.upload_file(
            file_bytes=dummy_file_bytes,
            object_key="welcome-document.txt",
            metadata=metadata
        )
        logger.info("Demo document 'welcome-document.txt' successfully seeded in MinIO.")

    except Exception as e:
        logger.error(f"MinIO seeding failed: {e}")
