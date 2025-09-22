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
