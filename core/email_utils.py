import requests

from django.conf import settings


def send_email(to_email, subject, html_content):
    """
    Send an email through the Brevo API.
    """

    api_key = settings.BREVO_API_KEY

    if not api_key:
        raise ValueError("Brevo API key is not configured.")

    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json",
    }

    payload = {
        "sender": {
            "name": settings.DEFAULT_FROM_NAME,
            "email": settings.DEFAULT_FROM_EMAIL,
        },
        "to": [
            {"email": to_email}
        ],
        "subject": subject,
        "htmlContent": html_content,
    }

    response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=15,
    )

    response.raise_for_status()

    return response.json()