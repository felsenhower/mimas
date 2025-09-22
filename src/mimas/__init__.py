from pathlib import Path
from collections.abc import Generator


def get_frontend_dependencies() -> Generator[tuple[str, Path], None, None]:
    """Acquire the Python source files of mimas that are needed inside the
    web frontend.

    Yields:
        tuple[str, Path]: Tuples `(name, location)`, where `name` is the name that the Python source file will be
            available at under the `/mimas/` endpoint and `location` is the path of the source file.
    """
    mimas_root = Path(__file__).parent

    def get_module_path(py_file):
        return (str(Path("mimas") / py_file), mimas_root / py_file)

    yield get_module_path("interface.py")
    yield get_module_path("web_frontend.py")
