from collections.abc import AsyncGenerator

from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from bots_place.app.security.google_auth.base import GoogleAuth
from bots_place.app.security.google_auth.oauth import AuthlibGoogleAuth
from bots_place.app.security.tokens import TokenService
from bots_place.app.tasks.email import EmailSender, SmtpEmailSender
from bots_place.config.env import (
    CodeSettings,
    CookieSettings,
    GoogleSettings,
    JwtSettings,
    SmtpSettings,
)
from bots_place.config.env import settings as app_settings
from bots_place.domain.commands import (
    ConfirmLoginCommand,
    ConfirmRegistrationCommand,
    GoogleLoginCommand,
    RegisterUserCommand,
    RequestLoginCodeCommand,
    ResendCodeCommand,
)
from bots_place.infrastructure.commands import (
    ConfirmLoginHandler,
    ConfirmRegistrationHandler,
    GoogleLoginHandler,
    RegisterUserHandler,
    RequestLoginCodeHandler,
    ResendCodeHandler,
)
from bots_place.infrastructure.mediator import Mediator
from bots_place.infrastructure.repository.base import BaseUnitOfWork
from bots_place.infrastructure.repository.sqlalchemy.core.session import (
    engine as default_engine,
)
from bots_place.infrastructure.repository.sqlalchemy.core.session import (
    session_factory as default_session_factory,
)
from bots_place.infrastructure.repository.sqlalchemy.core.uow import UnitOfWork
from bots_place.infrastructure.setup.base.initializer import BaseDatabaseInitializer
from bots_place.infrastructure.setup.sqlalchemy.initializer import (
    SqlAlchemyDatabaseInitializer,
)


class SettingsProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_jwt_settings(self) -> JwtSettings:
        return app_settings.jwt

    @provide(scope=Scope.APP)
    def provide_smtp_settings(self) -> SmtpSettings:
        return app_settings.smtp

    @provide(scope=Scope.APP)
    def provide_cookie_settings(self) -> CookieSettings:
        return app_settings.cookie

    @provide(scope=Scope.APP)
    def provide_code_settings(self) -> CodeSettings:
        return app_settings.code

    @provide(scope=Scope.APP)
    def provide_google_settings(self) -> GoogleSettings:
        return app_settings.google


class DatabaseProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_engine(self) -> AsyncEngine:
        return default_engine

    @provide(scope=Scope.APP)
    def provide_session_factory(self) -> async_sessionmaker[AsyncSession]:
        return default_session_factory


class DatabaseInitializerProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_database_initializer(
        self, engine: AsyncEngine
    ) -> BaseDatabaseInitializer:
        return SqlAlchemyDatabaseInitializer(engine)


class UnitOfWorkProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def provide_uow(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> AsyncGenerator[BaseUnitOfWork]:
        async with UnitOfWork(session_factory) as uow:
            yield uow


class EmailProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_email_sender(self, smtp: SmtpSettings) -> EmailSender:
        return SmtpEmailSender(smtp)


class TokenProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_token_service(self, jwt_settings: JwtSettings) -> TokenService:
        return TokenService(jwt_settings)


class AuthProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_google_auth(self, google_settings: GoogleSettings) -> GoogleAuth:
        return AuthlibGoogleAuth(google_settings)


class CommandHandlerProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_register_user_handler(
        self,
        uow: BaseUnitOfWork,
        email_sender: EmailSender,
        jwt_settings: JwtSettings,
    ) -> RegisterUserHandler:
        return RegisterUserHandler(uow, email_sender, jwt_settings)

    @provide(scope=Scope.REQUEST)
    def provide_confirm_registration_handler(
        self,
        uow: BaseUnitOfWork,
        code_settings: CodeSettings,
    ) -> ConfirmRegistrationHandler:
        return ConfirmRegistrationHandler(uow, code_settings)

    @provide(scope=Scope.REQUEST)
    def provide_request_login_code_handler(
        self,
        uow: BaseUnitOfWork,
        email_sender: EmailSender,
        jwt_settings: JwtSettings,
    ) -> RequestLoginCodeHandler:
        return RequestLoginCodeHandler(uow, email_sender, jwt_settings)

    @provide(scope=Scope.REQUEST)
    def provide_confirm_login_handler(
        self,
        uow: BaseUnitOfWork,
        code_settings: CodeSettings,
    ) -> ConfirmLoginHandler:
        return ConfirmLoginHandler(uow, code_settings)

    @provide(scope=Scope.REQUEST)
    def provide_google_login_handler(
        self,
        uow: BaseUnitOfWork,
    ) -> GoogleLoginHandler:
        return GoogleLoginHandler(uow)

    @provide(scope=Scope.REQUEST)
    def provide_resend_code_handler(
        self,
        uow: BaseUnitOfWork,
        email_sender: EmailSender,
        code_settings: CodeSettings,
        jwt_settings: JwtSettings,
    ) -> ResendCodeHandler:
        return ResendCodeHandler(uow, email_sender, code_settings, jwt_settings)


class MediatorProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_mediator(
        self,
        register_user: RegisterUserHandler,
        confirm_registration: ConfirmRegistrationHandler,
        request_login_code: RequestLoginCodeHandler,
        confirm_login: ConfirmLoginHandler,
        resend_code: ResendCodeHandler,
        google_login: GoogleLoginHandler,
    ) -> Mediator:
        mediator = Mediator()
        mediator.register(RegisterUserCommand, register_user)
        mediator.register(ConfirmRegistrationCommand, confirm_registration)
        mediator.register(RequestLoginCodeCommand, request_login_code)
        mediator.register(ConfirmLoginCommand, confirm_login)
        mediator.register(ResendCodeCommand, resend_code)
        mediator.register(GoogleLoginCommand, google_login)
        return mediator


def create_container() -> AsyncContainer:
    return make_async_container(
        SettingsProvider(),
        DatabaseProvider(),
        DatabaseInitializerProvider(),
        UnitOfWorkProvider(),
        EmailProvider(),
        TokenProvider(),
        AuthProvider(),
        CommandHandlerProvider(),
        MediatorProvider(),
    )


async def init_database(container: AsyncContainer) -> None:
    """Create all tables at application startup."""
    initializer = await container.get(BaseDatabaseInitializer)
    await initializer.create_all()
