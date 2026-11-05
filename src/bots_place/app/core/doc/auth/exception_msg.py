from enum import StrEnum


class AuthExceptionMessageEnum(StrEnum):
    EMAIL_ALREADY_EXISTS = "Пользователь с таким email уже существует."
    LOGIN_NOT_ALLOWED = "Пользователь не найден или email не подтверждён."
    INVALID_EMAIL_CODE = "Неверный или просроченный код."
    INVALID_PENDING_TOKEN = "Сессия подтверждения не найдена или истекла."
    RESEND_NOT_ALLOWED = "Повторная отправка кода недоступна."
    RESEND_COOLDOWN = "Код уже отправлен. Повторно можно запросить позже."
