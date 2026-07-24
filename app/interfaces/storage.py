from abc import ABC, abstractmethod
from typing import Dict, List

class IStorageEngine(ABC):

    @abstractmethod
    async def upload_file(self, file_bytes: bytes, object_key: str, metadata: Dict[str, str]) -> bool:
        """Upload byte stream to the target storage location with system metadata tags."""
        pass

    @abstractmethod
    def generate_download_url(self, object_key: str, expires_in: int) -> str:
        """Generate a secure, time-limited download URL for a specific asset."""
        pass

    @abstractmethod
    async def fetch_metadata(self, object_key: str) -> Dict[str, str]:
        """Retrieve the immutable user-defined metadata dict attached to an object."""
        pass

    @abstractmethod
    async def list_files(self, prefix: str) -> List[str]:
        """List all object keys under a specific S3 prefix."""
        pass
