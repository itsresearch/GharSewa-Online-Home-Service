from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from service_providers import routing as service_provider_routing

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            service_provider_routing.websocket_urlpatterns
        )
    ),
}) 