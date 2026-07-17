from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Tuple
from backend.database.models import User, RefreshToken, UserSetting, AuditLog
from backend.schemas.schemas import UserRegister, UserLogin
from backend.utils.auth_utils import hash_password, verify_password, create_access_token, create_refresh_token
from backend.utils.logger import auth_logger

class AuthenticationService:
    def register_user(self, data: UserRegister, db: Session) -> Tuple[Optional[User], str]:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == data.email).first()
        if existing_user:
            auth_logger.warning(f"Registration failed: Email '{data.email}' already registered.")
            return None, "Email already registered."

        try:
            # Create user
            hashed_pwd = hash_password(data.password)
            user = User(
                email=data.email,
                password_hash=hashed_pwd,
                full_name=data.full_name,
                created_at=datetime.utcnow()
            )
            db.add(user)
            db.commit()
            db.refresh(user)

            # Create default settings for user
            setting = UserSetting(user_id=user.id)
            db.add(setting)
            db.commit()
            
            auth_logger.info(f"User '{data.email}' registered successfully (ID: {user.id}).")
            return user, ""
        except Exception as e:
            db.rollback()
            auth_logger.error(f"Error registering user: {e}")
            return None, "Database registration error."

    def authenticate_user(self, data: UserLogin, db: Session) -> Optional[User]:
        user = db.query(User).filter(User.email == data.email).first()
        if not user:
            auth_logger.warning(f"Authentication failed: User '{data.email}' not found.")
            return None
        
        if not verify_password(data.password, user.password_hash):
            auth_logger.warning(f"Authentication failed: Invalid password for user '{data.email}'.")
            return None
            
        auth_logger.info(f"User '{data.email}' authenticated successfully.")
        return user

    def create_session_tokens(self, user_id: int, db: Session) -> Tuple[str, str]:
        access_token = create_access_token(subject=user_id)
        refresh_token = create_refresh_token(subject=user_id)
        
        # Save refresh token in database
        expires_at = datetime.utcnow() + timedelta(days=7)
        db_token = RefreshToken(
            user_id=user_id,
            token=refresh_token,
            expires_at=expires_at
        )
        db.add(db_token)
        db.commit()
        
        return access_token, refresh_token

    def revoke_refresh_token(self, token: str, db: Session):
        db_token = db.query(RefreshToken).filter(RefreshToken.token == token).first()
        if db_token:
            db_token.is_revoked = True
            db.commit()
            auth_logger.info(f"Refresh token revoked.")

    def audit_action(self, user_id: Optional[int], action: str, ip: Optional[str], ua: Optional[str], db: Session):
        log = AuditLog(
            user_id=user_id,
            action=action,
            ip_address=ip,
            user_agent=ua
        )
        db.add(log)
        db.commit()
