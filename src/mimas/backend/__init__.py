from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import mimas
from mimas.interface import InterfaceDefinition
from pathlib import Path
import shutil

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

def walk_dir(p: Path):
    for dirpath, dirnames, filenames in p.walk():
        for name in filenames:
            abs_path = dirpath / name 
            rel_path = p.stem / abs_path.relative_to(p)
            if abs_path.suffix == ".py":
                yield (abs_path, rel_path)

def get_frontend_python_dependencies(frontend_include_paths):
    yield from mimas.get_frontend_dependencies()
    for p in frontend_include_paths:
        p = Path(p)
        assert p.exists()
        yield from walk_dir(p)

def make_py_app(frontend_include_paths):
    static_py_dir = Path.cwd() / "static_py"
    if static_py_dir.exists():
        shutil.rmtree(static_py_dir)
    static_py_dir.mkdir()
    for (source_path, target_path) in get_frontend_python_dependencies(frontend_include_paths):
        target_path = static_py_dir / target_path
        target_path.parent.mkdir(exist_ok=True)
        shutil.copy(source_path, target_path)
    return StaticFiles(directory="static_py")
    
def make_app(interface_impl_class, frontend_include_paths):
    app = FastAPI()
    api_app = make_api_app(interface_impl_class)
    app.mount("/api", api_app)
    app.mount("/static_py", make_py_app(frontend_include_paths), name="static_py")
    app.mount("/", StaticFiles(directory="static", html=True, follow_symlink=True), name="static")
    return app
