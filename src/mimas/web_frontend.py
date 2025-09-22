import inspect
from mimas.interface import (
    InterfaceDefinition,
    require_interface_definition_cls,
    require_interface_implementation_cls,
)
from pyodide.http import pyfetch


def make_api_client(
    interface_definition: type[InterfaceDefinition],
    base_url: str = "http://127.0.0.1:8000/api",
):
    require_interface_definition_cls(interface_definition)
    methods = {}
    for route_name in getattr(interface_definition, "_route_definitions", []):
        func_def = interface_definition.__dict__[route_name].__func__
        path_template = getattr(func_def, "_path")
        http_method = getattr(func_def, "_method")
        sig = inspect.signature(func_def)

        def make_method(path_template, sig, http_method):
            async def method(*args, **kwargs):
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                full_path = path_template
                for k, v in bound.arguments.items():
                    full_path = full_path.replace(f"{{{k}}}", str(v))
                url = f"{base_url}{full_path}"
                r = await pyfetch(url, method=http_method)
                r.raise_for_status()
                return await r.json()

            return staticmethod(method)

        methods[route_name] = make_method(path_template, sig, http_method)
    # Create the class with all methods at once
    Frontend = type("Frontend", (interface_definition,), methods)
    require_interface_implementation_cls(Frontend)
    return Frontend
