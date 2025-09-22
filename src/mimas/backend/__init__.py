from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import mimas
from mimas.interface import InterfaceDefinition
from pathlib import Path
import shutil
from mimas.backend import serve_python_code


def route_impl(func):
    return staticmethod(func)

def make_api_app(interface_impl_class):
    # Is the provided class constructable? TODO: There's probably a more elegant way to do this...
    interface_impl_class()
    assert (len(interface_impl_class.__bases__) == 1), ("Interface implementation class must inherit from exactly one base class.")
    abc = interface_impl_class.__base__
    assert (abc.__bases__ == (InterfaceDefinition,)), ("Interface definition class must inherit from \"InterfaceDefinition\" and no other direct base classes.")
    app = FastAPI()
    route_definitions = abc._route_definitions
    for r in route_definitions:
        path = abc.__dict__[r].__func__._my_path
        interface_impl_class_dict = interface_impl_class.__dict__
        static_func = interface_impl_class_dict[r]
        if not hasattr(static_func, "__func__"):
            raise Exception(f"Unable to obtain function object for function \"{r}\". Perhaps you forgot a \"@route_impl\"?")
        func_impl = static_func.__func__
        app.add_api_route(path, endpoint=func_impl)
    return app

   
def make_app(interface_impl_class, frontend_module, frontend_source_paths, frontend_extra_modules):
    app = FastAPI()
    api_app = make_api_app(interface_impl_class)
    app.mount("/api", api_app)
    app.mount("/mimas", serve_python_code.make_app(frontend_module, frontend_source_paths, frontend_extra_modules), name="mimas")
    app.mount("/", StaticFiles(directory="static", html=True, follow_symlink=True), name="static")
    return app
