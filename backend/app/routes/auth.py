import hashlib, secrets, os
from urllib.parse import urlencode
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import get_session
from ..models.db_models import User
from ..models.schemas import RegisterRequest, LoginRequest, AuthResponse

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((password + salt).encode()).hexdigest()


def _make_token() -> str:
    return secrets.token_hex(32)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _redirect_with_auth(user: User, token: str) -> RedirectResponse:
    query = urlencode({
        "token": token,
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
    })
    return RedirectResponse(url=f"{FRONTEND_URL}/login?{query}")


async def _find_or_create_oauth_user(
    session: AsyncSession,
    *,
    name: str,
    email: str,
    provider: str,
    provider_id: str,
) -> User:
    normalized_email = _normalize_email(email)
    result = await session.execute(select(User).where(User.email == normalized_email))
    user = result.scalar_one_or_none()
    if user:
        return user

    salt = secrets.token_hex(8)
    user = User(
        name=name,
        email=normalized_email,
        password_hash=_hash_password(secrets.token_hex(16), salt),
        salt=salt,
        provider=provider,
        provider_id=provider_id,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest, session: AsyncSession = Depends(get_session)):
    email = _normalize_email(req.email)
    result = await session.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    salt = secrets.token_hex(8)
    user = User(
        name=req.name.strip(),
        email=email,
        password_hash=_hash_password(req.password, salt),
        salt=salt,
        provider="local",
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    token = _make_token()
    user.token = token
    await session.commit()

    return AuthResponse(
        user={"id": user.id, "name": user.name, "email": user.email},
        token=token,
    )


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, session: AsyncSession = Depends(get_session)):
    email = _normalize_email(req.email)
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not user.password_hash or not user.salt:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if user.password_hash != _hash_password(req.password, user.salt):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = _make_token()
    user.token = token
    await session.commit()

    return AuthResponse(
        user={"id": user.id, "name": user.name, "email": user.email},
        token=token,
    )


# Google OAuth
@router.get("/google")
async def google_login(session: AsyncSession = Depends(get_session)):
    # Trigger mock if keys are missing or placeholders
    use_mock = not GOOGLE_CLIENT_ID or GOOGLE_CLIENT_ID.startswith(("dummy", "your", "client_id"))
    
    if use_mock:
        user = await _find_or_create_oauth_user(
            session,
            name="Google User",
            email="mock_google@example.com",
            provider="google",
            provider_id="mock-google-user",
        )
        token = _make_token()
        user.token = token
        await session.commit()
        return _redirect_with_auth(user, token)
    
    redirect_uri = f"{BACKEND_URL}/api/auth/google/callback"
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        "&response_type=code"
        "&scope=openid email profile"
        "&access_type=offline"
    )
    return RedirectResponse(url=google_auth_url)


@router.get("/google/callback")
async def google_callback(code: str, session: AsyncSession = Depends(get_session)):
    import httpx
    redirect_uri = f"{BACKEND_URL}/api/auth/google/callback"

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Google OAuth failed")
        tokens = token_resp.json()
        access_token = tokens["access_token"]

        # Get user info
        user_resp = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get Google user info")
        guser = user_resp.json()

    email = guser.get("email", "")
    name = guser.get("name", "Google User")
    google_id = guser.get("sub", "")

    if not email:
        raise HTTPException(status_code=400, detail="Email not provided by Google")

    user = await _find_or_create_oauth_user(
        session,
        name=name,
        email=email,
        provider="google",
        provider_id=google_id,
    )
    token = _make_token()
    user.token = token
    await session.commit()
    return _redirect_with_auth(user, token)


