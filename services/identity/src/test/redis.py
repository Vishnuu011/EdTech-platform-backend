import asyncio
import sys
from pathlib import Path
sys.path.insert(
    0,
    str(Path(__file__).resolve().parents[2])
)
from src.controller.verification import (
    create_otp,
    check_otp
)

async def main():

    email="kk7521673@gmail.com"

    otp=await create_otp(
        verification_type="EMAIL_VERIFICATION",
        destination=email
    )

    print("Generated otp: ", otp)

    result=await check_otp(
        verification_type="EMAIL_VERIFICATION",
        destination=email,
        otp=otp
    )

    print("Verification: ", result)


asyncio.run(main())    