import requests
from tools.logger import get_logger

logger = get_logger("ProVerifier")


def verify_license(key: str, verify_url: str = None, timeout: int = 10) -> bool:
    """Verify a license key against a configured verification endpoint.

    If `verify_url` is None, returns False (no remote verification configured).
    The endpoint is expected to accept a JSON body {"license": "<key>"} and
    return JSON with {"valid": true} when valid.
    """
    if not verify_url:
        logger.info("No pro verifier URL configured; skipping remote verification.")
        return False

    try:
        resp = requests.post(verify_url, json={"license": key}, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        valid = bool(data.get("valid", False))
        logger.info(f"License verification response: valid={valid}")
        return valid
    except Exception as e:
        logger.error(f"License verification failed: {e}")
        return False
