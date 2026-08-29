import logging
from typing import Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Form, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth

from app.config import settings
from app.database import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Authentication"])

oauth = OAuth()

if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

@router.get('/auth/register')
@router.get('/register')
def get_register_page():
    """If someone navigates to /auth/register via GET, redirect to home page."""
    return RedirectResponse(url="/")

@router.get('/auth/login')
@router.get('/login')
def get_login_page():
    """If someone navigates to /auth/login via GET, redirect to home page."""
    return RedirectResponse(url="/")

@router.post('/auth/register')
@router.post('/register')
def register_user(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Register a new user with Email & Password."""
    email_clean = email.strip().lower()
    existing_user = db.query(User).filter(User.email == email_clean).first()
    
    if existing_user:
        return RedirectResponse(url="/?error=Email+already+registered.+Please+sign+in.", status_code=status.HTTP_303_SEE_OTHER)

    new_user = User(
        name=name.strip(),
        email=email_clean,
        password_hash=User.hash_password(password),
        auth_provider="email"
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Establish session
    request.session['user'] = {
        'id': new_user.id,
        'email': new_user.email,
        'name': new_user.name,
        'picture': new_user.avatar_url or ""
    }
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.post('/auth/login')
@router.post('/login')
def login_email(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """Authenticate existing user with Email & Password."""
    email_clean = email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()

    if not user or not user.verify_password(password):
        return RedirectResponse(url="/?error=Invalid+email+or+password", status_code=status.HTTP_303_SEE_OTHER)

    request.session['user'] = {
        'id': user.id,
        'email': user.email,
        'name': user.name,
        'picture': user.avatar_url or ""
    }
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get('/login/google')
async def login_google(request: Request):
    """Redirect user to Google OAuth2 consent screen."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        return RedirectResponse(url='/?error=Google+OAuth2+credentials+not+configured+in+.env')
    redirect_uri = str(request.url_for('auth_google_callback'))
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get('/auth/google/callback', name='auth_google_callback')
async def auth_google_callback(request: Request, db: Session = Depends(get_db)):
    """Process OAuth2 callback from Google, extract user profile, and establish session."""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        return RedirectResponse(url='/?error=google_not_configured')
        
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        if user_info:
            email_clean = user_info.get('email', '').strip().lower()
            name_val = user_info.get('name', 'Google User')
            picture_val = user_info.get('picture', '')

            # Create or update user in DB
            user = db.query(User).filter(User.email == email_clean).first()
            if not user:
                user = User(
                    name=name_val,
                    email=email_clean,
                    avatar_url=picture_val,
                    auth_provider="google"
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            request.session['user'] = {
                'id': user.id,
                'email': user.email,
                'name': user.name,
                'picture': picture_val
            }
        return RedirectResponse(url='/dashboard')
    except Exception as e:
        logger.error(f"Google authentication error: {e}")
        return RedirectResponse(url=f'/?error={str(e)}')

@router.get('/logout')
def logout(request: Request):
    """Clear session data and logout user."""
    request.session.pop('user', None)
    return RedirectResponse(url='/')

@router.get('/api/me')
def get_current_user(request: Request):
    """API endpoint to fetch current authenticated user session."""
    user = request.session.get('user')
    return {"authenticated": user is not None, "user": user}
