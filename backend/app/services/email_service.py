"""
app/services/email_service.py
-----------------------------
EmailJS-based transactional email service.

Belongs in:
    backend/app/services/email_service.py

Used for:
    - Email verification OTP
    - Password reset OTP

EmailJS configuration comes from backend/.env:
    EMAILJS_SERVICE_ID
    EMAILJS_TEMPLATE_ID
    EMAILJS_PUBLIC_KEY
"""

import httpx

from app.config import settings


# EmailJS REST API
EMAILJS_API_URL = "https://api.emailjs.com/api/v1.0/email/send"


def _send_email(
    to_email: str,
    full_name: str,
    otp_code: str,
) -> bool:
    """
    Send an email through EmailJS.

    Returns:
        True  -> EmailJS accepted the request
        False -> Something went wrong

    This function does not raise an exception so that an email
    provider failure does not crash the registration request.
    """

    # ---------------------------------------------------------
    # Check EmailJS configuration
    # ---------------------------------------------------------

    if not settings.EMAILJS_SERVICE_ID:
        print("[email_service] ERROR: EMAILJS_SERVICE_ID is not configured.")
        return False

    if not settings.EMAILJS_TEMPLATE_ID:
        print("[email_service] ERROR: EMAILJS_TEMPLATE_ID is not configured.")
        return False

    if not settings.EMAILJS_PUBLIC_KEY:
        print("[email_service] ERROR: EMAILJS_PUBLIC_KEY is not configured.")
        return False

    # ---------------------------------------------------------
    # EmailJS request
    # ---------------------------------------------------------

    payload = {
    "service_id": settings.EMAILJS_SERVICE_ID,
    "template_id": settings.EMAILJS_TEMPLATE_ID,
    "user_id": settings.EMAILJS_PUBLIC_KEY,
    "accessToken": settings.EMAILJS_PRIVATE_KEY,

    "template_params": {
        "email": to_email,
        "name": full_name,
        "otp": otp_code,
    },
}

    try:
        response = httpx.post(
            EMAILJS_API_URL,
            json=payload,
            timeout=15.0,
        )

        # -----------------------------------------------------
        # Success
        # -----------------------------------------------------

        if response.status_code == 200:
            print(
                f"[email_service] OTP email sent successfully to {to_email}"
            )
            return True

        # -----------------------------------------------------
        # EmailJS rejected the request
        # -----------------------------------------------------

        print(
            "\n"
            + "=" * 70
        )
        print("[email_service] EmailJS FAILED")
        print(f"Status code : {response.status_code}")
        print(f"Response    : {response.text}")
        print("=" * 70 + "\n")

        return False

    except httpx.HTTPError as exc:
        print(
            f"[email_service] HTTP error while sending email "
            f"to {to_email}: {exc}"
        )
        return False

    except Exception as exc:
        print(
            f"[email_service] Unexpected error while sending email "
            f"to {to_email}: {exc}"
        )
        return False


# =============================================================
# OTP EMAIL
# =============================================================

def send_otp_email(
    to_email: str,
    full_name: str,
    otp_code: str,
    purpose: str,
) -> bool:
    """
    Sends an OTP email.

    The same EmailJS template is used for:
        - email_verification
        - password_reset

    The purpose is currently handled by the existing
    EmailJS template text.
    """

    return _send_email(
        to_email=to_email,
        full_name=full_name,
        otp_code=otp_code,
    )


# =============================================================
# RECRUITER STATUS EMAIL
# =============================================================

def send_recruiter_status_email(
    to_email: str,
    full_name: str,
    status: str,
) -> bool:
    """
    Recruiter status notification.

    EmailJS currently has only the OTP template configured,
    so recruiter status emails are not sent through that
    template.

    This function is kept so existing imports/calls in the
    project do not break.

    A separate EmailJS notification template can be added
    later for:
        approved
        rejected
        suspended
        activated
    """

    print(
        f"[email_service] Recruiter status email requested: "
        f"{to_email} -> {status}"
    )

    print(
        "[email_service] Recruiter status notification template "
        "is not configured yet."
    )

    return False