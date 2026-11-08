from enum import StrEnum


class UserSummaryEnum(StrEnum):
    API_USER = "Get current user"
    API_CHANGE_USERNAME = "Change user name"
    API_CHANGE_USER_EMAIL_LINK = "Send link for change email"
    API_CHANGE_USER_EMAIL = "Change user email"
