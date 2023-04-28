import logging
from typing import Any, Dict, Optional

from pyramid.config import PHASE1_CONFIG, Configurator

_LOG = logging.getLogger(__name__)


def includeme(config: Configurator) -> None:
    config.include("pyramid_openapi3")
    config.add_directive("pyramid_ogcapi_register_routes", register_routes)


class _OgcType:
    def __init__(self, val: str, config: pyramid.config.Configurator):
        del config
        self.val = val

    def phash(self):
        return f"ogc_type = {self.val}"

    def __call__(self, context, request):
        if request.params.get("f") in ["html", "json"]:
            _LOG.error(request.params["f"].lower() == self.val)
            return request.params["f"].lower() == self.val
        _LOG.error(dict(request.headers))
        if request.headers.get("Accept", "*/*") == "*/*":
            return self.val == "json"
        return request.accept.best_match(["text/html", "application/json"]).split("/")[1] == self.val


def register_routes(
    config: Configurator,
    path_view: Dict[str, Any],
    apiname: str = "pyramid_openapi3",
    route_prefix: Optional[str] = None,
    path_template: Optional[Dict[str, str]] = None,
    json_renderer: str = "json",
) -> None:
    """Register routes of an OSC API application.

    :param route_name_ext: Extension's key for using a ``route_name`` argument
    :param root_factory_ext: Extension's key for using a ``factory`` argument
    """

    def action() -> None:
        config.add_route_predicate("ogc_type", _OgcType)

        spec = config.registry.settings[apiname]["spec"]
        for pattern in spec["paths"].keys():
            route_name = (
                "landing_page"
                if pattern == "/"
                else pattern.lstrip("/")
                .replace("/", "_")
                .replace("{", "")
                .replace("}", "")
                .replace("-", "_"),
            )

            if pattern in path_template:
                config.add_route(
                    f"{route_name}_html",
                    pattern,
                    request_method="GET",
                    ogc_type="html",
                )
                config.add_view(
                    path_view[route_name], route_name=f"{route_name}_html", renderer=json_renderer,ogcapi=True
                )
                config.add_route(
                    f"{route_name}_json",
                    pattern,
                    request_method="GET",
                    ogc_type="json",
                )
                config.add_view(
                    path_view[route_name], route_name=f"{route_name}_json", renderer=json_renderer, ogcapi=True
                )

            else:
                config.add_route(
                    route_name,
                    pattern,
                    request_method="GET",
                )
                config.add_view(path_view[route_name], route_name=route_name, renderer=json_renderer, ogcapi=True)

    config.action(("pyramid_openapi3_register_routes",), action, order=PHASE1_CONFIG)


def request_dict(func):
    def wrapper(request: pyramid.request.Request, **kwargs) -> Any:
        typed_request = {}
        try:
            typed_request{'request_body'} = request.json
        except Exception as e:
            pass
        typed_request{'path'} = request.matchdict
        typed_request{'query'} = request.params
        return = func(request, request_typed=typed_request, **kwargs)
    return wrapper
