from collections.abc import AsyncGenerator

from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from bots_place.app.security.tokens import TokenService
from bots_place.app.tasks.email import EmailSender, SmtpEmailSender
from bots_place.config.env import CookieSettings, JwtSettings, SmtpSettings
from bots_place.config.env import settings as app_settings
from bots_place.domain.commands import (
    ConfirmRegistrationCommand,
    RegisterUserCommand,
)
from bots_place.infrastructure.commands import (
    ConfirmRegistrationHandler,
    RegisterUserHandler,
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
    ) -> ConfirmRegistrationHandler:
        return ConfirmRegistrationHandler(uow)


class MediatorProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_mediator(
        self,
        register_user: RegisterUserHandler,
        confirm_registration: ConfirmRegistrationHandler,
    ) -> Mediator:
        mediator = Mediator()
        mediator.register(RegisterUserCommand, register_user)
        mediator.register(ConfirmRegistrationCommand, confirm_registration)
        return mediator


def create_container() -> AsyncContainer:
    return make_async_container(
        SettingsProvider(),
        DatabaseProvider(),
        DatabaseInitializerProvider(),
        UnitOfWorkProvider(),
        EmailProvider(),
        TokenProvider(),
        CommandHandlerProvider(),
        MediatorProvider(),
    )


async def init_database(container: AsyncContainer) -> None:
    """Create all tables at application startup."""
    initializer = await container.get(BaseDatabaseInitializer)
    await initializer.create_all()
