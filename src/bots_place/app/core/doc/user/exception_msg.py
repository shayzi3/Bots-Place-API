from enum import StrEnum


class UserExceptionMessageEnum(StrEnum):
    EMAIL_ALREADY_EXISTS = "Пользователь с таким email уже существует."
    EMAIL_CHANGE_COOLDOWN = "Ссылка уже отправлена. Повторно можно запросить позже."
