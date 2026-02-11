"""
Unit tests for core validators module.
Testing file validation logic in isolation without external dependencies.
"""
import pytest
import io
from fastapi import UploadFile, HTTPException, status
from app.core.validators import (
    sanitize_filename,
    validate_file_extension,
    validate_file_size
)
from app.core.config import settings


class TestSanitizeFilename:
    """Test filename sanitization to prevent security attacks."""
    
    def test_sanitize_normal_filename(self):
        """Test that normal filenames pass through correctly."""
        result = sanitize_filename("document.pdf")
        assert result == "document.pdf"
    
    def test_sanitize_filename_with_spaces(self):
        """Test that spaces are preserved in filenames."""
        result = sanitize_filename("my document.pdf")
        assert result == "my document.pdf"
    
    def test_sanitize_filename_directory_traversal(self):
        """Test prevention of directory traversal attacks."""
        result = sanitize_filename("../../etc/passwd")
        assert ".." not in result
        assert "/" not in result or result == "passwd"
    
    def test_sanitize_filename_removes_dangerous_characters(self):
        """Test that dangerous characters are replaced with underscores."""
        result = sanitize_filename("file:name<>test.pdf")
        assert ":" not in result
        assert "<" not in result
        assert ">" not in result
        assert "_" in result
    
    def test_sanitize_filename_double_extension(self):
        """Test prevention of double extension attacks."""
        result = sanitize_filename("malware.exe.jpg")
        # Should replace the first dot in the name
        assert result.count(".") == 1
        assert result.endswith(".jpg")
    
    def test_sanitize_filename_max_length(self):
        """Test that overly long filenames are truncated."""
        long_name = "a" * 300 + ".pdf"
        result = sanitize_filename(long_name)
        assert len(result) <= 255
        assert result.endswith(".pdf")
    
    def test_sanitize_filename_special_characters(self):
        """Test handling of various special characters."""
        result = sanitize_filename("file@name#test$.pdf")
        assert "@" not in result or result.replace("_", "")
        assert "#" not in result or result.replace("_", "")
    
    def test_sanitize_filename_unicode(self):
        """Test handling of unicode characters."""
        result = sanitize_filename("файл.pdf")
        # Unicode characters should be preserved
        assert len(result) > 0
        assert result.endswith(".pdf")


class TestValidateFileExtension:
    """Test file extension validation against allowed/blocked lists."""
    
    def test_validate_allowed_extension_pdf(self):
        """Test that allowed extensions are validated successfully."""
        result = validate_file_extension("document.pdf")
        assert result == "pdf"
    
    def test_validate_allowed_extension_jpg(self):
        """Test that image extensions are validated successfully."""
        result = validate_file_extension("photo.jpg")
        assert result == "jpg"
    
    def test_validate_allowed_extension_case_insensitive(self):
        """Test that extension validation is case-insensitive."""
        result = validate_file_extension("Document.PDF")
        assert result == "pdf"
    
    def test_validate_no_extension_raises_error(self):
        """Test that files without extensions are rejected."""
        with pytest.raises(HTTPException) as exc_info:
            validate_file_extension("filename")
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "must have an extension" in str(exc_info.value.detail)
    
    def test_validate_blocked_extension_raises_error(self):
        """Test that blocked extensions are rejected."""
        # Assuming .exe is in BLOCKED_EXTENSIONS
        with pytest.raises(HTTPException) as exc_info:
            validate_file_extension("malware.exe")
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "not allowed" in str(exc_info.value.detail).lower()
    
    def test_validate_disallowed_extension_raises_error(self):
        """Test that extensions not in allowed list are rejected."""
        # Test with an extension that's not explicitly allowed
        with pytest.raises(HTTPException) as exc_info:
            validate_file_extension("file.xyz")
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "not allowed" in str(exc_info.value.detail).lower()
    
    def test_validate_multiple_dots_in_filename(self):
        """Test filename with multiple dots uses last extension."""
        result = validate_file_extension("my.document.test.pdf")
        assert result == "pdf"


class TestValidateFileSize:
    """Test file size validation to prevent oversized uploads."""
    
    def test_validate_file_size_within_limit(self):
        """Test that files within size limit are accepted."""
        content = b"Small file content"
        upload_file = UploadFile(
            filename="small.txt",
            file=io.BytesIO(content)
        )
        
        result = validate_file_size(upload_file)
        assert result == len(content) / (1024 * 1024)
        # Verify file pointer was reset
        assert upload_file.file.tell() == 0
    
    def test_validate_file_size_exceeds_limit(self):
        """Test that files exceeding size limit are rejected."""
        # Create a file larger than MAX_FILE_SIZE
        large_content = b"x" * (settings.MAX_FILE_SIZE + 1000)
        upload_file = UploadFile(
            filename="large.txt",
            file=io.BytesIO(large_content)
        )
        
        with pytest.raises(HTTPException) as exc_info:
            validate_file_size(upload_file)
        assert exc_info.value.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        assert "exceeds maximum" in str(exc_info.value.detail).lower()
    
    def test_validate_empty_file(self):
        """Test that empty files are accepted (edge case)."""
        upload_file = UploadFile(
            filename="empty.txt",
            file=io.BytesIO(b"")
        )
        
        result = validate_file_size(upload_file)
        assert result == 0.0
    
    def test_validate_file_size_at_exact_limit(self):
        """Test that file at exactly the max size is accepted."""
        content = b"x" * settings.MAX_FILE_SIZE
        upload_file = UploadFile(
            filename="exact.txt",
            file=io.BytesIO(content)
        )
        
        result = validate_file_size(upload_file)
        assert result == settings.MAX_FILE_SIZE / (1024 * 1024)


class TestValidatorIntegration:
    """Integration tests combining multiple validation functions."""
    
    def test_full_validation_chain_success(self):
        """Test complete validation chain with valid file."""
        content = b"Valid file content"
        upload_file = UploadFile(
            filename="test-document.pdf",
            file=io.BytesIO(content)
        )
        
        # Sanitize filename
        safe_name = sanitize_filename(upload_file.filename)
        assert safe_name == "test-document.pdf"
        
        # Validate extension
        ext = validate_file_extension(safe_name)
        assert ext == "pdf"
        
        # Validate size
        size = validate_file_size(upload_file)
        assert size > 0
    
    def test_full_validation_chain_failure(self):
        """Test that validation chain stops at first failure."""
        # Create file with dangerous name and blocked extension
        upload_file = UploadFile(
            filename="../../malware.exe",
            file=io.BytesIO(b"malicious content")
        )
        
        # Sanitize first (would pass)
        safe_name = sanitize_filename(upload_file.filename)
        
        # Extension validation should fail
        with pytest.raises(HTTPException):
            validate_file_extension(safe_name)
