from typing import Optional, Tuple

import requests

SITEVERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def get_client_ip(meta: dict) -> Optional[str]:
    xff = meta.get("HTTP_X_FORWARDED_FOR")
    if xff:
        return xff.split(",")[0].strip()

    return meta.get("REMOTE_ADDR")


def verify_turnstile(
    *,
    token: str,
    secret: str,
    remote_ip: Optional[str] = None,
    expected_action: Optional[str] = None,
    timeout_seconds: float = 5.0,
) -> Tuple[bool, str]:

    if not secret:
        return False, "Weryfikacja chwilowo niedostępna. Spróbuj ponownie później."
    if not token:
        return False, "Potwierdź, że nie jesteś botem."

    payload = {"secret": secret, "response": token}
    if remote_ip:
        payload["remoteip"] = remote_ip

    try:
        r = requests.post(
            SITEVERIFY_URL,
            data=payload,
            timeout=timeout_seconds,
            headers={"User-Agent": "MIKO-Django/turnstile"},
        )
        r.raise_for_status()
        result = r.json()
    except (requests.RequestException, ValueError):
        return False, "Problem z weryfikacją. Spróbuj ponownie później."

    if not result.get("success", False):
        return False, "Weryfikacja nie powiodła się. Odśwież i spróbuj ponownie."

    # Check that action matches result from siteverify.
    if expected_action and result.get("action") != expected_action:
        return False, "Weryfikacja nie powiodła się. Spróbuj ponownie."

    return True, ""
