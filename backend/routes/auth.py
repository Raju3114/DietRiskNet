from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.schemas.schemas import UserRegister, UserLogin, Token, TokenRefresh
from backend.services.auth_service import AuthenticationService
from backend.routes.deps import get_current_user
from backend.database.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_service = AuthenticationService()

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, request: Request, db: Session = Depends(get_db)):
    user, err = auth_service.register_user(data, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err
        )
    
    access_token, refresh_token = auth_service.create_session_tokens(user.id, db)
    auth_service.audit_action(
        user_id=user.id,
        action="REGISTER",
        ip=request.client.host if request.client else None,
        ua=request.headers.get("user-agent"),
        db=db
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name
    }

@router.post("/login", response_model=Token)
def login(data: UserLogin, request: Request, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(data, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
        
    access_token, refresh_token = auth_service.create_session_tokens(user.id, db)
    auth_service.audit_action(
        user_id=user.id,
        action="LOGIN",
        ip=request.client.host if request.client else None,
        ua=request.headers.get("user-agent"),
        db=db
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name
    }

@router.post("/logout")
def logout(data: TokenRefresh, request: Request, db: Session = Depends(get_db)):
    auth_service.revoke_refresh_token(data.refresh_token, db)
    return {"detail": "Successfully logged out."}

@router.post("/refresh", response_model=Token)
def refresh(data: TokenRefresh, db: Session = Depends(get_db)):
    from backend.utils.auth_utils import verify_token
    user_id_str = verify_token(data.refresh_token, "refresh")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
        
    user_id = int(user_id_str)
    # Check if token is revoked in db
    from backend.database.models import RefreshToken
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token == data.refresh_token,
        RefreshToken.is_revoked == False
    ).first()
    
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked or is invalid"
        )
        
    user = db.query(User).filter(User.id == user_id).first()
    access_token, refresh_token = auth_service.create_session_tokens(user.id, db)
    
    # Revoke old refresh token
    db_token.is_revoked = True
    db.commit()
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name
    }
