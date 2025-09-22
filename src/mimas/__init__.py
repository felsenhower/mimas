import inspect

from pathlib import Path


def get_frontend_dependencies():
    mimas_root = Path(__file__).parent

    def get_module_path(py_file):
        return (mimas_root / py_file, Path("mimas") / py_file)

    yield get_module_path("interface.py")
    yield get_module_path("web_frontend.py")
    # def get_module_path(module):
    #     module_path = Path(inspect.getsourcefile(module))
    #     assert module_path.exists(), (f"Unable to determine module path for {module}")
    #     rel_path = Path("mimas") / module_path.relative_to(mimas_root)
    #     return (module_path, rel_path)
    # import mimas.interface
    # import mimas.web_frontend
    # yield get_module_path(mimas.interface)
    # yield get_module_path(mimas.web_frontend)
