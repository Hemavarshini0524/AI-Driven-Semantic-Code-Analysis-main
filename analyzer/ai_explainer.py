
import ast


def explain_code(source_code):

    # Validate input
    if not isinstance(source_code, str):
        return "Unable to explain: source code must be a string."

    if not source_code.strip():
        return "Unable to explain: the source code is empty."

    # Parse Python source code
    try:
        tree = ast.parse(source_code)

    except SyntaxError as error:
        return (
            "Cannot explain the code because of a syntax error: "
            f"Line {error.lineno}: {error.msg}"
        )

    explanations = []

    explanations.append("SOFTWARE CODE EXPLANATION")
    explanations.append("=" * 45)

    # Program purpose
    docstring = ast.get_docstring(tree)

    explanations.append("\n1. PROGRAM OVERVIEW")

    if docstring:
        explanations.append(docstring)
    else:
        explanations.append(
            "No module-level documentation was found. "
            "The program structure is described below."
        )

    # Import analysis
    explanations.append("\n2. IMPORTED LIBRARIES")

    imports = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)

        elif isinstance(node, ast.ImportFrom):
            module = node.module or "unknown module"
            names = ", ".join(
                alias.name for alias in node.names
            )
            imports.append(f"{names} from {module}")

    if imports:
        for item in sorted(set(imports)):
            explanations.append(f"- {item}")
    else:
        explanations.append("No imports were found.")

    # Class analysis
    explanations.append("\n3. CLASSES AND METHODS")

    classes = [
        node for node in tree.body
        if isinstance(node, ast.ClassDef)
    ]

    if classes:
        for class_node in classes:

            explanations.append(
                f"\nClass: {class_node.name}"
            )

            if class_node.bases:
                bases = [
                    ast.unparse(base)
                    for base in class_node.bases
                ]
                explanations.append(
                    "Inherits from: " + ", ".join(bases)
                )

            class_doc = ast.get_docstring(class_node)

            if class_doc:
                explanations.append(
                    f"Description: {class_doc}"
                )

            methods = [
                item for item in class_node.body
                if isinstance(
                    item,
                    (ast.FunctionDef, ast.AsyncFunctionDef)
                )
            ]

            if methods:
                for method in methods:
                    explanations.append(
                        f"- Method: {method.name}"
                    )

                    method_doc = ast.get_docstring(method)

                    if method_doc:
                        explanations.append(
                            f"  Description: {method_doc}"
                        )
            else:
                explanations.append(
                    "- No methods detected."
                )
    else:
        explanations.append("No classes were found.")

    # Standalone function analysis
    explanations.append("\n4. FUNCTIONS")

    functions = [
        node for node in tree.body
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        )
    ]

    if functions:
        for function in functions:

            arguments = [
                argument.arg
                for argument in function.args.args
            ]

            explanations.append(
                f"- Function: {function.name}"
            )

            explanations.append(
                "  Parameters: " +
                (", ".join(arguments) if arguments else "None")
            )

            function_doc = ast.get_docstring(function)

            if function_doc:
                explanations.append(
                    f"  Description: {function_doc}"
                )
    else:
        explanations.append(
            "No standalone functions were found."
        )

    # Function and method calls
    explanations.append("\n5. FUNCTION AND METHOD CALLS")

    calls = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):

            try:
                calls.add(ast.unparse(node.func))
            except Exception:
                calls.add("Unknown function call")

    if calls:
        for call in sorted(calls):
            explanations.append(f"- Calls: {call}")
    else:
        explanations.append("No function calls were detected.")

    # Variables
    explanations.append("\n6. IMPORTANT VARIABLES")

    variables = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    variables.add(target.id)

        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                variables.add(node.target.id)

    if variables:
        for variable in sorted(variables):
            explanations.append(f"- {variable}")
    else:
        explanations.append("No assigned variables were detected.")

    # Program structure
    explanations.append("\n7. PROGRAM STRUCTURE")

    explanations.append(
        f"- Total classes: {len(classes)}"
    )

    explanations.append(
        f"- Total standalone functions: {len(functions)}"
    )

    total_methods = sum(
        1 for node in ast.walk(tree)
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        )
        and node not in functions
    )

    explanations.append(
        f"- Total methods and nested functions: {total_methods}"
    )

    explanations.append(
        f"- Total imports: {len(imports)}"
    )

    explanations.append(
        f"- Total detected function/method calls: {len(calls)}"
    )

    explanations.append("\n8. ANALYSIS SUMMARY")

    explanations.append(
        "This explanation was generated using static "
        "Python code analysis. It identifies program "
        "structure and syntax-based relationships."
    )

    explanations.append(
        "It does not execute the program or guarantee "
        "the actual runtime behavior."
    )

    return "\n".join(explanations)
