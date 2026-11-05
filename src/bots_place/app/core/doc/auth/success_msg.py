from enum import StrEnum


class AuthSuccessMessageEnum(StrEnum):
    REGISTER_CODE_SENT = "Код подтверждения отправлен на email."
    LOGIN_CODE_SENT = "Код для входа отправлен на email."
    CODE_CONFIRMED = "Код подтверждён, вход выполнен."
    CODE_RESENT = "Код отправлен повторно."
    LOGOUT = "Выход выполнен."
