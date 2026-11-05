from bots_place.app.controllers.rest.templates import templates


def test_login_page_shows_error() -> None:
    html = templates.env.get_template("login.html").render(
        login_url="/api/v1/auth/login",
        register_url="/auth/register",
        google_url="#",
        error="login",
    )
    assert "Пользователь не найден" in html


def test_login_page_without_error() -> None:
    html = templates.env.get_template("login.html").render(
        login_url="/api/v1/auth/login",
        register_url="/auth/register",
        google_url="#",
        error=None,
    )
    assert "Пользователь не найден" not in html
    assert 'name="email"' in html


def test_confirm_page_renders_code_form() -> None:
    html = templates.env.get_template("confirm.html").render(
        confirm_url="/api/v1/auth/confirm",
        google_url="#",
        error=None,
    )
    assert "Подтвердите почту" in html
    assert 'name="code"' in html


def test_confirm_page_shows_code_error() -> None:
    html = templates.env.get_template("confirm.html").render(
        confirm_url="/api/v1/auth/confirm",
        google_url="#",
        error="code",
    )
    assert "Неверный или просроченный код" in html
