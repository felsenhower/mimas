from fastapi import FastAPI, Request
from pathlib import Path
import mimas
from fastapi.responses import FileResponse, Response
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

init_js_code = """
async function init_mimas() {
    const pyodide = await loadPyodide();
    async function get_overview() {
        const response = await fetch("mimas/");
        const json = await response.json();
        return json
    }
    const overview = await get_overview();
    for (let file_name of overview.frontend_source_paths) {
        const parent_dir = file_name.substring(0, file_name.lastIndexOf("/"));
        pyodide.FS.mkdirTree(parent_dir);
        const response = await fetch("mimas/" + file_name);
        const code = await response.text();
        pyodide.FS.writeFile(file_name, code);
    }
    for (let module of overview.frontend_extra_modules) {
        await pyodide.loadPackage(module);
    }
    const frontend_module = overview.frontend_module;
    await pyodide.runPythonAsync(`import ${frontend_module}`);
    const result = await pyodide.runPythonAsync(`${frontend_module}.main()`);
}
init_mimas();
"""

def make_app(frontend_module: str, frontend_source_paths, frontend_extra_modules):
    app = FastAPI()
    
    overview = Overview(
        frontend_module = frontend_module,
        frontend_source_paths = [str(target_path) for (source_path, target_path) in get_frontend_python_dependencies(frontend_source_paths)],
        frontend_extra_modules = frontend_extra_modules,
    )
    
    app.add_api_route("/", endpoint=lambda: overview)
    
    app.add_api_route("/init.js", endpoint=lambda: Response(content=init_js_code, media_type="text/javascript"))
    
    file_locations = {
        str(target_path): source_path for (source_path, target_path) in get_frontend_python_dependencies(frontend_source_paths)
    }
    
    def serve_static_file(request: Request):
        path = request.url.path
        # TODO: Fix this abomination
        assert path.startswith("/mimas")
        path = path[(len("/mimas") + 1):]
        file_location = file_locations[path]
        return FileResponse(file_location)
    
    for (source_path, target_path) in get_frontend_python_dependencies(frontend_source_paths):
        app.add_api_route("/" + str(target_path), endpoint=serve_static_file)
    
    return app
