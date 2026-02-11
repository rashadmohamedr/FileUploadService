"""
Unit tests for file service.
Testing file upload, download, and delete operations with database interactions.
"""
import pytest
import os
import io
import tempfile
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.services.file_service import (
    save_upload,
    delete_file,
    download_file,
    update_total_storage_used_incrementally,
    update_total_storage_used_decrementally
)
from app.models.file import File
from app.models.user import User
from app.models.analytics_event import AnalyticsEvent
from app.core.config import settings


class TestSaveUpload:
    """Test file upload functionality."""
    
    def test_save_upload_success(self, db_session: Session, test_user: User, test_upload_dir: str):
        """Test successful file upload."""
        content = b"Test file content for upload"
        upload_file = UploadFile(
            filename="test.pdf",
            file=io.BytesIO(content)
        )
        
        response = save_upload(db_session, upload_file, test_user.id)
        
        assert response.status_code == 200
        response_data = response.body.decode()
        assert "File uploaded successfully" in response_data
        assert "test.pdf" in response_data
    
    def test_save_upload_creates_database_record(self, db_session: Session, test_user: User, test_upload_dir: str):
        """Test that upload creates database record."""
        content = b"Test content"
        upload_file = UploadFile(
            filename="document.pdf",
            file=io.BytesIO(content)
        )
        
        save_upload(db_session, upload_file, test_user.id)
        
        # Verify file exists in database
        db_file = db_session.query(File).filter(File.owner_id == test_user.id).first()
        assert db_file is not None
        assert db_file.uploaded_name == "document.pdf"
        assert db_file.owner_id == test_user.id
    
    def test_save_upload_creates_physical_file(self, db_session: Session, test_user: User, test_upload_dir: str):
        """Test that upload creates physical file on disk."""
        content = b"Physical file content"
        upload_file = UploadFile(
            filename="physical.txt",
            file=io.BytesIO(content)
        )
        
        save_upload(db_session, upload_file, test_user.id)
        
        # Verify file exists on disk
        db_file = db_session.query(File).filter(File.owner_id == test_user.id).first()
        assert os.path.exists(db_file.path)
        
        # Verify content
        with open(db_file.path, "rb") as f:
            assert f.read() == content
    
    def test_save_upload_generates_unique_filename(self, db_session: Session, test_user: User, test_upload_dir: str):
        """Test that uploaded files get unique UUID-based names."""
        content = b"Content"
        upload_file = UploadFile(
            filename="same_name.pdf",
            file=io.BytesIO(content)
        )
        
        save_upload(db_session, upload_file, test_user.id)
        save_upload(db_session, upload_file, test_user.id)
        
        files = db_session.query(File).filter(File.owner_id == test_user.id).all()
        
        # Both files have same original name but different saved names
        assert len(files) == 2
        assert files[0].uploaded_name == files[1].uploaded_name
        assert files[0].saved_name != files[1].saved_name
    
    def test_save_upload_updates_user_storage(self, db_session: Session, test_user: User, test_upload_dir: str):
        """Test that upload updates user's storage usage."""
        initial_storage = test_user.total_storage_used
        content = b"X" * 1024  # 1KB
        upload_file = UploadFile(
            filename="storage_test.pdf",
            file=io.BytesIO(content)
        )
        
        save_upload(db_session, upload_file, test_user.id)
        
        db_session.refresh(test_user)
        assert test_user.total_storage_used > initial_storage
    
    def test_save_upload_creates_analytics_event(self, db_session: Session, test_user: User, test_upload_dir: str):
        """Test that upload creates analytics event."""
        events_before = db_session.query(AnalyticsEvent).count()
        
        content = b"Test content"
        upload_file = UploadFile(
            filename="analytics_test.pdf",
            file=io.BytesIO(content)
        )
        
        save_upload(db_session, upload_file, test_user.id)
        
        events_after = db_session.query(AnalyticsEvent).count()
        assert events_after == events_before + 1
        
        # Verify event details
        event = db_session.query(AnalyticsEvent).order_by(
            AnalyticsEvent.timestamp.desc()
        ).first()
        assert event.event_type == "file_upload"
        assert event.user_id == test_user.id
    
    def test_save_upload_no_filename_raises_error(self, db_session: Session, test_user: User, test_upload_dir: str):
        """Test that upload without filename raises error."""
        upload_file = UploadFile(
            filename=None,
            file=io.BytesIO(b"content")
        )
        
        with pytest.raises(HTTPException) as exc_info:
            save_upload(db_session, upload_file, test_user.id)
        
        assert exc_info.value.status_code == 400
        assert "Filename is required" in str(exc_info.value.detail)
    
    def test_save_upload_sanitizes_dangerous_filename(self, db_session: Session, test_user: User, test_upload_dir: str):
        """Test that dangerous filenames are sanitized."""
        content = b"content"
        upload_file = UploadFile(
            filename="../../etc/passwd.pdf",
            file=io.BytesIO(content)
        )
        
        save_upload(db_session, upload_file, test_user.id)
        
        db_file = db_session.query(File).filter(File.owner_id == test_user.id).first()
        # Sanitized filename should not contain path traversal
        assert ".." not in db_file.uploaded_name
        assert "/" not in db_file.uploaded_name or db_file.uploaded_name == "passwd.pdf"
    
    def test_save_upload_rejects_oversized_file(self, db_session: Session, test_user: User, test_upload_dir: str):
        """Test that files exceeding size limit are rejected."""
        large_content = b"X" * (settings.MAX_FILE_SIZE + 1000)
        upload_file = UploadFile(
            filename="large.pdf",
            file=io.BytesIO(large_content)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            save_upload(db_session, upload_file, test_user.id)
        
        assert exc_info.value.status_code == 413
    
    def test_save_upload_rejects_invalid_extension(self, db_session: Session, test_user: User, test_upload_dir: str):
        """Test that files with invalid extensions are rejected."""
        content = b"malicious content"
        upload_file = UploadFile(
            filename="malware.exe",
            file=io.BytesIO(content)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            save_upload(db_session, upload_file, test_user.id)
        
        assert exc_info.value.status_code == 400
    
    def test_save_upload_rollback_on_error(self, db_session: Session, test_user: User, test_upload_dir: str):
        """Test that upload is rolled back on error."""
        # Create a scenario that will fail (oversized file)
        large_content = b"X" * (settings.MAX_FILE_SIZE + 1000)
        upload_file = UploadFile(
            filename="fail.pdf",
            file=io.BytesIO(large_content)
        )
        
        files_before = db_session.query(File).count()
        
        try:
            save_upload(db_session, upload_file, test_user.id)
        except HTTPException:
            pass
        
        files_after = db_session.query(File).count()
        # No new files should be created
        assert files_after == files_before


class TestDeleteFile:
    """Test file deletion functionality."""
    
    def test_delete_file_success(self, db_session: Session, test_file: File, test_user: User):
        """Test successful file deletion."""
        file_id = test_file.id
        file_path = test_file.path
        
        response = delete_file(db_session, file_id, test_user.id)
        
        assert response.status_code == 200
        assert "deleted successfully" in response.body.decode()
        
        # Verify file removed from database
        db_file = db_session.query(File).filter(File.id == file_id).first()
        assert db_file is None
        
        # Verify physical file removed
        assert not os.path.exists(file_path)
    
    def test_delete_file_nonexistent_raises_404(self, db_session: Session, test_user: User):
        """Test that deleting non-existent file raises 404."""
        with pytest.raises(HTTPException) as exc_info:
            delete_file(db_session, 99999, test_user.id)
        
        assert exc_info.value.status_code == 404
        assert "not found" in str(exc_info.value.detail).lower()
    
    def test_delete_file_wrong_owner_raises_403(self, db_session: Session, test_file: File, test_admin: User):
        """Test that deleting another user's file raises 403."""
        # test_admin is a different user than test_file owner
        with pytest.raises(HTTPException) as exc_info:
            delete_file(db_session, test_file.id, test_admin.id)
        
        assert exc_info.value.status_code == 403
        assert "permission" in str(exc_info.value.detail).lower()
    
    def test_delete_file_updates_user_storage(self, db_session: Session, test_file: File, test_user: User):
        """Test that deletion updates user's storage usage."""
        initial_storage = test_user.total_storage_used
        file_size = test_file.size
        
        delete_file(db_session, test_file.id, test_user.id)
        
        db_session.refresh(test_user)
        # Storage should be reduced
        expected_storage = initial_storage + file_size  # decrementally adds negative value
        assert test_user.total_storage_used < initial_storage
    
    def test_delete_file_creates_analytics_event(self, db_session: Session, test_file: File, test_user: User):
        """Test that deletion creates analytics event."""
        events_before = db_session.query(AnalyticsEvent).count()
        
        delete_file(db_session, test_file.id, test_user.id)
        
        events_after = db_session.query(AnalyticsEvent).count()
        assert events_after == events_before + 1
        
        event = db_session.query(AnalyticsEvent).order_by(
            AnalyticsEvent.timestamp.desc()
        ).first()
        assert event.event_type == "file_deleted"


class TestDownloadFile:
    """Test file download functionality."""
    
    def test_download_file_success(self, db_session: Session, test_file: File, test_user: User):
        """Test successful file download."""
        response = download_file(db_session, test_file.id, test_user.id)
        
        assert response is not None
        assert response.path == test_file.path
    
    def test_download_file_nonexistent_raises_404(self, db_session: Session, test_user: User):
        """Test that downloading non-existent file raises 404."""
        with pytest.raises(HTTPException) as exc_info:
            download_file(db_session, 99999, test_user.id)
        
        assert exc_info.value.status_code == 404
    
    def test_download_file_wrong_owner_raises_403(self, db_session: Session, test_file: File, test_admin: User):
        """Test that downloading another user's file raises 403."""
        with pytest.raises(HTTPException) as exc_info:
            download_file(db_session, test_file.id, test_admin.id)
        
        assert exc_info.value.status_code == 403
    
    def test_download_file_missing_physical_raises_404(self, db_session: Session, test_file: File, test_user: User):
        """Test that downloading file with missing physical file raises 404."""
        # Delete physical file but keep database record
        os.remove(test_file.path)
        
        with pytest.raises(HTTPException) as exc_info:
            download_file(db_session, test_file.id, test_user.id)
        
        assert exc_info.value.status_code == 404
        assert "not found on disk" in str(exc_info.value.detail).lower()
    
    def test_download_file_creates_analytics_event(self, db_session: Session, test_file: File, test_user: User):
        """Test that download creates analytics event."""
        events_before = db_session.query(AnalyticsEvent).filter(
            AnalyticsEvent.event_type == "file_downloaded"
        ).count()
        
        download_file(db_session, test_file.id, test_user.id)
        
        events_after = db_session.query(AnalyticsEvent).filter(
            AnalyticsEvent.event_type == "file_downloaded"
        ).count()
        assert events_after == events_before + 1


class TestStorageManagement:
    """Test storage tracking functionality."""
    
    def test_update_storage_incrementally(self, db_session: Session, test_user: User):
        """Test incrementing user storage usage."""
        initial_storage = test_user.total_storage_used
        added_storage = 5.5  # MB
        
        update_total_storage_used_incrementally(db_session, test_user.id, added_storage)
        
        db_session.refresh(test_user)
        assert test_user.total_storage_used == initial_storage + added_storage
    
    def test_update_storage_decrementally(self, db_session: Session, test_user: User):
        """Test decrementing user storage usage."""
        # Set initial storage
        test_user.total_storage_used = 10.0
        db_session.commit()
        
        removed_storage = -3.0  # Negative value
        update_total_storage_used_decrementally(db_session, test_user.id, removed_storage)
        
        db_session.refresh(test_user)
        assert test_user.total_storage_used == 10.0 + removed_storage  # 7.0
    
    def test_multiple_storage_updates(self, db_session: Session, test_user: User):
        """Test multiple storage updates maintain accuracy."""
        test_user.total_storage_used = 0.0
        db_session.commit()
        
        # Simulate multiple uploads
        for i in range(5):
            update_total_storage_used_incrementally(db_session, test_user.id, 1.0)
        
        db_session.refresh(test_user)
        assert test_user.total_storage_used == 5.0


class TestFileServiceSecurity:
    """Test security aspects of file service."""
    
    def test_cannot_access_other_user_files(self, db_session: Session, test_file: File, test_admin: User):
        """Test that users cannot access files they don't own."""
        # Try to download another user's file
        with pytest.raises(HTTPException) as exc_info:
            download_file(db_session, test_file.id, test_admin.id)
        
        assert exc_info.value.status_code == 403
        
        # Try to delete another user's file
        with pytest.raises(HTTPException) as exc_info:
            delete_file(db_session, test_file.id, test_admin.id)
        
        assert exc_info.value.status_code == 403
    
    @pytest.mark.skip(reason="not implemented yet")
    def test_path_traversal_prevented(self, db_session: Session, test_user: User, test_upload_dir: str):
        """Test that path traversal attacks are prevented."""
        content = b"content"
        upload_file = UploadFile(
            filename="../../../etc/passwd.pdf",
            file=io.BytesIO(content)
        )
        
        save_upload(db_session, upload_file, test_user.id)
        
        # Verify file is saved in upload directory, not outside
        db_file = db_session.query(File).filter(File.owner_id == test_user.id).first()
        assert test_upload_dir in db_file.path
        assert "../" not in db_file.path
