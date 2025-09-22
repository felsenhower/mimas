from fastapi import FastAPI, Request
from pathlib import Path
import mimas
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from importlib import resources
from typing import Union
import os
from collections.abc import Iterable, Generator

PathLike = Union[os.PathLike, str]


def find_python_files(p: PathLike) -> Generator[Path, None, None]:
    """Recursively finds all Python files at the provided path.

    Args:
        p (PathLike): Either a Python file or a directory containing Python
            files. If a directory is given, all non-Python files are ignored.

    Yields:
        Path: The Python files found.
    """
    p = Path(p)
    assert not p.is_absolute()
    assert p.is_dir() or (p.is_file() and p.suffix == ".py")
    if p.is_file():
        yield p
        return
    for dirpath, dirnames, filenames in p.walk():
        for name in filenames:
            subpath = dirpath / name
            if subpath.suffix == ".py":
                yield subpath


def get_frontend_python_dependencies(
    frontend_source_paths: Iterable[PathLike],
) -> Generator[tuple[str, Path], None, None]:
    """Finds all Python files that are needed in the frontend.

    Args:
        frontend_source_paths (Iterable[PathLike]): An iterable of relative paths containing the Python source locations
            that are required in the frontend.

    Yields:
        tuple[str, Path]: Tuples `(name, location)`, where `name` is the name that the Python source file will be
            available at under the `/mimas/` endpoint and `location` is the path of the source file.
    """
    yield from mimas.get_frontend_dependencies()
    for p in frontend_source_paths:
        p = Path(p)
        assert p.exists()
        yield from ((str(x), x) for x in find_python_files(p))


class Overview(BaseModel):
    frontend_module: str
    frontend_source_paths: list[str]
    frontend_extra_modules: list[str]


INIT_JS_CODE = resources.files("mimas").joinpath("data/init.js").read_text()


def make_app(
    frontend_module: str,
    frontend_source_paths: Iterable[str],
    frontend_extra_modules: Iterable[str] | None,
) -> FastAPI:
    """Generate a FastAPI app that serves the python code that is needed inside
    the frontend as well as mimas' required JS and HTML code and an overview
    endpoint under `/mimas/`.

    Args:
        frontend_module (str): The name of the frontend module. It must be possible to import the frontend with this
            name. The frontend module can be a single python file (e.g. `frontend.py`) or a directory with a
            `__init__.py` (e.g. `frontend/__init__.py`), and this argument will be `"frontend"` either way.
        frontend_source_paths (Iterable[PathLike]): An iterable containing all paths from the project directory that
            the frontend depends on. This includes the frontend itself. If the path refers to a directory, all python
            files inside of it will be included recursively.
        frontend_extra_modules (Iterable[str] | None): An iterable containing all Python packages that the frontend
            depends on (directly or indirectly) which are not part of the Python standard library, mimas, or the modules
            that are specified in `frontend_source_paths`. A list of packages available inside Pyodide can be found
            here: https://pyodide.org/en/stable/usage/packages-in-pyodide.html

    Returns:
        FastAPI: The generated FastAPI app.
    """
    app = FastAPI()

    frontend_python_dependencies = dict(
        get_frontend_python_dependencies(frontend_source_paths)
    )

    overview = Overview(
        frontend_module=frontend_module,
        frontend_source_paths=[str(p) for p in frontend_python_dependencies.keys()],
        frontend_extra_modules=list(frontend_extra_modules or []),
    )

    app.add_api_route("/", endpoint=lambda: overview)

    app.add_api_route(
        "/init.js",
        endpoint=lambda: Response(content=INIT_JS_CODE, media_type="text/javascript"),
    )

    def serve_static_file(request: Request):
        path = request.url.path
        # TODO: Fix this abomination
        assert path.startswith("/mimas")
        path = path[(len("/mimas") + 1) :]
        file_location = frontend_python_dependencies[path]
        return FileResponse(file_location)

    for name in frontend_python_dependencies.keys():
        app.add_api_route("/" + str(name), endpoint=serve_static_file)

    return app
