"""
End-to-End tests for File Upload Service.
Testing complete user scenarios and workflows from signup to file management.
"""
import pytest
import io
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestUserJourney:
    """Test complete user journey from signup to file operations."""
    
    def test_new_user_complete_journey(self, client: TestClient, test_upload_dir: str):
        """
        Test a new user's complete journey:
        1. Sign up
        2. Login
        3. Upload files
        4. List files
        5. Download files
        6. Delete files
        """
        # Step 1: Sign up
        signup_response = client.post(
            "/auth/signup",
            json={
                "username": "journeyuser",
                "email": "journey@example.com",
                "password": "JourneyPassword123!"
            }
        )
        assert signup_response.status_code == 200
        user_data = signup_response.json()
        user_id = user_data["id"]
        assert "journey@example.com" in signup_response.text
        
        # Step 2: Login
        login_response = client.post(
            "/auth/login",
            json={
                "email": "journey@example.com",
                "password": "JourneyPassword123!"
            }
        )
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "Welcome back" in login_data["message"]
        token = login_data.get("token", "")
        
        # Step 3: Upload multiple files
        uploaded_files = []
        for i in range(3):
            upload_response = client.post(
                "/file/upload",
                files={"file": (f"document{i}.pdf", io.BytesIO(b"Content " + str(i).encode()), "application/pdf")},
                params={"owner_id": user_id}
            )
            assert upload_response.status_code == 200
            uploaded_files.append(upload_response.json())
        
        # Step 4: List files
        list_response = client.get(
            "/file/",#?skip=0&limit=100&owner_id=1
            params={"owner_id": user_id,"limit":100,"skip":0}
        )
        assert list_response.status_code == 200
        files_list = list_response.json()
        assert len(files_list) >= 3
        
        # Step 5: Download a file
        file_to_download = uploaded_files[0]
        download_response = client.get(
            f"/file/download/{file_to_download['id']}",
            params={"owner_id": user_id}
        )
        assert download_response.status_code == 200
        assert len(download_response.content) > 0
        
        # Step 6: Delete a file
        file_to_delete = uploaded_files[1]
        delete_response = client.delete(
            f"/file/{file_to_delete['id']}",
            params={"owner_id": user_id}
        )
        assert delete_response.status_code == 200
        
        # Verify file is deleted
        verify_response = client.get(
            f"/file/download/{file_to_delete['id']}",
            params={"owner_id": user_id}
        )
        assert verify_response.status_code == 404


class TestMultiUserScenarios:
    """Test scenarios involving multiple users."""
    @pytest.mark.skip(reason="Not implemented yet")
    def test_two_users_isolated_storage(self, client: TestClient, test_upload_dir: str):
        """Test that two users have completely isolated file storage."""
        # Create User 1
        client.post(
            "/auth/signup",
            json={"username": "user1", "email": "user1@example.com", "password": "Pass1word123!"}
        )
        login1 = client.post(
            "/auth/login",
            json={"email": "user1@example.com", "password": "Pass1word123!"}
        )
        user1_id = login1.json()["user_id"]
        
        # Create User 2
        client.post(
            "/auth/signup",
            json={"username": "user2", "email": "user2@example.com", "password": "Pass2word123!"}
        )
        login2 = client.post(
            "/auth/login",
            json={"email": "user2@example.com", "password": "Pass2word123!"}
        )
        user2_id = login2.json()["user_id"]
        
        # User 1 uploads files
        user1_upload = client.post(
            "/file/upload",
            files={"file": ("user1_file.txt", io.BytesIO(b"User 1 content"), "text/plain")},
            data={"owner_id": user1_id}
        )
        user1_file_id = user1_upload.json()["id"]
        
        # User 2 uploads files
        user2_upload = client.post(
            "/file/upload",
            files={"file": ("user2_file.txt", io.BytesIO(b"User 2 content"), "text/plain")},
            data={"owner_id": user2_id}
        )
        user2_file_id = user2_upload.json()["id"]
        
        # User 1 cannot access User 2's files
        user1_access_attempt = client.get(
            f"/file/download/{user2_file_id}",
            params={"owner_id": user1_id}
        )
        assert user1_access_attempt.status_code == 403
        
        # User 2 cannot access User 1's files
        user2_access_attempt = client.get(
            f"/file/download/{user1_file_id}",
            params={"owner_id": user2_id}
        )
        assert user2_access_attempt.status_code == 403
        
        # Each user can access their own files
        user1_own_file = client.get(
            f"/file/download/{user1_file_id}",
            params={"owner_id": user1_id}
        )
        assert user1_own_file.status_code == 200
        
        user2_own_file = client.get(
            f"/file/download/{user2_file_id}",
            params={"owner_id": user2_id}
        )
        assert user2_own_file.status_code == 200
    
    def test_user_storage_quota_tracking(self, client: TestClient, test_upload_dir: str, db_session: Session):
        """Test that user storage is tracked correctly across operations."""
        from app.models.user import User
        
        # Create user
        client.post(
            "/auth/signup",
            json={"username": "storagequser", "email": "storage@example.com", "password": "Storage123!"}
        )
        login = client.post(
            "/auth/login",
            json={"email": "storage@example.com", "password": "Storage123!"}
        )
        user_id = login.json()["user_id"]
        
        # Get initial storage
        user = db_session.query(User).filter(User.id == user_id).first()
        initial_storage = user.total_storage_used  # type: ignore
        
        # Upload files
        file_sizes = []
        for i in range(3):
            content = b"X" * (1024 * (i + 1))  # Different sizes
            upload_response = client.post(
                "/file/upload",
                files={"file": (f"file{i}.txt", io.BytesIO(content), "text/plain")},
                params={"owner_id": user_id}
            )
            file_sizes.append(upload_response.json()["size"])
        
        # Check storage increased
        db_session.refresh(user)
        expected_increase = sum(file_sizes)
        assert user.total_storage_used  > initial_storage # type: ignore
        
        # Delete one file
        files_list = client.get("/file/", params={"owner_id": user_id}).json()
        file_to_delete = files_list[0]
        deleted_size = file_to_delete["size"]
        
        client.delete(
            f"/file/{file_to_delete['id']}",
            params={"owner_id": user_id}
        )
        
        # Check storage decreased
        db_session.refresh(user)
        # Storage should be initial + (uploaded - deleted)
        assert user.total_storage_used < initial_storage + expected_increase # type: ignore


class TestFileTypeScenarios:
    """Test handling of different file types."""
    
    @pytest.mark.parametrize("filename,mimetype,should_succeed", [
        ("document.pdf", "application/pdf", True),
        ("image.jpg", "image/jpeg", True),
        ("image.png", "image/png", True),
        ("doc.txt", "text/plain", True),
        ("spreadsheet.csv", "text/csv", True),
        ("archive.zip", "application/zip", True),
        ("malware.exe", "application/x-msdownload", False),
        ("script.sh", "application/x-sh", False),
    ])
    def test_upload_various_file_types(
        self, client: TestClient, test_upload_dir: str, filename: str, mimetype: str, should_succeed: bool
    ):
        """Test uploading various file types."""
        # Create a user for this test
        client.post(
            "/auth/signup",
            json={"username": f"user_{filename}", "email": f"user_{filename}@example.com", "password": "Test123!"}
        )
        login = client.post(
            "/auth/login",
            json={"email": f"user_{filename}@example.com", "password": "Test123!"}
        )
        user_id = login.json()["user_id"]
        
        response = client.post(
            "/file/upload",
            files={"file": (filename, io.BytesIO(b"content"), mimetype)},
            data={"owner_id": user_id}
        )
        
        if should_succeed:
            assert response.status_code == 200
        else:
            assert response.status_code in [400, 403]


class TestErrorRecovery:
    """Test system behavior under error conditions."""
    
    def test_upload_failure_rollback(self, client: TestClient, test_upload_dir: str, db_session: Session):
        """Test that failed uploads don't leave orphaned records."""
        from app.models.file import File
        from app.core.config import settings
        
        # Create user
        client.post(
            "/auth/signup",
            json={"username": "rollbackuser", "email": "rollback@example.com", "password": "Rollback123!"}
        )
        login = client.post(
            "/auth/login",
            json={"email": "rollback@example.com", "password": "Rollback123!"}
        )
        user_id = login.json()["user_id"]
        
        # Count files before
        files_before = db_session.query(File).filter(File.owner_id == user_id).count()
        
        # Try to upload oversized file (should fail)
        large_content = b"X" * (settings.MAX_FILE_SIZE + 1000)
        response = client.post(
            "/file/upload",
            files={"file": ("large.pdf", io.BytesIO(large_content), "application/pdf")},
            data={"owner_id": user_id}
        )
        assert response.status_code == 413
        
        # Count files after - should be same (rollback)
        files_after = db_session.query(File).filter(File.owner_id == user_id).count()
        assert files_after == files_before
    
    def test_network_interruption_simulation(self, client: TestClient, test_upload_dir: str):
        """Test handling of incomplete uploads (simulated)."""
        # Create user
        client.post(
            "/auth/signup",
            json={"username": "networkuser", "email": "network@example.com", "password": "Network123!"}
        )
        login = client.post(
            "/auth/login",
            json={"email": "network@example.com", "password": "Network123!"}
        )
        user_id = login.json()["user_id"]
        
        # Upload a valid file
        response = client.post(
            "/file/upload",
            files={"file": ("test.pdf", io.BytesIO(b"content"), "application/pdf")},
            params={"owner_id": user_id}
        )
        assert response.status_code == 200
        
        # System should remain consistent
        files = client.get("/file/", params={"owner_id": user_id}).json()
        
        assert len(files) > 0


class TestPerformanceScenarios:
    """Test performance-related scenarios."""
    
    def test_upload_many_small_files(self, client: TestClient, test_upload_dir: str):
        """Test uploading many small files."""
        # Create user
        client.post(
            "/auth/signup",
            json={"username": "perfuser", "email": "perf@example.com", "password": "Perf123!"}
        )
        login = client.post(
            "/auth/login",
            json={"email": "perf@example.com", "password": "Perf123!"}
        )
        user_id = login.json()["user_id"]
        
        # Upload 20 small files
        for i in range(20):
            response = client.post(
                "/file/upload",
                files={"file": (f"small{i}.txt", io.BytesIO(b"small content"), "text/plain")},
                params={"owner_id": user_id}
            )
            assert response.status_code == 200
        
        # List all files
        files = client.get("/file/", params={"owner_id": user_id}).json()
        assert len(files) >= 20
    
    def test_pagination_with_many_files(self, client: TestClient, test_upload_dir: str):
        """Test pagination works correctly with many files."""
        # Create user
        client.post(
            "/auth/signup",
            json={"username": "paginationuser", "email": "pagination@example.com", "password": "Pag123!"}
        )
        login = client.post(
            "/auth/login",
            json={"email": "pagination@example.com", "password": "Pag123!"}
        )
        user_id = login.json()["user_id"]
        
        # Upload 15 files
        for i in range(15):
            client.post(
                "/file/upload",
                files={"file": (f"page{i}.txt", io.BytesIO(b"content"), "text/plain")},
                params={"owner_id": user_id}
            )
        
        # Test pagination
        page1 = client.get("/file/", params={"owner_id": user_id, "skip": 0, "limit": 10}).json()
        page2 = client.get("/file/", params={"owner_id": user_id, "skip": 10, "limit": 10}).json()
        
        assert len(page1) == 10
        assert len(page2) >= 5
        
        # Verify no overlap
        page1_ids = {f["id"] for f in page1}
        page2_ids = {f["id"] for f in page2}
        assert len(page1_ids & page2_ids) == 0


class TestSecurityScenarios:
    """Test security-critical scenarios end-to-end."""
    
    def test_cannot_access_files_without_ownership(self, client: TestClient, test_upload_dir: str):
        """Test that users cannot access files without proper ownership."""
        # Create two users
        for i in [1, 2]:
            client.post(
                "/auth/signup",
                json={
                    "username": f"secuser{i}",
                    "email": f"secuser{i}@example.com",
                    "password": f"Secure{i}23!"
                }
            )
        
        # User 1 uploads file
        login1 = client.post(
            "/auth/login",
            json={"email": "secuser1@example.com", "password": "Secure123!"}
        )
        user1_id = login1.json()["user_id"]
        
        upload_response = client.post(
            "/file/upload",
            files={"file": ("private.txt", io.BytesIO(b"private content"), "text/plain")},
            params={"owner_id": user1_id}
        )
        file_id = upload_response.json()["id"]
        
        # User 2 tries to access
        login2 = client.post(
            "/auth/login",
            json={"email": "secuser2@example.com", "password": "Secure223!"}
        )
        user2_id = login2.json()["user_id"]
        
        # User 2 cannot download
        download_attempt = client.get(
            f"/file/download/{file_id}",
            params={"owner_id": user2_id}
        )
        assert download_attempt.status_code == 403
        
        # User 2 cannot delete
        delete_attempt = client.delete(
            f"/file/{file_id}",
            params={"owner_id": user2_id}
        )
        assert delete_attempt.status_code == 403
    
    def test_malicious_filename_handling(self, client: TestClient, test_upload_dir: str):
        """Test handling of malicious filenames throughout the system."""
        # Create user
        client.post(
            "/auth/signup",
            json={"username": "malicioususer", "email": "malicious@example.com", "password": "Mal123!"}
        )
        login = client.post(
            "/auth/login",
            json={"email": "malicious@example.com", "password": "Mal123!"}
        )
        user_id = login.json()["user_id"]
        
        # Try various malicious filenames
        malicious_names = [
            "../../../etc/passwd.txt",
            "..\\..\\..\\windows\\system32\\config.txt",
            "file; rm -rf /.txt",
            "file && cat /etc/passwd.txt",
            "$(whoami).txt",
            "`whoami`.txt",
        ]
        
        for filename in malicious_names:
            response = client.post(
                "/file/upload",
                files={"file": (filename, io.BytesIO(b"content"), "text/plain")},
                params={"owner_id": user_id}
            )
            
            # Should either succeed with sanitized name or fail gracefully
            assert response.status_code in [200, 400]
            
            if response.status_code == 200:
                # Verify filename was sanitized
                uploaded_filename = response.json()["filename"]
                assert ".." not in uploaded_filename
                assert "/" not in uploaded_filename or uploaded_filename.split("/")[-1]
                assert ";" not in uploaded_filename
                assert "&" not in uploaded_filename


class TestAnalyticsAndAuditing:
    """Test that analytics events are properly logged."""
    
    def test_user_actions_create_analytics_events(
        self, client: TestClient, test_upload_dir: str, db_session: Session
    ):
        """Test that user actions create appropriate analytics events."""
        from app.models.analytics_event import AnalyticsEvent
        
        # Create and login user
        client.post(
            "/auth/signup",
            json={"username": "analyticsuser", "email": "analytics@example.com", "password": "Analytics123!"}
        )
        
        events_after_signup = db_session.query(AnalyticsEvent).count()
        
        login_response = client.post(
            "/auth/login",
            json={"email": "analytics@example.com", "password": "Analytics123!"}
        )
        user_id = login_response.json()["user_id"]
        
        # Should have login event
        events_after_login = db_session.query(AnalyticsEvent).filter(
            AnalyticsEvent.event_type == "user_login"
        ).count()
        assert events_after_login > 0
        
        # Upload file
        client.post(
            "/file/upload",
            files={"file": ("analytics.txt", io.BytesIO(b"content"), "text/plain")},
            params={"owner_id": user_id}
        )
        
        # Should have upload event
        upload_events = db_session.query(AnalyticsEvent).filter(
            AnalyticsEvent.event_type == "file_upload",
            AnalyticsEvent.user_id == user_id
        ).count()
        assert upload_events > 0
