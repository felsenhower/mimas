from fastapi import FastAPI, Request
from mimas.interface import InterfaceDefinition, require_interface_implementation_cls
from mimas.backend import serve_python_code
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from markupsafe import Markup
from importlib import resources
from collections.abc import Callable, Iterable
from typing import Any, TypeVar, Union
import os


def route_impl(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator for functions that implement routes in the backend.

    Args:
        func (Callable[..., Any]): The function to annotate. It must be possible to convert the method to a
            staticmethod.

    Returns:
        Callable[..., Any]: The function as a static method.
    """
    return staticmethod(func)


T = TypeVar("T", bound=InterfaceDefinition)


def make_api_app(interface_impl_class: type[T]) -> FastAPI:
    """Derive a FastAPI app for the REST API from the given Interface Implementation Class.

    Args:
        interface_impl_class (type[T]): The Interface Implementation Class which inherit from a class T that inherits
            from InterfaceDefinition.

    Returns:
        FastAPI: The generated FastAPI app.
    """
    require_interface_implementation_cls(interface_impl_class)
    abc = interface_impl_class.__base__
    app = FastAPI()
    route_definitions = abc._route_definitions
    for r in route_definitions:
        path = abc.__dict__[r].__func__._path
        method = abc.__dict__[r].__func__._method
        interface_impl_class_dict = interface_impl_class.__dict__
        static_func = interface_impl_class_dict[r]
        if not hasattr(static_func, "__func__"):
            raise Exception(
                f'Unable to obtain function object for function "{r}". Perhaps you forgot a "@route_impl"?'
            )
        func_impl = static_func.__func__
        app.add_api_route(path, endpoint=func_impl, methods=[method])
    return app


SETUP_HTML_CODE = Markup(
    resources.files("mimas").joinpath("data/setup_snippet.html").read_text()
)

SETUP_HTML_HOOK = "setup_mimas"

TEMPLATE_CONTEXT = {SETUP_HTML_HOOK: SETUP_HTML_CODE}

PathLike = Union[os.PathLike, str]


def make_app(
    interface_impl_class: type[T],
    frontend_module: str,
    frontend_source_paths: Iterable[str],
    frontend_extra_modules: Iterable[str] | None,
) -> FastAPI:
    """Generate the outer FastAPI app.

    Args:
        interface_impl_class (type[T]): The Interface Implementation Class (see `make_api_app` for more details)
        frontend_module (str): The name of the frontend module. See `serve_python_code.make_api` for more info.
        frontend_source_paths (Iterable[PathLike]): An iterable containing all paths from the project directory that
            the frontend depends on. See `serve_python_code.make_api` for more info.
        frontend_extra_modules (Iterable[str] | None): See `serve_python_code.make_api` for more info.

    Returns:
        FastAPI: The generated FastAPI app.
    """
    app = FastAPI()

    api_app = make_api_app(interface_impl_class)

    app.mount("/api", api_app)
    app.mount(
        "/mimas",
        serve_python_code.make_app(
            frontend_module, frontend_source_paths, frontend_extra_modules
        ),
        name="mimas",
    )

    templates = Jinja2Templates(directory="templates")

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        return templates.TemplateResponse(
            request=request, name="index.html", context=TEMPLATE_CONTEXT
        )

    return app
