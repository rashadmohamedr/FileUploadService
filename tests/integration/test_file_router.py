"""
Integration tests for file router.
Testing file endpoints with real HTTP requests and database interactions.
"""
import pytest
import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.file import File


class TestFileUploadEndpoint:
    """Test /file/upload endpoint."""
    
    def test_upload_file_success(self, client: TestClient, test_user: User, test_upload_dir: str):
        """Test successful file upload via API."""
        file_content = b"Test file content for API upload"
        
        response = client.post(
            "/file/upload",
            files={"file": ("test.pdf", io.BytesIO(file_content), "application/pdf")},
            params={"owner_id": test_user.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.pdf"
        assert "uploaded successfully" in data["message"].lower()
        assert "id" in data
    
    def test_upload_file_creates_database_record(
        self, client: TestClient, test_user: User, test_upload_dir: str, db_session: Session
    ):
        """Test that upload creates database record."""
        file_content = b"Database test content"
        
        response = client.post(
            "/file/upload",
            files={"file": ("database.txt", io.BytesIO(file_content), "text/plain")},
            params={"owner_id": test_user.id}
        )
        
        assert response.status_code == 200
        file_id = response.json()["id"]
        
        # Verify in database
        db_file = db_session.query(File).filter(File.id == file_id).first()
        assert db_file is not None
        assert db_file.uploaded_name == "database.txt"
    
    def test_upload_multiple_files(self, client: TestClient, test_user: User, test_upload_dir: str):
        """Test uploading multiple files sequentially."""
        files = ["file1.txt", "file2.pdf", "file3.jpg"]
        uploaded_ids = []
        
        for filename in files:
            response = client.post(
                "/file/upload",
                files={"file": (filename, io.BytesIO(b"content"), "application/octet-stream")},
                params={"owner_id": test_user.id}
            )
            assert response.status_code == 200
            uploaded_ids.append(response.json()["id"])
        
        # All files should have unique IDs
        assert len(set(uploaded_ids)) == len(files)
    
    def test_upload_file_invalid_extension(self, client: TestClient, test_user: User, test_upload_dir: str):
        """Test that files with invalid extensions are rejected."""
        response = client.post(
            "/file/upload",
            files={"file": ("malware.exe", io.BytesIO(b"bad content"), "application/x-msdownload")},
            params={"owner_id": test_user.id}
        )
        
        assert response.status_code == 400
        assert "not allowed" in response.json()["detail"].lower()
    
    def test_upload_file_too_large(self, client: TestClient, test_user: User, test_upload_dir: str):
        """Test that oversized files are rejected."""
        from app.core.config import settings
        
        # Create file larger than max size
        large_content = b"X" * (settings.MAX_FILE_SIZE + 1000)
        
        response = client.post(
            "/file/upload",
            files={"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")},
            params={"owner_id": test_user.id}
        )
        
        assert response.status_code == 413
    
    def test_upload_file_dangerous_filename(self, client: TestClient, test_user: User, test_upload_dir: str):
        """Test that dangerous filenames are sanitized."""
        response = client.post(
            "/file/upload",
            files={"file": ("../../etc/passwd.pdf", io.BytesIO(b"content"), "application/pdf")},
            params={"owner_id": test_user.id}
        )
        
        # Should succeed after sanitization
        assert response.status_code == 200
        data = response.json()
        # Filename should be sanitized
        assert ".." not in data["filename"]
    
    def test_upload_file_with_unicode_name(self, client: TestClient, test_user: User, test_upload_dir: str):
        """Test uploading file with unicode characters in name."""
        response = client.post(
            "/file/upload",
            files={"file": ("文档.pdf", io.BytesIO(b"content"), "application/pdf")},
            params={"owner_id": test_user.id}
        )
        
        assert response.status_code == 200


class TestFileDownloadEndpoint:
    """Test /file/download/{file_id} endpoint."""
    
    def test_download_file_success(self, client: TestClient, test_file: File, test_user: User):
        """Test successful file download."""
        response = client.get(
            f"/file/download/{test_file.id}",
            params={"owner_id": test_user.id}
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert len(response.content) > 0
    
    def test_download_file_nonexistent(self, client: TestClient, test_user: User):
        """Test downloading non-existent file."""
        response = client.get(
            "/file/download/99999",
            params={"owner_id": test_user.id}
        )
        
        assert response.status_code == 404
    
    
    def test_download_file_wrong_owner(self, client: TestClient, test_file: File, test_admin: User):
        """Test downloading file owned by another user."""
        response = client.get(
            f"/file/download/{test_file.id}",
            params={"owner_id": test_admin.id}
        )
        
        assert response.status_code == 403
    
    def test_download_preserves_original_filename(
        self, client: TestClient, test_user: User, test_upload_dir: str
    ):
        """Test that download uses original filename."""
        # Upload a file
        upload_response = client.post(
            "/file/upload",
            files={"file": ("original_name.pdf", io.BytesIO(b"content"), "application/pdf")},
            params={"owner_id": test_user.id}
        )
        file_id = upload_response.json()["id"]
        
        # Download it
        download_response = client.get(
            f"/file/download/{file_id}",
            params={"owner_id": test_user.id}
        )
        
        assert download_response.status_code == 200
        # Content-Disposition header should include original filename
        content_disp = download_response.headers.get("content-disposition", "")
        assert "original_name.pdf" in content_disp


class TestFileListEndpoint:
    """Test /file/ endpoint for listing files."""
    
    def test_list_files_empty(self, client: TestClient, test_user: User):
        """Test listing files when user has none."""
        response = client.get(
            "/file/",
            params={"owner_id": test_user.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_files_with_files(
        self, client: TestClient, test_user: User, test_upload_dir: str
    ):
        """Test listing files when user has uploaded files."""
        # Upload some files
        for i in range(3):
            client.post(
                "/file/upload",
                files={"file": (f"file{i}.txt", io.BytesIO(b"content"), "text/plain")},
                params={"owner_id": test_user.id}
            )
        
        # List files
        response = client.get(
            "/file/",
            params={"owner_id": test_user.id}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
    
    def test_list_files_pagination(
        self, client: TestClient, test_user: User, test_upload_dir: str
    ):
        """Test file listing pagination."""
        # Upload multiple files
        for i in range(10):
            client.post(
                "/file/upload",
                files={"file": (f"file{i}.txt", io.BytesIO(b"content"), "text/plain")},
                params={"owner_id": test_user.id}
            )
        
        # Get first page
        response = client.get(
            "/file/",
            params={"owner_id": test_user.id, "skip": 0, "limit": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 5
    
    def test_list_files_only_shows_user_files(
        self, client: TestClient, test_user: User, test_admin: User, test_upload_dir: str
    ):
        """Test that users only see their own files."""
        # User uploads files
        client.post(
            "/file/upload",
            files={"file": ("user_file.txt", io.BytesIO(b"user content"), "text/plain")},
            params={"owner_id": test_user.id}
        )
        
        # Admin uploads files
        client.post(
            "/file/upload",
            files={"file": ("admin_file.txt", io.BytesIO(b"admin content"), "text/plain")},
            params={"owner_id": test_admin.id}
        )
        
        # User lists their files
        response = client.get(
            "/file/",
            params={"owner_id": test_user.id}
        )
        
        data = response.json()
        # Verify only user's files are returned
        for file_info in data:
            assert file_info["owner_id"] == test_user.id


class TestFileDeleteEndpoint:
    """Test /file/{file_id} DELETE endpoint."""
    
    def test_delete_file_success(
        self, client: TestClient, test_user: User, test_upload_dir: str
    ):
        """Test successful file deletion."""
        # Upload a file
        upload_response = client.post(
            "/file/upload",
            files={"file": ("to_delete.txt", io.BytesIO(b"content"), "text/plain")},
            params={"owner_id": test_user.id}
        )
        file_id = upload_response.json()["id"]
        
        # Delete it
        delete_response = client.delete(
            f"/file/{file_id}",
            params={"owner_id": test_user.id}
        )
        
        assert delete_response.status_code == 200
    
    def test_delete_file_removes_from_database(
        self, client: TestClient, test_user: User, test_upload_dir: str, db_session: Session
    ):
        """Test that deletion removes file from database."""
        # Upload a file
        upload_response = client.post(
            "/file/upload",
            files={"file": ("db_delete.txt", io.BytesIO(b"content"), "text/plain")},
            params={"owner_id": test_user.id}
        )
        file_id = upload_response.json()["id"]
        
        # Delete it
        client.delete(
            f"/file/{file_id}",
            params={"owner_id": test_user.id}
        )
        
        # Verify not in database
        db_file = db_session.query(File).filter(File.id == file_id).first()
        assert db_file is None
    
    def test_delete_file_nonexistent(self, client: TestClient, test_user: User):
        """Test deleting non-existent file."""
        response = client.delete(
            "/file/99999",
            params={"owner_id": test_user.id}
        )
        
        assert response.status_code == 404
    
    
    def test_delete_file_wrong_owner(self, client: TestClient, test_file: File, test_admin: User):
        """Test deleting file owned by another user."""
        response = client.delete(
            f"/file/{test_file.id}",
            params={"owner_id": test_admin.id}
        )
        
        assert response.status_code == 403
    
    def test_delete_file_twice(
        self, client: TestClient, test_user: User, test_upload_dir: str
    ):
        """Test that deleting same file twice returns error."""
        # Upload and delete
        upload_response = client.post(
            "/file/upload",
            files={"file": ("twice.txt", io.BytesIO(b"content"), "text/plain")},
            params={"owner_id": test_user.id}
        )
        file_id = upload_response.json()["id"]
        
        client.delete(f"/file/{file_id}", params={"owner_id": test_user.id})
        
        # Try to delete again
        response = client.delete(
            f"/file/{file_id}",
            params={"owner_id": test_user.id}
        )
        
        assert response.status_code == 404


class TestFileWorkflows:
    """Test complete file operation workflows."""
    
    def test_upload_download_delete_workflow(
        self, client: TestClient, test_user: User, test_upload_dir: str
    ):
        """Test complete file lifecycle: upload -> download -> delete."""
        file_content = b"Complete workflow test content"
        
        # 1. Upload
        upload_response = client.post(
            "/file/upload",
            files={"file": ("workflow.txt", io.BytesIO(file_content), "text/plain")},
            params={"owner_id": test_user.id}
        )
        assert upload_response.status_code == 200
        file_id = upload_response.json()["id"]
        
        # 2. Download
        download_response = client.get(
            f"/file/download/{file_id}",
            params={"owner_id": test_user.id}
        )
        assert download_response.status_code == 200
        assert download_response.content == file_content
        
        # 3. Delete
        delete_response = client.delete(
            f"/file/{file_id}",
            params={"owner_id": test_user.id}
        )
        assert delete_response.status_code == 200
        
        # 4. Verify deleted
        verify_response = client.get(
            f"/file/download/{file_id}",
            params={"owner_id": test_user.id}
        )
        assert verify_response.status_code == 404
    
    def test_multiple_users_separate_files(
        self, client: TestClient, test_user: User, test_admin: User, test_upload_dir: str
    ):
        """Test that multiple users can upload with isolated storage."""
        # User 1 uploads
        user_response = client.post(
            "/file/upload",
            files={"file": ("user_file.txt", io.BytesIO(b"user content"), "text/plain")},
            params={"owner_id": test_user.id}
        )
        assert user_response.status_code == 200
        
        # User 2 uploads
        admin_response = client.post(
            "/file/upload",
            files={"file": ("admin_file.txt", io.BytesIO(b"admin content"), "text/plain")},
            params={"owner_id": test_admin.id}
        )
        assert admin_response.status_code == 200
        
        # Each user can only see their own files
        user_files = client.get("/file/", params={"owner_id": test_user.id}).json()
        admin_files = client.get("/file/", params={"owner_id": test_admin.id}).json()
        
        user_file_ids = [f["id"] for f in user_files]
        admin_file_ids = [f["id"] for f in admin_files]
        
        # No overlap in file IDs
        assert user_response.json()["id"] in user_file_ids
        assert admin_response.json()["id"] in admin_file_ids
        assert user_response.json()["id"] not in admin_file_ids
        assert admin_response.json()["id"] not in user_file_ids


class TestFileSecurityAndValidation:
    """Test security and validation in file operations."""
    
    def test_upload_with_sql_injection_filename(
        self, client: TestClient, test_user: User, test_upload_dir: str
    ):
        """Test that SQL injection in filename is handled safely."""
        response = client.post(
            "/file/upload",
            files={"file": ("'; DROP TABLE Files; --.txt", io.BytesIO(b"content"), "text/plain")},
            params={"owner_id": test_user.id}
        )
        
        # Should either succeed with sanitized name or handle gracefully
        assert response.status_code in [200, 400]
    
    def test_upload_with_xss_filename(
        self, client: TestClient, test_user: User, test_upload_dir: str
    ):
        """Test that XSS in filename is handled safely."""
        response = client.post(
            "/file/upload",
            files={"file": ("<script>alert('xss')</script>.txt", io.BytesIO(b"content"), "text/plain")},
            params={"owner_id": test_user.id}
        )
        
        if response.status_code == 200:
            # Verify script tags are escaped or removed
            filename = response.json()["filename"]
            assert "<script>" not in filename
    
    @pytest.mark.skip(reason="not implemented yet")
    def test_concurrent_uploads(
        self, client: TestClient, test_user: User, test_upload_dir: str
    ):
        """Test handling of concurrent file uploads."""
        import concurrent.futures
        
        def upload_file(index):
            return client.post(
                "/file/upload",
                files={"file": (f"concurrent{index}.txt", io.BytesIO(b"content"), "text/plain")},
                params={"owner_id": test_user.id} #type: ignore
            )
        
        # Upload files concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(upload_file, i) for i in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All should succeed
        for result in results:
            assert result.status_code == 200
