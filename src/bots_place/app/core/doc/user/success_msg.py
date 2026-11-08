from enum import StrEnum


class UserSuccessMessageEnum(StrEnum):
    PROFILE = "Данные пользователя."
    EMAIL_CHANGE_LINK_SENT = "Дальнейшие инструкции на вашей почте."
    EMAIL_CHANGE_LINK_VALID = "Редирект на страницу подтверждения кода."
