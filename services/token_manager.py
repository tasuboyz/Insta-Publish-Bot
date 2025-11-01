"""
Token manager for Facebook/Instagram Graph API.

Features:
- debug token (get expiry)
- exchange token (get new long-lived token)
- get page access token for Instagram Business account
- background refresh loop that refreshes token when close to expiry and persists to .env

Security note: This script will overwrite the INSTAGRAM_ACCESS_TOKEN value in .env. Keep .env secure.
"""
import asyncio
import time
import httpx
import logging
from pathlib import Path
from typing import Optional
from dotenv import dotenv_values

from config import config

logger = logging.getLogger(__name__)

BASE_URL = f"https://graph.facebook.com/{config.instagram.graph_api_version}"

ENV_PATH = Path('.env')


async def debug_token(token: str) -> Optional[dict]:
    """Return token debug info (data dict) or None on error."""
    if not config.instagram.app_id or not config.instagram.app_secret:
        logger.warning("App id/secret not configured; cannot call debug_token")
        return None

    app_access = f"{config.instagram.app_id}|{config.instagram.app_secret}"
    url = f"https://graph.facebook.com/debug_token"
    params = {"input_token": token, "access_token": app_access}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            data = r.json().get('data')
            return data
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            logger.warning(f"Token debug failed (400 Bad Request) - token may be invalid or expired")
            logger.debug(f"Debug response: {e.response.text}")
            return None
        else:
            logger.error(f"debug_token HTTP error: {e}")
            return None
    except Exception as e:
        logger.error(f"debug_token error: {e}")
        return None


async def exchange_long_lived(token: str) -> Optional[dict]:
    """Exchange a short- or long-lived user token for a new long-lived token.

    Returns dict with keys: access_token, token_type, expires_in
    """
    if not config.instagram.app_id or not config.instagram.app_secret:
        logger.warning("App id/secret not configured; cannot exchange token")
        return None

    params = {
        "grant_type": "fb_exchange_token",
        "client_id": config.instagram.app_id,
        "client_secret": config.instagram.app_secret,
        "fb_exchange_token": token,
    }
    url = "https://graph.facebook.com/oauth/access_token"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json()
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 400:
            logger.error(f"Token exchange failed (400 Bad Request) - check Facebook app configuration")
            logger.error(f"Response: {e.response.text}")
            logger.error("Common causes:")
            logger.error("  - App is in Development mode (needs Live mode)")
            logger.error("  - Missing Instagram Graph API product")
            logger.error("  - Invalid App ID or App Secret")
            logger.error("  - App doesn't have required permissions")
            return None
        else:
            logger.error(f"exchange_long_lived HTTP error: {e}")
            return None
    except Exception as e:
        logger.error(f"exchange_long_lived error: {e}")
        try:
            # log body if available
            logger.error(f"response text: {r.text}")
        except Exception:
            pass
        return None


async def get_page_access_token(page_id: str, user_token: str) -> Optional[str]:
    """Get page access token for a Page ID using a user token with appropriate permissions."""
    url = f"{BASE_URL}/{page_id}"
    params = {"fields": "access_token", "access_token": user_token}
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(url, params=params)
            r.raise_for_status()
            return r.json().get('access_token')
    except Exception as e:
        logger.error(f"get_page_access_token error: {e}")
        try:
            logger.debug(f"response: {r.text}")
        except Exception:
            pass
        return None


def persist_token_to_env(new_token: str) -> bool:
    """Overwrite INSTAGRAM_ACCESS_TOKEN in .env file. Returns True on success."""
    if not ENV_PATH.exists():
        logger.error(".env not found; cannot persist token")
        return False

    try:
        text = ENV_PATH.read_text(encoding='utf-8')
        lines = text.splitlines()
        out = []
        replaced = False
        for ln in lines:
            if ln.strip().startswith('INSTAGRAM_ACCESS_TOKEN='):
                out.append(f"INSTAGRAM_ACCESS_TOKEN={new_token}")
                replaced = True
            else:
                out.append(ln)
        if not replaced:
            out.append(f"INSTAGRAM_ACCESS_TOKEN={new_token}")
        ENV_PATH.write_text('\n'.join(out) + '\n', encoding='utf-8')
        logger.info("Persisted new INSTAGRAM_ACCESS_TOKEN to .env")
        return True
    except Exception as e:
        logger.error(f"persist_token_to_env error: {e}")
        return False


async def test_facebook_app_config() -> dict:
    """Test Facebook app configuration and return status info."""
    result = {
        "app_configured": False,
        "can_exchange_tokens": False,
        "can_debug_tokens": False,
        "issues": []
    }

    if not config.instagram.app_id or not config.instagram.app_secret:
        result["issues"].append("FACEBOOK_APP_ID or FACEBOOK_APP_SECRET not configured")
        return result

    result["app_configured"] = True

    # Test token debug capability
    try:
        debug = await debug_token(config.instagram.access_token)
        result["can_debug_tokens"] = debug is not None
        if not debug:
            result["issues"].append("Cannot debug tokens - app may not have proper permissions")
    except Exception as e:
        result["issues"].append(f"Token debug test failed: {e}")

    # Test token exchange capability
    try:
        # Use a dummy token to test if exchange endpoint works
        exchanged = await exchange_long_lived("dummy_token")
        result["can_exchange_tokens"] = exchanged is not None
        if not exchanged:
            result["issues"].append("Cannot exchange tokens - check app configuration")
    except Exception as e:
        result["issues"].append(f"Token exchange test failed: {e}")

    return result


async def refresh_token_if_needed(threshold_seconds: int = 7 * 24 * 3600) -> bool:
    """Check token expiry and refresh if expires within threshold_seconds.

    Returns True if token refreshed, False otherwise.
    """
    token = config.instagram.access_token
    if not token:
        logger.warning("No INSTAGRAM_ACCESS_TOKEN configured")
        return False

    debug = await debug_token(token)
    if not debug:
        logger.warning("Unable to debug token - may be invalid/expired. Will attempt token exchange anyway.")
        # Try to exchange token even if debug fails
        # This might work if the token is still valid for exchange but not for debug
        return await force_token_refresh()

    expires_at = debug.get('expires_at')
    if not expires_at:
        logger.info("Token appears non-expiring or no expiry info; skipping refresh")
        return False

    now = int(time.time())
    seconds_left = expires_at - now
    logger.info(f"Token expires in {seconds_left // 3600} hours")

    if seconds_left > threshold_seconds:
        logger.debug("Token not close to expiry")
        return False

    # Exchange token
    return await exchange_and_update_token(token)


async def force_token_refresh() -> bool:
    """Force token refresh regardless of expiry check."""
    token = config.instagram.access_token
    if not token:
        logger.warning("No INSTAGRAM_ACCESS_TOKEN configured")
        return False

    logger.info("Attempting forced token refresh...")
    return await exchange_and_update_token(token)


async def exchange_and_update_token(token: str) -> bool:
    """Exchange token and update configuration."""
    exchanged = await exchange_long_lived(token)
    if not exchanged:
        logger.error("Failed to exchange token")
        return False

    new_token = exchanged.get('access_token')
    if not new_token:
        logger.error("Exchange response missing access_token")
        return False

    # Persist and update in-memory config
    ok = persist_token_to_env(new_token)
    if ok:
        # update in-memory
        config.instagram.access_token = new_token
        logger.info("Updated in-memory instagram token")
    else:
        logger.warning("Token refreshed but failed to persist to .env; in-memory updated only")
        config.instagram.access_token = new_token

    # Try to get page access token
    await try_update_page_token(new_token)
    return True


async def try_update_page_token(user_token: str):
    """Try to update page access token if possible."""
    try:
        # try to find page id from user accounts
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(f"{BASE_URL}/me/accounts", params={"access_token": user_token})
            r.raise_for_status()
            data = r.json().get('data', [])
            for entry in data:
                page_id = entry.get('id')
                # get instagram_business_account for page
                r2 = await client.get(f"{BASE_URL}/{page_id}", params={"fields": "instagram_business_account", "access_token": user_token})
                r2.raise_for_status()
                ig = r2.json().get('instagram_business_account')
                if ig and str(ig.get('id')) == str(config.instagram.account_id):
                    # found page; get its access token
                    page_token = entry.get('access_token')
                    if page_token:
                        # Persist page token into env as fallback variable
                        persist_token_to_env(page_token)
                        logger.info(f"Persisted page access token for page {page_id}")
                        break
    except Exception as e:
        logger.debug(f"Could not auto-resolve page access token: {e}")


async def background_refresh_loop(interval_seconds: int = 24 * 3600):
    """Background task: check daily and refresh if near expiry."""
    logger.info("Starting Instagram token background refresh loop")
    try:
        while True:
            try:
                await refresh_token_if_needed()
            except Exception as e:
                logger.error(f"Error in refresh loop: {e}")
            await asyncio.sleep(interval_seconds)
    except asyncio.CancelledError:
        logger.info("Token refresh loop cancelled")
        raise


# Convenience function to start loop (returns task)
def start_background_task(loop=None, interval_seconds: int = 24 * 3600):
    if loop is None:
        loop = asyncio.get_event_loop()
    task = loop.create_task(background_refresh_loop(interval_seconds=interval_seconds))
    return task
