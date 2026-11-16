"""
environment_config.py
=====================
Production, Staging, and Development Configuration Engine for NovaNest Platform.
Enforces strict validation, credential safety, CORS origin checking, and cookie policies.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dotenv import dotenv_values, load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

INSECURE_DEFAULT_SECRETS = {
    "NovaNestApp_Secure2026!",
    "NovaNestSecuredEnterpriseKey2026!",
    "NovaAppPass2026!",
    "novanest_monitoring_secret_2026",
    "REPLACE_WITH_APP_PASSWORD",
    "REPLACE_WITH_INGESTION_PASSWORD",
    "PROD_REPLACE_WITH_HSM_OR_VAULT_GENERATED_SECRET",
    "PROD_REPLACE_WITH_VAULT_GENERATED_HS512_SECRET_KEY_MIN_64_BYTES",
    "PROD_REPLACE_WITH_AES256_PBKDF2_KEY_FROM_SECRETS_MANAGER",
}


@dataclass
class EnvironmentValidationResult:
    is_valid: bool
    environment: str
    errors: List[str]
    warnings: List[str]
    configs: Dict[str, str]


def validate_environment_configuration(
    env_file: Optional[Path] = None,
    override_env: Optional[str] = None
) -> EnvironmentValidationResult:
    """
    Validates environment settings against production readiness criteria.
    Uses non-destructive dotenv parsing without polluting process os.environ.
    """
    if env_file and env_file.exists():
        env_dict = dotenv_values(env_file)
    else:
        env_dict = {**os.environ, **dotenv_values(REPO_ROOT / ".env")}

    app_env = (override_env or env_dict.get("APP_ENV") or env_dict.get("ENVIRONMENT") or "development").lower()
    debug = env_dict.get("DEBUG", "False").lower() in ("true", "1", "yes")

    errors: List[str] = []
    warnings: List[str] = []

    # 1. Debug checks
    if app_env == "production" and debug:
        errors.append("Production violation: DEBUG must be set to False in production.")

    # 2. Secret audit
    jwt_secret = env_dict.get("JWT_SECRET_KEY", "")
    app_enc_key = env_dict.get("APP_ENCRYPTION_KEY", "")
    db_pass = env_dict.get("DB_APP_PASSWORD", "")
    monitoring_token = env_dict.get("MONITORING_SECRET_TOKEN", "")

    if app_env == "production":
        if not jwt_secret or jwt_secret in INSECURE_DEFAULT_SECRETS or len(jwt_secret) < 32:
            errors.append("Production violation: JWT_SECRET_KEY must be a unique, dedicated key of at least 32 characters.")

        if not app_enc_key or app_enc_key in INSECURE_DEFAULT_SECRETS or len(app_enc_key) < 16:
            errors.append("Production violation: APP_ENCRYPTION_KEY must be a unique, dedicated key.")

        if db_pass in INSECURE_DEFAULT_SECRETS or not db_pass:
            errors.append("Production violation: DB_APP_PASSWORD must not use insecure default or placeholder credentials.")

        if monitoring_token in INSECURE_DEFAULT_SECRETS or not monitoring_token:
            errors.append("Production violation: MONITORING_SECRET_TOKEN must be a unique high-entropy token.")
    else:
        if db_pass in INSECURE_DEFAULT_SECRETS:
            warnings.append(f"Development warning: DB_APP_PASSWORD uses development fallback '{db_pass[:6]}...'.")

    # 3. CORS origin checks
    cors_origins = env_dict.get("CORS_ALLOWED_ORIGINS", "")
    origins_list = [o.strip() for o in cors_origins.split(",") if o.strip()]

    if app_env == "production":
        if "*" in origins_list:
            errors.append("Production violation: Wildcard '*' is strictly forbidden in CORS_ALLOWED_ORIGINS.")
        for origin in origins_list:
            if origin.startswith("http://") and not origin.startswith("http://localhost"):
                warnings.append(f"Production warning: Non-TLS origin '{origin}' detected in CORS_ALLOWED_ORIGINS.")

    # 4. Cookie hardening checks
    cookie_secure = env_dict.get("COOKIE_SECURE", "True" if app_env == "production" else "False").lower() in ("true", "1", "yes")
    cookie_samesite = env_dict.get("COOKIE_SAMESITE", "Strict" if app_env == "production" else "Lax")

    if app_env == "production" and not cookie_secure:
        errors.append("Production violation: COOKIE_SECURE must be True in production.")

    if app_env == "production" and cookie_samesite.lower() not in ("strict", "lax"):
        errors.append("Production violation: COOKIE_SAMESITE must be 'Strict' or 'Lax' in production.")

    # 5. Database host exposure check
    db_host = env_dict.get("DB_HOST", "127.0.0.1")
    if db_host == "0.0.0.0":
        errors.append("Production violation: DB_HOST cannot be 0.0.0.0 (must be private VPC/internal host or 127.0.0.1).")

    configs = {
        "APP_ENV": app_env,
        "DEBUG": str(debug),
        "DB_HOST": db_host,
        "DB_PORT": env_dict.get("DB_PORT", "3306"),
        "DB_NAME": env_dict.get("DB_NAME", "novanest_db"),
        "COOKIE_SECURE": str(cookie_secure),
        "COOKIE_SAMESITE": cookie_samesite,
        "CORS_ORIGINS_COUNT": str(len(origins_list)),
    }

    return EnvironmentValidationResult(
        is_valid=(len(errors) == 0),
        environment=app_env,
        errors=errors,
        warnings=warnings,
        configs=configs
    )


if __name__ == "__main__":
    res = validate_environment_configuration()
    print(f"Environment: {res.environment.upper()} | Valid: {res.is_valid}")
    if res.errors:
        print("Errors:")
        for e in res.errors:
            print(f"  ❌ {e}")
    if res.warnings:
        print("Warnings:")
        for w in res.warnings:
            print(f"  ⚠️ {w}")
