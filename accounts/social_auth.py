import logging
import re
import secrets
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from .models import SocialIdentity, SocialProviderSettings

logger = logging.getLogger(__name__)

PROVIDERS = {
    "google": {
        "provider": "google",
        "label": "Google",
        "client_id_setting": "GOOGLE_CLIENT_ID",
        "client_secret_setting": "GOOGLE_CLIENT_SECRET",
        "authorize_url": "https://accounts.google.com/o/oauth2/v2/auth",
        "token_url": "https://oauth2.googleapis.com/token",
        "profile_url": "https://openidconnect.googleapis.com/v1/userinfo",
        "scope": "openid email profile",
        "auth_params": {"access_type": "online", "prompt": "select_account"},
    },
    "instagram": {
        "provider": "instagram",
        "label": "Instagram",
        "client_id_setting": "INSTAGRAM_CLIENT_ID",
        "client_secret_setting": "INSTAGRAM_CLIENT_SECRET",
        "authorize_url": "https://www.instagram.com/oauth/authorize",
        "token_url": "https://api.instagram.com/oauth/access_token",
        "profile_url": "https://graph.instagram.com/me",
        "scope": "instagram_business_basic",
        "auth_params": {},
    },
}


def _get_provider(provider):
    config = PROVIDERS.get(provider)
    if not config:
        raise Http404("Unknown social provider")
    return config


def _credentials(config):
    client_id = getattr(settings, config["client_id_setting"], "")
    client_secret = getattr(settings, config["client_secret_setting"], "")
    if client_id and client_secret:
        return client_id, client_secret

    stored = SocialProviderSettings.objects.filter(
        provider=config["provider"]
    ).first()
    if stored:
        return (
            client_id or stored.client_id,
            client_secret or stored.client_secret,
        )
    return client_id, client_secret


def _callback_url(request, provider):
    return request.build_absolute_uri(
        reverse("accounts:social_callback", kwargs={"provider": provider})
    )


def social_login(request, provider):
    config = _get_provider(provider)
    client_id, client_secret = _credentials(config)
    if not client_id or not client_secret:
        messages.error(
            request,
            f"{config['label']} login is not configured yet. "
            "Add the provider credentials in the Django admin or your environment.",
        )
        return redirect("accounts:login")

    state = secrets.token_urlsafe(32)
    request.session[f"oauth_state_{provider}"] = state
    next_url = request.GET.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}
    ):
        request.session[f"oauth_next_{provider}"] = next_url

    params = {
        "client_id": client_id,
        "redirect_uri": _callback_url(request, provider),
        "response_type": "code",
        "scope": config["scope"],
        "state": state,
        **config["auth_params"],
    }
    return redirect(f"{config['authorize_url']}?{urlencode(params)}")


def social_callback(request, provider):
    config = _get_provider(provider)
    client_id, client_secret = _credentials(config)
    if not client_id or not client_secret:
        messages.error(request, f"{config['label']} login is not configured yet.")
        return redirect("accounts:login")

    error = request.GET.get("error")
    if error:
        logger.warning("OAuth error from %s: %s", provider, error)
        messages.error(request, f"{config['label']} login was cancelled or failed.")
        return redirect("accounts:login")

    code = request.GET.get("code")
    state = request.GET.get("state")
    expected_state = request.session.pop(f"oauth_state_{provider}", None)
    if not code or not state or state != expected_state:
        messages.error(request, "The login request could not be verified. Please try again.")
        return redirect("accounts:login")

    try:
        profile = _fetch_profile(
            provider, config, client_id, client_secret, code, _callback_url(request, provider)
        )
        user = _link_user(provider, profile)
    except (requests.RequestException, KeyError, ValueError, TypeError):
        logger.exception("Social login failed for provider %s", provider)
        messages.error(
            request,
            f"We couldn't complete your {config['label']} login. Please try again.",
        )
        return redirect("accounts:login")

    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    messages.success(request, f"Welcome back, {user.first_name or user.username}!")

    next_url = request.session.pop(f"oauth_next_{provider}", "")
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}
    ):
        return redirect(next_url)
    return redirect(settings.LOGIN_REDIRECT_URL)


def _fetch_profile(provider, config, client_id, client_secret, code, redirect_uri):
    token_response = requests.post(
        config["token_url"],
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "code": code,
            "grant_type": "authorization_code",
        },
        timeout=15,
    )
    token_response.raise_for_status()
    access_token = token_response.json().get("access_token")
    if not access_token:
        raise ValueError("The provider did not return an access token.")

    if provider == "google":
        profile_response = requests.get(
            config["profile_url"],
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
        profile_response.raise_for_status()
        data = profile_response.json()
        uid = data.get("sub")
        email = data.get("email", "")
        email_verified = bool(data.get("email_verified"))
        if not email_verified:
            email = ""
        return {
            "uid": str(uid),
            "email": email,
            "username": email.split("@")[0] if email else "google_user",
            "first_name": data.get("given_name", ""),
            "last_name": data.get("family_name", ""),
        }

    profile_response = requests.get(
        config["profile_url"],
        params={"fields": "user_id,username", "access_token": access_token},
        timeout=15,
    )
    profile_response.raise_for_status()
    data = profile_response.json()
    uid = data.get("user_id") or data.get("id")
    return {
        "uid": str(uid),
        "email": "",
        "username": data.get("username") or f"ig_{uid}",
        "first_name": "",
        "last_name": "",
    }


def _link_user(provider, profile):
    if not profile.get("uid"):
        raise ValueError("The provider did not return an account id.")

    identity = (
        SocialIdentity.objects.select_related("user")
        .filter(provider=provider, uid=profile["uid"])
        .first()
    )
    if identity:
        return identity.user

    User = get_user_model()
    email = profile.get("email", "").strip()
    user = None
    if email:
        user = User.objects.filter(email__iexact=email).first()

    if user is None:
        username = _unique_username(profile.get("username") or f"{provider}_user")
        user = User(
            username=username,
            email=email,
            first_name=profile.get("first_name", "")[:150],
            last_name=profile.get("last_name", "")[:150],
        )
        user.set_unusable_password()
        user.save()

    SocialIdentity.objects.get_or_create(
        provider=provider, uid=profile["uid"], defaults={"user": user}
    )
    return user


def _unique_username(value):
    User = get_user_model()
    base = re.sub(r"[^\w.@+-]", "", value)[:120] or "user"
    candidate = base
    suffix = 1
    while User.objects.filter(username__iexact=candidate).exists():
        suffix += 1
        candidate = f"{base[: 150 - len(str(suffix))]}{suffix}"
    return candidate
