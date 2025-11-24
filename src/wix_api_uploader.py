"""Wix API Uploader - Upload PDFs to Wix using REST API.

Uses Wix Media Manager API to upload files without browser automation.
Eliminates need for 2FA OTP - uses API key authentication instead.

Setup:
    1. Get API Key from Wix Dashboard → API Keys Manager
    2. Get Site ID from dashboard URL (appears after '/dashboard/')
    3. Set environment variables:
       export WIX_API_KEY="your-api-key"
       export WIX_SITE_ID="your-site-id"

Workflow:
    1. Create weekly folder (e.g., Week-09) in season folder
    2. Upload PDFs to weekly folder (for archive)
    3. Overwrite Current/Individual.pdf and Current/Overall.pdf
    4. Publish site

Advantages over Selenium:
    - No 2FA required
    - Faster execution
    - More reliable (no UI changes)
    - Simpler error handling
"""

import os
import logging
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional


class WixAPIUploader:
    """Handles PDF uploads to Wix using REST API."""

    BASE_URL = "https://www.wixapis.com"

    def __init__(self, api_key: Optional[str] = None, site_id: Optional[str] = None):
        """
        Initialize Wix API uploader.

        Args:
            api_key: Wix API key (or from WIX_API_KEY env var)
            site_id: Wix Site ID (or from WIX_SITE_ID env var)
        """
        self.api_key = api_key or os.getenv("WIX_API_KEY")
        self.site_id = site_id or os.getenv("WIX_SITE_ID")
        self.logger = logging.getLogger(__name__)

        if not self.api_key:
            raise ValueError(
                "Wix API key required. Set WIX_API_KEY environment variable.\n"
                "Get it from: https://manage.wix.com/account/api-keys"
            )

        if not self.site_id:
            raise ValueError(
                "Wix Site ID required. Set WIX_SITE_ID environment variable.\n"
                "Find it in your dashboard URL after '/dashboard/'"
            )

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": self.api_key,
                "wix-site-id": self.site_id,
                "Content-Type": "application/json",
            }
        )

        self.logger.info("✅ Wix API uploader initialized")

    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Make authenticated API request.

        Args:
            method: HTTP method (GET, POST, PUT, etc.)
            endpoint: API endpoint path
            **kwargs: Additional arguments for requests

        Returns:
            Response object

        Raises:
            requests.HTTPError: If request fails
        """
        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.HTTPError as e:
            self.logger.error(f"❌ API request failed: {method} {endpoint}")
            self.logger.error(f"Status: {e.response.status_code}")
            self.logger.error(f"Response: {e.response.text}")
            raise

    def list_folders(self, parent_folder_id: Optional[str] = None) -> List[Dict]:
        """
        List folders in Media Manager.

        Args:
            parent_folder_id: Parent folder to list from (None = root)

        Returns:
            List of folder objects
        """
        self.logger.debug(f"Listing folders in {parent_folder_id or 'root'}")

        # Build query parameters
        params = {}
        if parent_folder_id and parent_folder_id != "media-root":
            params["parentFolderId"] = parent_folder_id

        response = self._make_request("GET", "/site-media/v1/folders", params=params)

        result = response.json()
        folders = result.get("folders", [])
        self.logger.debug(f"Found {len(folders)} folder(s)")
        return folders

    def get_folder_by_name(
        self, folder_name: str, parent_folder_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Find folder by name within parent folder.

        Args:
            folder_name: Name of folder to find
            parent_folder_id: Parent folder to search in (None = root)

        Returns:
            Folder object if found, None otherwise
        """
        folders = self.list_folders(parent_folder_id)

        for folder in folders:
            if folder.get("displayName") == folder_name:
                return folder

        return None

    def create_folder(
        self, folder_name: str, parent_folder_id: str = "media-root"
    ) -> Dict:
        """
        Create a new folder in Media Manager.

        Args:
            folder_name: Name for the new folder
            parent_folder_id: Parent folder ID (default: media-root)

        Returns:
            Created folder object with id, displayName, etc.
        """
        self.logger.info(f"Creating folder: {folder_name}")

        payload = {"displayName": folder_name}

        if parent_folder_id and parent_folder_id != "media-root":
            payload["parentFolderId"] = parent_folder_id

        response = self._make_request("POST", "/site-media/v1/folders", json=payload)

        folder = response.json().get("folder", {})
        folder_id = folder.get("id")

        self.logger.info(f"✅ Created folder: {folder_name} (ID: {folder_id})")
        return folder

    def ensure_folder_path(self, folder_path: List[str]) -> str:
        """
        Ensure folder path exists, creating folders as needed.

        Args:
            folder_path: List of folder names (e.g., ['SEASON 74 - 2025 Fall', 'Week-09'])

        Returns:
            ID of the deepest folder
        """
        parent_id = "media-root"

        for folder_name in folder_path:
            # Check if folder exists
            folder = self.get_folder_by_name(folder_name, parent_id)

            if folder:
                parent_id = folder["id"]
                self.logger.debug(f"Found existing folder: {folder_name}")
            else:
                # Create folder
                folder = self.create_folder(folder_name, parent_id)
                parent_id = folder["id"]

        return parent_id

    def list_files(self, parent_folder_id: str) -> List[Dict]:
        """
        List files in a folder.

        Args:
            parent_folder_id: Parent folder to list files from

        Returns:
            List of file objects
        """
        self.logger.debug(f"Listing files in folder {parent_folder_id}")

        params = {}
        if parent_folder_id and parent_folder_id != "media-root":
            params["parentFolderId"] = parent_folder_id

        response = self._make_request("GET", "/site-media/v1/files", params=params)

        result = response.json()
        files = result.get("files", [])
        self.logger.debug(f"Found {len(files)} file(s)")
        return files

    def delete_files(self, file_ids: List[str], permanent: bool = False) -> bool:
        """
        Delete files by IDs using bulk delete API.

        Args:
            file_ids: List of file IDs to delete
            permanent: If True, permanently delete (can't restore). Default: move to trash.

        Returns:
            True if successful
        """
        if not file_ids:
            return True  # Nothing to delete

        self.logger.debug(f"Bulk deleting {len(file_ids)} file(s)")

        try:
            payload = {"fileIds": file_ids}
            if permanent:
                payload["permanent"] = True

            self._make_request("POST", "/site-media/v1/bulk/files/delete", json=payload)
            self.logger.debug(f"✅ Deleted {len(file_ids)} file(s)")
            return True
        except Exception as e:
            self.logger.error(f"❌ Failed to delete files: {e}")
            return False

    def delete_files_by_name(
        self, folder_id: str, filename: str, permanent: bool = False
    ) -> int:
        """
        Delete all files with a specific name in a folder.

        Args:
            folder_id: Folder to search in
            filename: Display name to match
            permanent: If True, permanently delete. Default: move to trash.

        Returns:
            Number of files deleted
        """
        files = self.list_files(folder_id)
        file_ids_to_delete = []

        for file in files:
            if file.get("displayName") == filename:
                file_ids_to_delete.append(file.get("id"))

        if file_ids_to_delete:
            if self.delete_files(file_ids_to_delete, permanent):
                self.logger.info(
                    f"🗑️  Deleted {len(file_ids_to_delete)} existing file(s) named '{filename}'"
                )
                return len(file_ids_to_delete)

        return 0

    def generate_upload_url(
        self, filename: str, parent_folder_id: str, mime_type: str = "application/pdf"
    ) -> Dict:
        """
        Generate an upload URL for a file.

        Args:
            filename: Display name for the file
            parent_folder_id: Folder to upload to
            mime_type: MIME type of file

        Returns:
            Dict with uploadUrl and fileId
        """
        self.logger.debug(f"Generating upload URL for: {filename}")

        payload = {"mimeType": mime_type, "displayName": filename}

        if parent_folder_id and parent_folder_id != "media-root":
            payload["parentFolderId"] = parent_folder_id

        response = self._make_request(
            "POST", "/site-media/v1/files/generate-upload-url", json=payload
        )

        result = response.json()
        upload_url = result.get("uploadUrl")

        self.logger.debug(f"Got upload URL for {filename}")
        return result

    def upload_file_to_url(
        self, file_path: Path, upload_url: str, display_name: str
    ) -> bool:
        """
        Upload file bytes to generated upload URL.

        Args:
            file_path: Path to file to upload
            upload_url: Pre-signed upload URL from generate_upload_url
            display_name: Filename to use in upload (e.g., "Individual.pdf")

        Returns:
            True if successful
        """
        self.logger.info(f"Uploading {file_path.name} as {display_name}...")

        try:
            # Try multipart form upload (common for file uploads)
            # Use display_name instead of file_path.name
            with open(file_path, "rb") as f:
                files = {"file": (display_name, f, "application/pdf")}
                response = requests.post(upload_url, files=files)

            # If that fails, try direct PUT
            if response.status_code >= 400:
                self.logger.debug("Multipart failed, trying direct PUT...")
                with open(file_path, "rb") as f:
                    response = requests.put(
                        upload_url,
                        data=f,
                        headers={"Content-Type": "application/octet-stream"},
                    )

            response.raise_for_status()

            self.logger.info(f"✅ Uploaded {file_path.name}")
            return True

        except Exception as e:
            self.logger.error(f"❌ Upload failed for {file_path.name}: {e}")
            self.logger.debug(
                f"Response status: {response.status_code if 'response' in locals() else 'N/A'}"
            )
            self.logger.debug(
                f"Response body: {response.text[:500] if 'response' in locals() else 'N/A'}"
            )
            return False

    def upload_file(
        self, file_path: Path, folder_id: str, display_name: Optional[str] = None
    ) -> bool:
        """
        Complete file upload workflow: generate URL, upload file, wait for processing.

        Args:
            file_path: Path to file to upload
            folder_id: Destination folder ID
            display_name: Optional display name (defaults to filename)

        Returns:
            True if successful, False otherwise
        """
        display_name = display_name or file_path.name

        # Generate upload URL
        upload_info = self.generate_upload_url(display_name, folder_id)
        upload_url = upload_info.get("uploadUrl")

        if not upload_url:
            self.logger.error("Failed to generate upload URL")
            return False

        # Upload file
        if not self.upload_file_to_url(file_path, upload_url, display_name):
            return False

        # Wait a moment for processing
        time.sleep(2)

        return True

    def publish_site(self) -> bool:
        """
        Publish the site to make changes live.

        Returns:
            True if successful
        """
        self.logger.info("🚀 Publishing site...")

        try:
            response = self._make_request("POST", "/site-publisher/v1/site/publish")

            self.logger.info("✅ Site published successfully!")
            return True

        except Exception as e:
            self.logger.error(f"❌ Publish failed: {e}")
            return False

    def upload_weekly_pdfs(
        self,
        individual_pdf: Path,
        overall_pdf: Path,
        week_number: int,
        season_name: str = "SEASON 74 - 2025 Fall",
    ) -> bool:
        """
        Complete workflow: upload PDFs to weekly folder and Current/ folder, then publish.

        Strategy:
        1. Create/ensure season folder exists
        2. Create/ensure Current/ folder exists
        3. Create weekly folder (Week-XX)
        4. Upload PDFs to weekly folder (archive)
        5. Overwrite Current/Individual.pdf
        6. Overwrite Current/Overall.pdf
        7. Publish site

        Args:
            individual_pdf: Path to Individual PDF
            overall_pdf: Path to Overall PDF
            week_number: Week number (e.g., 9 for Week-09)
            season_name: Season folder name

        Returns:
            True if entire workflow successful
        """
        try:
            week_folder_name = f"Week-{week_number:02d}"

            # Ensure season folder exists
            self.logger.info("📁 Ensuring folder structure exists...")
            season_folder_id = self.ensure_folder_path([season_name])

            # Ensure Current/ folder exists (for icons to link to)
            current_folder_id = self.ensure_folder_path([season_name, "Current"])

            # Create/get weekly folder
            week_folder_id = self.ensure_folder_path([season_name, week_folder_name])

            # Upload to weekly folder (archive)
            self.logger.info(f"📤 Uploading to {week_folder_name}/ (archive)...")
            if not self.upload_file(
                individual_pdf, week_folder_id, f"Individual-Week{week_number:02d}.pdf"
            ):
                return False
            if not self.upload_file(
                overall_pdf, week_folder_id, f"Overall-Week{week_number:02d}.pdf"
            ):
                return False

            # Upload to Current/ folder (what icons link to)
            self.logger.info("📤 Uploading to Current/ (icon targets)...")

            # Delete old files to avoid confusion (keeps only latest files)
            # NOTE: Wix icons link by file ID - deleting creates new IDs
            # MANUAL STEP REQUIRED: Re-link icons in editor after upload (~30 seconds)
            self.delete_files_by_name(
                current_folder_id, "Individual.pdf", permanent=True
            )
            self.delete_files_by_name(current_folder_id, "Overall.pdf", permanent=True)

            if not self.upload_file(
                individual_pdf, current_folder_id, "Individual.pdf"
            ):
                return False
            if not self.upload_file(overall_pdf, current_folder_id, "Overall.pdf"):
                return False

            # Publish site
            if not self.publish_site():
                return False

            self.logger.info("✅ Upload workflow completed successfully!")
            return True

        except Exception as e:
            self.logger.error(f"❌ Upload workflow failed: {e}")
            return False
