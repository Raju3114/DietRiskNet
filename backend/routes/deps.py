from fastapi import Depends, HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from backend.database.database import get_db
from backend.database.models import User
from backend.utils.auth_utils import verify_token
from backend.utils.logger import auth_logger

# Use security token bearer
security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
) -> User:
    token = credentials.credentials
    user_id_str = verify_token(token, "access")
    
    if not user_id_str:
        auth_logger.warning("Authentication failure: Invalid or expired access token.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    user_id = int(user_id_str)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        auth_logger.warning(f"Authentication failure: User ID {user_id} not found in database.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
        
    return user
