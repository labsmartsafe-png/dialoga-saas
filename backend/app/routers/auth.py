"""
Rotas de autenticação: cadastro, login, perfil e recuperação de senha.

Fase E.4: no cadastro, se existir compra pendente por billing para o mesmo email,
o plano é aplicado automaticamente.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import create_access_token, get_current_user, hash_password, verify_password
from ..database import get_db
from ..models import User
from ..schemas import PasswordResetConfirm, PasswordResetRequest, Token, UserCreate, UserLogin, UserOut
from ..services import billing_service

router = APIRouter()


@router.post("/register", response_model=Token, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    email = payload.email.lower()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="E-mail já cadastrado.")

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        company_name=payload.company_name,
        full_name=payload.full_name,
        phone=payload.phone,
        plan="essencial",
        is_active=True,
    )
    db.add(user)
    db.flush()

    # Se o pagamento chegou antes do cadastro, aplica plano automaticamente.
    billing_service.claim_pending_for_user(db, user)

    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": str(user.id), "email": user.email})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="E-mail ou senha incorretos.")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Conta desativada. Contate o suporte.")
    token = create_access_token({"sub": str(user.id), "email": user.email})
    return Token(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


@router.post("/password-reset/request")
def password_reset_request(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    msg = "Se o e-mail estiver cadastrado, enviaremos as instruções de recuperação."
    if user:
        print(f"[PASSWORD-RESET] Token de recuperação para {user.email}: rT-{user.id}-{user.email}")
    return {"message": msg}


@router.post("/password-reset/confirm")
def password_reset_confirm(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="E-mail não encontrado.")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Senha atualizada com sucesso."}
