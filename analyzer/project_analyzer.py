
import ast
import os
import javalang


def analyze_project(source_files):

    result = {
        "error": None,
        "files": [],
        "dependencies": [],
        "file_details": [],
        "errors": []
    }

    # Validate the overall input
    if not isinstance(source_files, dict):
        result["error"] = (
            "Invalid input: source_files must be a dictionary."
        )
        return result

    if not source_files:
        result["error"] = (
            "Empty project: no source files were provided."
        )
        return result

    try:
        file_map = {}
        class_map = {}
        valid_trees = {}

        result["files"] = sorted(source_files.keys())

        # Step 1: Validate files and parse supported source code
        for filename, source_code in source_files.items():

            if not isinstance(filename, str):
                result["errors"].append(
                    f"Invalid filename: {filename!r}"
                )
                continue

            extension = os.path.splitext(filename)[1].lower()

            if extension not in [".py", ".java"]:
                result["errors"].append(
                    f"{filename}: unsupported file type."
                )
                continue

            if not isinstance(source_code, str):
                result["errors"].append(
                    f"{filename}: source code must be a string."
                )
                continue

            if not source_code.strip():
                result["errors"].append(
                    f"{filename}: file is empty."
                )
                continue

            try:
                if extension == ".py":
                    tree = ast.parse(source_code)

                else:
                    tree = javalang.parse.parse(source_code)

                valid_trees[filename] = tree

                module_name = os.path.splitext(
                    os.path.basename(filename)
                )[0]

                file_map.setdefault(
                    module_name, []
                ).append(filename)

            except SyntaxError as error:
                result["errors"].append(
                    f"{filename}: Python syntax error at "
                    f"line {error.lineno}: {error.msg}"
                )

            except javalang.parser.JavaSyntaxError as error:
                result["errors"].append(
                    f"{filename}: Java syntax error: "
                    f"{error or 'Invalid Java syntax.'}"
                )

            except Exception as error:
                result["errors"].append(
                    f"{filename}: parsing failed: {error}"
                )

        # Step 2: Build class and interface map
        for filename, tree in valid_trees.items():

            extension = os.path.splitext(filename)[1].lower()

            if extension == ".py":

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        class_map.setdefault(
                            node.name, set()
                        ).add(filename)

            elif extension == ".java":

                for _, node in tree.filter(
                    javalang.tree.ClassDeclaration
                ):
                    class_map.setdefault(
                        node.name, set()
                    ).add(filename)

                for _, node in tree.filter(
                    javalang.tree.InterfaceDeclaration
                ):
                    class_map.setdefault(
                        node.name, set()
                    ).add(filename)

        # Step 3: Collect dependencies
        dependency_edges = set()

        def add_dependency(source, target, relationship):
            if source != target:
                dependency_edges.add(
                    (source, target, relationship)
                )

        for filename, tree in valid_trees.items():

            extension = os.path.splitext(filename)[1].lower()

            try:
                if extension == ".py":

                    for node in ast.walk(tree):

                        # Detect imports
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                module = alias.name.split(".")[0]

                                for target in file_map.get(
                                    module, []
                                ):
                                    add_dependency(
                                        filename,
                                        target,
                                        "imports"
                                    )

                        elif isinstance(node, ast.ImportFrom):

                            if node.module:
                                module = node.module.split(".")[0]

                                for target in file_map.get(
                                    module, []
                                ):
                                    add_dependency(
                                        filename,
                                        target,
                                        "imports"
                                    )

                            for alias in node.names:
                                for target in class_map.get(
                                    alias.name, set()
                                ):
                                    add_dependency(
                                        filename,
                                        target,
                                        "imports class"
                                    )

                        # Detect inheritance
                        elif isinstance(node, ast.ClassDef):

                            for base in node.bases:
                                if isinstance(base, ast.Name):

                                    for target in class_map.get(
                                        base.id, set()
                                    ):
                                        add_dependency(
                                            filename,
                                            target,
                                            "inherits from"
                                        )

                        # Detect object creation
                        elif isinstance(node, ast.Call):

                            if isinstance(node.func, ast.Name):
                                class_name = node.func.id

                                for target in class_map.get(
                                    class_name, set()
                                ):
                                    add_dependency(
                                        filename,
                                        target,
                                        "creates object of"
                                    )

                elif extension == ".java":

                    # Detect Java imports
                    for item in tree.imports:
                        imported_name = item.path.split(".")[-1]

                        for target in class_map.get(
                            imported_name, set()
                        ):
                            add_dependency(
                                filename,
                                target,
                                "imports"
                            )

                    # Detect inheritance and implementation
                    for _, node in tree.filter(
                        javalang.tree.ClassDeclaration
                    ):

                        if node.extends:
                            parent_name = node.extends.name

                            for target in class_map.get(
                                parent_name, set()
                            ):
                                add_dependency(
                                    filename,
                                    target,
                                    "inherits from"
                                )

                        if node.implements:
                            for interface in node.implements:
                                interface_name = interface.name

                                for target in class_map.get(
                                    interface_name, set()
                                ):
                                    add_dependency(
                                        filename,
                                        target,
                                        "implements"
                                    )

                    # Detect object creation
                    for _, node in tree.filter(
                        javalang.tree.ClassCreator
                    ):
                        class_name = node.type.name

                        for target in class_map.get(
                            class_name, set()
                        ):
                            add_dependency(
                                filename,
                                target,
                                "creates object of"
                            )

            except Exception as error:
                result["errors"].append(
                    f"{filename}: dependency analysis failed: {error}"
                )

        # Step 4: Format dependency results
        result["dependencies"] = [
            {
                "source": source,
                "target": target,
                "relationship": relationship
            }
            for source, target, relationship
            in sorted(dependency_edges)
        ]

        # Step 5: Create file-level details
        for filename in result["files"]:

            targets = sorted({
                target
                for source, target, relationship
                in dependency_edges
                if source == filename
            })

            result["file_details"].append({
                "filename": filename,
                "dependencies": targets
            })

    except Exception as error:
        result["error"] = (
            f"Project analysis failed: {error}"
        )

    return result
