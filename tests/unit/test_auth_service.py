"""
Unit tests for authentication service
"""
import pytest
from unittest.mock import AsyncMock, patch
from backend.services.auth import AuthService
from backend.models.user import UserRegistration, UserLogin

class TestAuthService:
    """Test authentication service"""
    
    @pytest.mark.asyncio
    async def test_hash_password(self):
        """Test password hashing"""
        password = "testpassword123"
        hashed = AuthService.hash_password(password)
        
        assert hashed != password
        assert AuthService.verify_password(password, hashed)
        assert not AuthService.verify_password("wrongpassword", hashed)
    
    @pytest.mark.asyncio
    async def test_generate_verification_code(self):
        """Test verification code generation"""
        code = AuthService.generate_verification_code()
        
        assert len(code) == 6
        assert code.isdigit()
    
    @pytest.mark.asyncio
    @patch('backend.services.auth.db_service')
    @patch('backend.services.auth.email_service')
    async def test_register_user_success(self, mock_email, mock_db):
        """Test successful user registration"""
        # Setup mocks
        mock_db.users_collection.find_one = AsyncMock(return_value=None)
        mock_db.users_collection.insert_one = AsyncMock()
        mock_db.verification_codes_collection.insert_one = AsyncMock()
        mock_email.send_verification_email = AsyncMock(return_value=True)
        
        # Test registration
        registration = UserRegistration(
            email="test@example.com",
            password="testpassword123"
        )
        
        result = await AuthService.register_user(registration)
        
        assert result["email"] == "test@example.com"
        assert "user_id" in result
        assert "message" in result
        mock_db.users_collection.insert_one.assert_called_once()
        mock_db.verification_codes_collection.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('backend.services.auth.db_service')
    async def test_register_user_exists(self, mock_db):
        """Test registration with existing user"""
        # Setup mock
        mock_db.users_collection.find_one = AsyncMock(return_value={"email": "test@example.com"})
        
        # Test registration
        registration = UserRegistration(
            email="test@example.com",
            password="testpassword123"
        )
        
        with pytest.raises(ValueError, match="User already exists"):
            await AuthService.register_user(registration)
    
    @pytest.mark.asyncio
    @patch('backend.services.auth.db_service')
    async def test_login_success(self, mock_db):
        """Test successful login"""
        # Setup mock
        hashed_password = AuthService.hash_password("testpassword123")
        mock_user = {
            "id": "test-user-id",
            "email": "test@example.com",
            "password": hashed_password,
            "is_verified": True
        }
        mock_db.users_collection.find_one = AsyncMock(return_value=mock_user)
        
        # Test login
        login = UserLogin(
            email="test@example.com",
            password="testpassword123"
        )
        
        result = await AuthService.login_user(login)
        
        assert result["status"] == "success"
        assert result["user"]["email"] == "test@example.com"
        assert "password" not in result["user"]
    
    @pytest.mark.asyncio
    @patch('backend.services.auth.db_service')
    async def test_login_invalid_credentials(self, mock_db):
        """Test login with invalid credentials"""
        # Setup mock
        mock_db.users_collection.find_one = AsyncMock(return_value=None)
        
        # Test login
        login = UserLogin(
            email="test@example.com",
            password="wrongpassword"
        )
        
        with pytest.raises(ValueError, match="Invalid credentials"):
            await AuthService.login_user(login)