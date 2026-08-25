import httpx
from src.config.settings import settings


SENDGRID_URL="https://api.sendgrid.com/v3/mail/send"

async def send_verification_email_to_send_grid(
    destination:str,
    otp:str
) -> None:

    payload={
        "personalizations": [
            {
                "to": [
                    {
                        "email": destination
                    }
                ]
            }
        ],
        "from": {
            "email":settings.SENDGRID_FROM_EMAIL
        },
        "subject": "Email Verifiation Code",
        "content":[
            {
                "type":"text/plain",
                "value":(
                    f"Your Verification code is: {otp}\n\n"
                    f"This code will expaire in 5 minutes."
                )
            }
        ]
    }

    headers={
        "Authorization":(
            f"Bearer {settings.SENDGRID_API_KEY}"
        ),
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(
        timeout=10.0
    ) as client:

        response=await client.post(
            SENDGRID_URL,
            json=payload,
            headers=headers
        )

    if response.status_code >= 400:
        raise RuntimeError(
            f"SendGrid failed: "
            f"{response.status_code}"
            f"{response.text}"
        )    