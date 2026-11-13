from contextvars import ContextVar


_current_actor = ContextVar("audit_actor", default=None)


def get_current_actor():
    return _current_actor.get()


class AuditActorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        actor = getattr(request, "user", None)
        identity = (
            (str(actor.pk), actor.get_username())
            if actor is not None and actor.is_authenticated
            else ("", "Anonymous")
        )
        token = _current_actor.set(identity)
        try:
            return self.get_response(request)
        finally:
            _current_actor.reset(token)
