import requests
import inspect
from mimas.interface import InterfaceDefinition

def make_api_client(base_class, base_url="http://127.0.0.1:8000/api"):
    assert (base_class.__bases__ == (InterfaceDefinition,)), ("Interface definition class must inherit from \"InterfaceDefinition\" and no other direct base classes.")
    methods = {}
    for route_name in getattr(base_class, "_route_definitions", []):
        func_def = base_class.__dict__[route_name].__func__
        path_template = getattr(func_def, "_my_path")
        sig = inspect.signature(func_def)

        def make_method(path_template, sig):
            def method(*args, **kwargs):
                bound = sig.bind(*args, **kwargs)
                bound.apply_defaults()
                full_path = path_template
                for k, v in bound.arguments.items():
                    full_path = full_path.replace(f"{{{k}}}", str(v))
                url = f"{base_url}{full_path}"
                r = requests.get(url)
                r.raise_for_status()
                return r.json()
            return staticmethod(method)

        methods[route_name] = make_method(path_template, sig)
    # Create the class with all methods at once
    Frontend = type("Frontend", (base_class,), methods)
    # Sanity check: Is the auto-generated class constructable? TODO: Remove this later!
    Frontend()
    return Frontend
