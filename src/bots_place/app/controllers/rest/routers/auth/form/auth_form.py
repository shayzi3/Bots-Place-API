from typing import Annotated

from fastapi import Form

from ..doc import AuthFormDescriptionEnum


class EmailAuthForm:
    def __init__(
        self,
        *,
        email: Annotated[
            str,
            Form(
                description=AuthFormDescriptionEnum.EMAIL,
                pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
            ),
        ],
    ) -> None:
        self.email = email
