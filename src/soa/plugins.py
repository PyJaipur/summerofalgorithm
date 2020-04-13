import bottle
from soa import models, settings
from functools import wraps


class Plugin:
    name = None
    api = 2

    def apply(self, callback, route):
        raise NotImplemented

    def setup(self, app):
        self.app = app


class AutoSession(Plugin):
    name = "auto_session"

    def apply(self, callback, route):
        @wraps(callback)
        def wrapper(*a, **kw):
            bottle.request.session = models.Session()
            return callback(*a, **kw)

        return wrapper


class CurrentUser(Plugin):
    name = "current_user"

    def apply(self, callback, route):
        @wraps(callback)
        def wrapper(*a, **kw):
            # Check cookies
            user = models.AnonUser()
            cook = bottle.request.get_cookie(
                settings.cookie_name, secret=settings.secret
            )
            if cook is not None:
                token = (
                    bottle.request.session.query(models.LoginToken)
                    .filter_by(token=cook, has_logged_out=False)
                    .first()
                )
                bottle.request.token = token
                if token is not None:
                    user = token.user
            bottle.request.user = user
            return callback(*a, **kw)

        return wrapper


class LoginRequired(Plugin):
    name = "login_required"

    def apply(self, callback, route):
        @wraps(callback)
        def wrapper(*a, **kw):
            if bottle.request.user.is_anon:
                return bottle.redirect(
                    self.app.get_url("get_login", next_url=bottle.request.url)
                )
            return callback(*a, **kw)

        return wrapper
