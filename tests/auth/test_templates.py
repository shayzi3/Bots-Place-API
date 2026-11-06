from bots_place.app.controllers.rest.templates import templates


def test_login_page_shows_google_error() -> None:
    html = templates.env.get_template("login.html").render(
        login_url="/api/v1/auth/login",
        register_url="/auth/register",
        google_url="#",
        error="google",
    )
    assert "Не удалось войти через Google" in html


def test_login_page_without_error() -> None:
    html = templates.env.get_template("login.html").render(
        login_url="/api/v1/auth/login",
        register_url="/auth/register",
        google_url="#",
        error=None,
    )
    assert "Не удалось войти через Google" not in html
    assert 'name="email"' in html


def test_confirm_page_renders_code_form() -> None:
    html = templates.env.get_template("confirm.html").render(
        confirm_url="/api/v1/auth/confirm",
        resend_url="/api/v1/auth/resend",
    )
    assert "Подтвердите почту" in html
    assert 'name="code"' in html
