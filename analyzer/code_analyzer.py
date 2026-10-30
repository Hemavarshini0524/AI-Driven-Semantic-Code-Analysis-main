
import ast


def empty_analysis_result(error_message):
    """Return a consistent result when analysis cannot be completed."""
    return {
        "error": error_message,
        "classes": [],
        "functions": [],
        "imports": [],
        "relationships": []
    }


class SemanticAnalyzer(ast.NodeVisitor):

    def __init__(self):
        self.classes = set()
        self.functions = set()
        self.imports = set()
        self.relationships = set()

        self.current_class = None
        self.current_function = None
        self.scopes = [{}]

    def analyze(self, source_code):

        # Validate input type
        if not isinstance(source_code, str):
            return empty_analysis_result(
                "Invalid input: source code must be a string."
            )

        # Validate empty input
        if not source_code.strip():
            return empty_analysis_result(
                "Empty source code: please provide Python code."
            )

        try:
            tree = ast.parse(source_code)
            self.visit(tree)

            return {
                "error": None,
                "classes": sorted(self.classes),
                "functions": sorted(self.functions),
                "imports": sorted(self.imports),
                "relationships": sorted(self.relationships)
            }

        except SyntaxError as error:
            return empty_analysis_result(
                f"Python syntax error at line {error.lineno}, "
                f"column {error.offset}: {error.msg}"
            )

        except Exception as error:
            return empty_analysis_result(
                f"Analysis failed: {error}"
            )

    def visit_ClassDef(self, node):
        class_name = node.name
        self.classes.add(class_name)

        # Detect inheritance
        for base in node.bases:
            if isinstance(base, ast.Name):
                self.relationships.add(
                    f"{class_name} inherits from {base.id}"
                )

        previous_class = self.current_class
        self.current_class = class_name

        self.scopes.append({})

        for item in node.body:
            self.visit(item)

        self.scopes.pop()
        self.current_class = previous_class

    def visit_FunctionDef(self, node):
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node):
        self._visit_function(node)

    def _visit_function(self, node):
        function_name = node.name

        if self.current_class:
            qualified_name = (
                f"{self.current_class}.{function_name}"
            )
        else:
            qualified_name = function_name

        self.functions.add(qualified_name)

        previous_function = self.current_function
        self.current_function = qualified_name

        self.scopes.append({})

        for item in node.body:
            self.visit(item)

        self.scopes.pop()
        self.current_function = previous_function

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name)

    def visit_ImportFrom(self, node):
        module = node.module or ""

        for alias in node.names:
            self.imports.add(
                f"{module}.{alias.name}"
            )

    def visit_Assign(self, node):
        # Detect variable = ClassName()
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name):
                class_name = node.value.func.id

                if class_name in self.classes:
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            variable_name = target.id

                            self.scopes[-1][variable_name] = (
                                class_name
                            )

                            self.relationships.add(
                                f"{variable_name} is an object "
                                f"of {class_name}"
                            )

                            if self.current_function:
                                self.relationships.add(
                                    f"{self.current_function} "
                                    f"creates {class_name}"
                                )

        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute):
            object_name = None
            method_name = node.func.attr

            if isinstance(node.func.value, ast.Name):
                object_name = node.func.value.id

            class_name = None

            if object_name:
                for scope in reversed(self.scopes):
                    if object_name in scope:
                        class_name = scope[object_name]
                        break

            if class_name:
                self.relationships.add(
                    f"{object_name}.{method_name} calls "
                    f"{class_name}.{method_name}"
                )

            elif object_name == "self" and self.current_class:
                self.relationships.add(
                    f"{self.current_class}.{method_name} calls "
                    f"{self.current_class}.{method_name}"
                )

            else:
                self.relationships.add(
                    f"Calls method {method_name}"
                )

        elif isinstance(node.func, ast.Name):
            function_name = node.func.id

            if function_name in self.classes:
                self.relationships.add(
                    f"Creates object of {function_name}"
                )
            else:
                self.relationships.add(
                    f"Calls function {function_name}"
                )

        self.generic_visit(node)


def analyze_code(source_code):
    analyzer = SemanticAnalyzer()
    return analyzer.analyze(source_code)
