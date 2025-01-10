import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import status
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
import base64
import hashlib
import hmac

from models import User
from main import app
from db import get_session 

# Configuración de prueba
FORGET_PWD_SECRET_KEY = b"09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
FORGET_PASSWORD_LINK_EXPIRE_MINUTES = 10

# Crear la base de datos de prueba
@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,)
    SQLModel.metadata.create_all(engine)
    print("Database engine created")
    yield engine

@pytest.fixture(name="session")
def session_fixture(engine):
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session
    
    def get_fastmail_override():
        return Mock()

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides["get_fastmail"] = get_fastmail_override  # Asegúrate de que este es el nombre correcto de tu dependencia
    
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture(name="test_user")
def test_user_fixture(session: Session):
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def create_valid_token(email: str) -> str:
    expire_time = (datetime.now() + timedelta(minutes=5)).timestamp()
    data = f"{email}:{expire_time}"
    signature = hmac.new(FORGET_PWD_SECRET_KEY, data.encode(), hashlib.sha256).hexdigest()
    token = base64.urlsafe_b64encode(f"{data}:{signature}".encode()).decode()
    return token

def create_expired_token(email: str) -> str:
    expire_time = (datetime.now() - timedelta(minutes=5)).timestamp()
    data = f"{email}:{expire_time}"
    signature = hmac.new(FORGET_PWD_SECRET_KEY, data.encode(), hashlib.sha256).hexdigest()
    token = base64.urlsafe_b64encode(f"{data}:{signature}".encode()).decode()
    return token

class TestForgetPassword:
    def test_forget_password_success(self, client, test_user):
        response = client.post(
            "/recover/forget-password",
            json={"email": test_user.email}
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "Password reset email sent successfully"}

    def test_forget_password_invalid_email(self, client):
        response = client.post(
            "/recover/forget-password",
            json={"email": "nonexistent@example.com"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "Email not found"

class TestResetPassword:
    def test_reset_password_success(self, client, test_user, session):
        token = create_valid_token(test_user.email)
        response = client.post(
            "/recover/reset-password",
            json={
                "secret_token": token,
                "new_password": "newpassword123",
                "confirm_password": "newpassword123"
            }
        )
        
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {"message": "Password reset successful"}

        # Verificar que la contraseña se actualizó en la base de datos
        updated_user = session.get(User, test_user.id)
        assert updated_user.hashed_password != test_user.hashed_password

    def test_reset_password_expired_token(self, client, test_user):
        token = create_expired_token(test_user.email)
        response = client.post(
            "/recover/reset-password",
            json={
                "secret_token": token,
                "new_password": "newpassword123",
                "confirm_password": "newpassword123"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Invalid or expired token"

    def test_reset_password_passwords_dont_match(self, client, test_user):
        token = create_valid_token(test_user.email)
        response = client.post(
            "/recover/reset-password",
            json={
                "secret_token": token,
                "new_password": "newpassword123",
                "confirm_password": "differentpassword123"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Passwords do not match"

    def test_reset_password_invalid_token(self, client):
        response = client.post(
            "/recover/reset-password",
            json={
                "secret_token": "invalid_token",
                "new_password": "newpassword123",
                "confirm_password": "newpassword123"
            }
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "Invalid or expired token"