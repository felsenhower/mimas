from pathlib import Path


def get_frontend_dependencies():
    mimas_root = Path(__file__).parent

    def get_module_path(py_file):
        return (mimas_root / py_file, Path("mimas") / py_file)

    yield get_module_path("interface.py")
    yield get_module_path("web_frontend.py")
