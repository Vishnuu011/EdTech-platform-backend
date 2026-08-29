from enum import Enum

class UserStatus(str, Enum):

    PENDING="PENDING"
    ACTIVE="ACTIVE"
    SUSPENDED="SUSPENDED"
    DISABLED="DISABLED"


class CredentialStatus(str, Enum):

    ACTIVE="ACTIVE"
    DISABLED="DISABLED"
    COMPROMISED="COMPROMISED"



class VerificationType(str, Enum):

    EMAIL_VERIFICATION="EMAIL_VERIFICATION"
    PHONE_VERIFICATION="PHONE_VERIFICATION"
    LOGIN_OTP="LOGIN_OTP"
    PASSWORD_RESET="PASSWORD_RESET"


class VerificationStatus(str, Enum):

    PENDING="PENDING"
    VERIFIED="VERIFIED"
    EXPIRED="EXPIRED"
    LOCKED="LOCKED"


class SessionStatus(str, Enum):

    ACTIVE="ACTIVE"
    EXPIRED="EXPIRED"
    REVOKED="REVOKED"    


class UserRole(str, Enum):

    STUDENT="STUDENT"
    TEACHER="TEACHER"
    ADMIN="ADMIN"


    