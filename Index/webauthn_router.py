import os
import json
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Response, HTTPException, status
from pydantic import BaseModel
from jose import jwt
from dotenv import load_dotenv
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
    base64url_to_bytes,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    UserVerificationRequirement,
    ResidentKeyRequirement,
    AuthenticatorAttachment,
)

load_dotenv()

router = APIRouter(prefix="/webauthn", tags=["webauthn"])

RP_ID = "guma3d.com"
RP_NAME = "GumaLab Secure Vault"
ORIGIN = "https://home.guma3d.com"

# SSO Setup
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback_secret_key_change_me")
ALGORITHM = "HS256"
COOKIE_NAME = "guma_sso_token"
DOMAIN = ".guma3d.com"
if os.getenv("ENV") == "dev":
    DOMAIN = None

db_file = "webauthn_credentials.json"

challenges = {}

def load_db():
    if not os.path.exists(db_file):
        return {}
    with open(db_file, "r") as f:
        return json.load(f)

def save_db(data):
    with open(db_file, "w") as f:
        json.dump(data, f, indent=2)

def create_access_token(username: str):
    expire = datetime.utcnow() + timedelta(days=365)
    to_encode = {"sub": username, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

class RegisterRequest(BaseModel):
    password: str

@router.post("/register/begin")
async def register_begin(req: RegisterRequest):
    password = req.password
    CORRECT_HTTP_PASSWORD = os.getenv("GUMA_AUTH_PASSWORD", "iloveguma")
    if password != CORRECT_HTTP_PASSWORD:
        raise HTTPException(status_code=403, detail="Master password required to register FaceID")

    username = f"User-{str(uuid.uuid4())[:6]}"

    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_id=username.encode("utf-8"),
        user_name=username,
        user_display_name="GumaLab Member",
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM, # FaceID/TouchID/Windows Hello
            user_verification=UserVerificationRequirement.REQUIRED,
            resident_key=ResidentKeyRequirement.REQUIRED, # For username-less login
        ),
    )
    
    challenges[username] = options.challenge
    
    response_data = json.loads(options_to_json(options))
    response_data['internal_username'] = username
    return Response(content=json.dumps(response_data), media_type="application/json")


class RegisterVerifyRequest(BaseModel):
    username: str
    response: dict

@router.post("/register/verify")
async def register_verify(req: RegisterVerifyRequest):
    expected_challenge = challenges.get(req.username)
    if not expected_challenge:
        raise HTTPException(status_code=400, detail="Challenge expired or missing")

    try:
        verification = verify_registration_response(
            credential=req.response,
            expected_challenge=expected_challenge,
            expected_rp_id=RP_ID,
            expected_origin=ORIGIN,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    db = load_db()
    # Store by credential ID
    cred_id = verification.credential_id.hex()
    db[cred_id] = {
        "username": req.username,
        "public_key": verification.credential_public_key.hex(),
        "sign_count": verification.sign_count,
    }
    save_db(db)
    del challenges[req.username]
    return {"status": "ok", "message": "FaceID registered successfully!"}


@router.post("/login/begin")
async def login_begin():
    # Username-less login (Discoverable Credentials)
    options = generate_authentication_options(
        rp_id=RP_ID,
        user_verification=UserVerificationRequirement.REQUIRED,
    )
    
    # Store challenge globally or by challenge hex
    challenge_hex = options.challenge.hex() if isinstance(options.challenge, bytes) else options.challenge
    challenges[challenge_hex] = options.challenge
    
    # Send custom payload so client knows the challenge_hex
    response_data = json.loads(options_to_json(options))
    response_data['challenge_hex'] = challenge_hex
    return Response(content=json.dumps(response_data), media_type="application/json")


class LoginVerifyRequest(BaseModel):
    challenge_hex: str
    response: dict

@router.post("/login/verify")
async def login_verify(req: LoginVerifyRequest, response: Response):
    expected_challenge = challenges.get(req.challenge_hex)
    if not expected_challenge:
        raise HTTPException(status_code=400, detail="Challenge expired")

    # Find the credential in DB
    raw_id = req.response.get("id")
    if not raw_id:
        raise HTTPException(status_code=400, detail="Invalid response")
    
    # Usually base64url encoded. webauthn verification handles this, but we need to fetch public key.
    # The DB is keyed by hex of credential_id.
    try:
        cred_id_bytes = base64url_to_bytes(raw_id)
        cred_id_hex = cred_id_bytes.hex()
    except:
        raise HTTPException(status_code=400, detail="Invalid credential ID format")

    db = load_db()
    user_data = db.get(cred_id_hex)
    if not user_data:
        raise HTTPException(status_code=404, detail="FaceID not recognized visually in DB")

    try:
        verification = verify_authentication_response(
            credential=req.response,
            expected_challenge=expected_challenge,
            expected_rp_id=RP_ID,
            expected_origin=ORIGIN,
            credential_public_key=bytes.fromhex(user_data["public_key"]),
            credential_current_sign_count=user_data["sign_count"],
            require_user_verification=True
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Update sign count
    user_data["sign_count"] = verification.new_sign_count
    save_db(db)
    del challenges[req.challenge_hex]

    token = create_access_token(user_data["username"])
    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=31536000,
        expires=31536000,
        path="/",
        domain=DOMAIN,
        httponly=True,
        secure=True,
        samesite="lax"
    )
    return {"status": "ok", "message": "FaceID Auth Complete"}
