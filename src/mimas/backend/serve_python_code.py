from fastapi import FastAPI
from pathlib import Path
import mimas
from fastapi.responses import FileResponse
from pydantic import BaseModel

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

class Overview(BaseModel):
    frontend_module: str
    frontend_source_paths: list[str]
    frontend_extra_modules: list[str]

def make_app(frontend_module: str, frontend_source_paths, frontend_extra_modules):
    app = FastAPI()
    
    overview = Overview(
        frontend_module = frontend_module,
        frontend_source_paths = [str(target_path) for (source_path, target_path) in get_frontend_python_dependencies(frontend_source_paths)],
        frontend_extra_modules = frontend_extra_modules,
    )

    app.add_api_route("/", endpoint=lambda: overview)
    
    for (source_path, target_path) in get_frontend_python_dependencies(frontend_source_paths):
        app.add_api_route("/" + str(target_path), endpoint=lambda: FileResponse(source_path))
    
    return app
