from enum import StrEnum


class BaseExceptionMessageEnum(StrEnum):
    INTERNAL_ERROR = "Внутренняя ошибка сервера. Попробуйте позже."
    VALIDATION_ERROR = "Ошибка валидации. {}"
