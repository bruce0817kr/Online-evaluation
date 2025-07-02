

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
import os
import io
import base64
import uuid

from secure_file_endpoints import secure_file_router, check_file_access_permission, log_file_access, add_security_headers, get_db
from security import get_current_user

@pytest.fixture
def mock_db_fixture():
    mock_db = MagicMock()
    mock_db.file_metadata = MagicMock()
    mock_db.file_metadata.find_one = AsyncMock(return_value=None)
    mock_db.evaluation_sheets = MagicMock()
    mock_db.evaluation_sheets.find_one = AsyncMock(return_value=None)
    mock_db.file_access_logs = MagicMock()
    mock_db.file_access_logs.insert_one = AsyncMock(return_value=None)
    return mock_db

@pytest.fixture
def client(mock_db_fixture):
    app = FastAPI()
    app.include_router(secure_file_router)

    async def override_get_current_user():
        return AsyncMock(id="test_user_id", role="evaluator")

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = lambda: mock_db_fixture

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.pop(get_current_user)
    app.dependency_overrides.pop(get_db)



@pytest.fixture
def mock_current_user():
    return AsyncMock(id="test_user_id", role="evaluator")

@pytest.fixture
def mock_admin_user():
    return AsyncMock(id="admin_user_id", role="admin")

@pytest.fixture
def mock_secretary_user():
    return AsyncMock(id="secretary_user_id", role="secretary")

@pytest.mark.asyncio
async def test_check_file_access_permission_admin(mock_db_fixture, mock_admin_user):
    mock_db_fixture.file_metadata.find_one.return_value = {"id": "file123", "file_path": "/path/to/file.pdf"}
    result = await check_file_access_permission(mock_db_fixture, mock_admin_user, "file123")
    assert result is True

@pytest.mark.asyncio
async def test_check_file_access_permission_secretary(mock_db_fixture, mock_secretary_user):
    mock_db_fixture.file_metadata.find_one.return_value = {"id": "file123", "file_path": "/path/to/file.pdf"}
    result = await check_file_access_permission(mock_db_fixture, mock_secretary_user, "file123")
    assert result is True

@pytest.mark.asyncio
async def test_check_file_access_permission_evaluator_has_access(mock_db_fixture, mock_current_user):
    mock_db_fixture.file_metadata.find_one.return_value = {"id": "file123", "company_id": "comp1"}
    mock_db_fixture.evaluation_sheets.find_one.return_value = {"company_id": "comp1", "evaluator_id": "test_user_id"}
    result = await check_file_access_permission(mock_db_fixture, mock_current_user, "file123")
    assert result is True

@pytest.mark.asyncio
async def test_check_file_access_permission_evaluator_no_access(mock_db_fixture, mock_current_user):
    mock_db_fixture.file_metadata.find_one.return_value = {"id": "file123", "company_id": "comp2"}
    mock_db_fixture.evaluation_sheets.find_one.return_value = None
    result = await check_file_access_permission(mock_db_fixture, mock_current_user, "file123")
    assert result is False

@pytest.mark.asyncio
async def test_check_file_access_permission_file_not_found(mock_db_fixture, mock_current_user):
    mock_db_fixture.file_metadata.find_one.return_value = None
    result = await check_file_access_permission(mock_db_fixture, mock_current_user, "nonexistent_file")
    assert result is False

@pytest.mark.asyncio
async def test_log_file_access(mock_db_fixture):
    await log_file_access(mock_db_fixture, user_id="user123", file_id="file456", action="view", ip_address="127.0.0.1", user_agent="test_agent")
    mock_db_fixture.file_access_logs.insert_one.assert_called_once()
    args, _ = mock_db_fixture.file_access_logs.insert_one.call_args
    log_entry = args[0]
    assert log_entry["user_id"] == "user123"
    assert log_entry["file_id"] == "file456"
    assert log_entry["action"] == "view"
    assert log_entry["ip_address"] == "127.0.0.1"
    assert log_entry["user_agent"] == "test_agent"
    assert log_entry["success"] is True

@pytest.mark.asyncio
async def test_secure_pdf_view_success(client, mock_db_fixture, mock_current_user):
    file_id = "test_pdf_file"
    test_file_path = "uploads/test_pdf.pdf"
    pdf_content = rb"%PDF-1.4
%%EOF"

    try:
        os.makedirs("uploads", exist_ok=True)
        with open(test_file_path, "wb") as f:
            f.write(pdf_content) # Minimal PDF content

        mock_db_fixture.file_metadata.find_one.return_value = {
            "id": file_id,
            "file_path": "test_pdf.pdf",
            "original_filename": "test_document.pdf"
        }
        with patch('secure_file_endpoints.check_file_access_permission', new_callable=AsyncMock) as mock_check_permission, 
             patch('aiofiles.open', new_callable=AsyncMock) as mock_aiofiles_open, 
             patch('os.path.exists', return_value=True) as mock_os_path_exists, 
             patch('os.path.getsize', return_value=len(pdf_content)) as mock_os_path_getsize:
            mock_check_permission.return_value = True
            mock_file_handle = AsyncMock()
            mock_file_handle.__aenter__.return_value = mock_file_handle
            mock_file_handle.read.side_effect = [pdf_content, b'']
            mock_aiofiles_open.return_value = mock_file_handle

            with patch('secure_file_endpoints.log_file_access', new_callable=AsyncMock) as mock_log_access:
                response = client.post(f"/api/files/secure-pdf-view/{file_id}")

                assert response.status_code == 200
                assert response.headers["content-type"] == "application/pdf"
                assert response.content == pdf_content
                mock_log_access.assert_called_with(
                    mock_db_fixture, # Pass mock_db_fixture
                    user_id=mock_current_user.id,
                    file_id=file_id,
                    action="preview_success",
                    ip_address="testclient",
                    user_agent="testclient",
                    success=True
                )
    finally:
        if os.path.exists(test_file_path):
            os.remove(test_file_path)


        mock_db_fixture.file_metadata.find_one.return_value = {
            "id": file_id,
            "file_path": "test_pdf.pdf",
            "original_filename": "test_document.pdf"
        }
        with patch('secure_file_endpoints.check_file_access_permission', new_callable=AsyncMock) as mock_check_permission,
         patch('aiofiles.open', new_callable=AsyncMock) as mock_aiofiles_open,
         patch('os.path.exists', return_value=True) as mock_os_path_exists,
         patch('os.path.getsize', return_value=len(pdf_content)) as mock_os_path_getsize:
            mock_check_permission.return_value = True
            mock_file_handle = AsyncMock()
            mock_file_handle.__aenter__.return_value = mock_file_handle
            mock_file_handle.read.side_effect = [pdf_content, b'']
            mock_aiofiles_open.return_value = mock_file_handle

            with patch('secure_file_endpoints.log_file_access', new_callable=AsyncMock) as mock_log_access:
                response = client.post(f"/api/files/secure-pdf-view/{file_id}")

                assert response.status_code == 200
                assert response.headers["content-type"] == "application/pdf"
                assert response.content == pdf_content
                mock_log_access.assert_called_with(
                    mock_db_fixture, # Pass mock_db_fixture
                    user_id=mock_current_user.id,
                    file_id=file_id,
                    action="preview_success",
                    ip_address="testclient",
                    user_agent="testclient",
                    success=True
                )
    finally:
        if os.path.exists(test_file_path):
            os.remove(test_file_path)

@pytest.mark.asyncio
async def test_secure_pdf_view_permission_denied(client, mock_db_fixture, mock_current_user):
    file_id = "test_pdf_file"
    mock_db_fixture.file_metadata.find_one.return_value = {
        "id": file_id,
        "file_path": "test_pdf.pdf",
        "original_filename": "test_document.pdf"
    }
    with patch('secure_file_endpoints.check_file_access_permission', new_callable=AsyncMock) as mock_check_permission:
        mock_check_permission.return_value = False
        with patch('secure_file_endpoints.log_file_access', new_callable=AsyncMock) as mock_log_access:
            response = client.post(f"/api/files/secure-pdf-view/{file_id}")

            assert response.status_code == 403
            mock_log_access.assert_called_with(
                mock_db_fixture, # Pass mock_db_fixture
                user_id=mock_current_user.id,
                file_id=file_id,
                action="preview_denied",
                ip_address="testclient",
                user_agent="testclient",
                success=False,
                error_message="접근 권한 없음"
            )

@pytest.mark.asyncio
async def test_get_secure_thumbnail_success(client, mock_db_fixture, mock_current_user):
    file_id = "test_thumbnail_file"
    test_thumbnail_path = "uploads/thumbnails/test_thumb.jpg"
    os.makedirs("uploads/thumbnails", exist_ok=True)
    with open(test_thumbnail_path, "wb") as f:
        f.write(pdf_content) # Minimal PDF content

    mock_db_fixture.file_metadata.find_one.return_value = {
        "id": file_id,
        "file_path": "original/file.pdf",
        "thumbnail_path": test_thumbnail_path
    }
    with patch('secure_file_endpoints.check_file_access_permission', new_callable=AsyncMock) as mock_check_permission, 
         patch('os.path.exists', return_value=True):
        mock_check_permission.return_value = True
        with patch('secure_file_endpoints.log_file_access', new_callable=AsyncMock) as mock_log_access:
            response = client.get(f"/api/files/secure-thumbnail/{file_id}")

            assert response.status_code == 200
            assert response.headers["content-type"] == "image/jpeg"
            assert response.content == b"fake_image_data"
            mock_log_access.assert_called_with(
                mock_db_fixture, # Pass mock_db_fixture
                user_id=mock_current_user.id,
                file_id=file_id,
                action="thumbnail_view",
                ip_address="testclient",
                user_agent="testclient",
                success=True
            )
    os.remove(test_thumbnail_path)
    os.rmdir("uploads/thumbnails") # Clean up created directory

@pytest.mark.asyncio
async def test_get_secure_thumbnail_permission_denied(client, mock_db_fixture, mock_current_user):
    file_id = "test_thumbnail_file"
    mock_db_fixture.file_metadata.find_one.return_value = {
        "id": file_id,
        "file_path": "original/file.pdf",
        "thumbnail_path": "uploads/thumbnails/test_thumb.jpg"
    }
    with patch('secure_file_endpoints.check_file_access_permission', new_callable=AsyncMock) as mock_check_permission:
        mock_check_permission.return_value = False
        with patch('secure_file_endpoints.log_file_access', new_callable=AsyncMock) as mock_log_access:
            response = client.get(f"/api/files/secure-thumbnail/{file_id}")

            assert response.status_code == 403
            mock_log_access.assert_called_with(
                mock_db_fixture, # Pass mock_db_fixture
                user_id=mock_current_user.id,
                file_id=file_id,
                action="preview_denied",
                ip_address="testclient",
                user_agent="testclient",
                success=False,
                error_message="접근 권한 없음"
            )

@pytest.mark.asyncio
async def test_get_secure_thumbnail_no_thumbnail_path(client, mock_db_fixture, mock_current_user):
    file_id = "test_thumbnail_file"
    mock_db_fixture.file_metadata.find_one.return_value = {
        "id": file_id,
        "file_path": "original/file.pdf",
        "thumbnail_path": None # No thumbnail path
    }
    with patch('secure_file_endpoints.check_file_access_permission', new_callable=AsyncMock) as mock_check_permission:
        mock_check_permission.return_value = True
        response = client.get(f"/api/files/secure-thumbnail/{file_id}")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml"
        # Check for default SVG content (minimal check)
        assert b"PDF" in response.content or b"svg" in response.content

@pytest.mark.asyncio
async def test_get_secure_thumbnail_thumbnail_not_found(client, mock_db_fixture, mock_current_user):
    file_id = "test_thumbnail_file"
    mock_db_fixture.file_metadata.find_one.return_value = {
        "id": file_id,
        "file_path": "original/file.pdf",
        "thumbnail_path": "uploads/nonexistent_thumb.jpg" # Path does not exist
    }
    with patch('secure_file_endpoints.check_file_access_permission', new_callable=AsyncMock) as mock_check_permission:
        mock_check_permission.return_value = True
        response = client.get(f"/api/files/secure-thumbnail/{file_id}")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/svg+xml"
        # Check for default SVG content (minimal check)
        assert b"PDF" in response.content or b"svg" in response.content



