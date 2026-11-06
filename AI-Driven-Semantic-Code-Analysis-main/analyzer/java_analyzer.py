
import javalang


def empty_java_result(error_message):
    """Return a consistent result when Java analysis fails."""
    return {
        "error": error_message,
        "classes": [],
        "functions": [],
        "imports": [],
        "relationships": []
    }


def analyze_java_code(source_code):

    # Validate input type
    if not isinstance(source_code, str):
        return empty_java_result(
            "Invalid input: Java source code must be a string."
        )

    # Validate empty input
    if not source_code.strip():
        return empty_java_result(
            "Empty source code: please provide Java code."
        )

    try:
        tree = javalang.parse.parse(source_code)

        classes = set()
        functions = set()
        imports = set()
        relationships = set()

        # Collect imports
        for item in tree.imports:
            imports.add(item.path)

        # Collect class and interface names
        for _, node in tree.filter(
            javalang.tree.ClassDeclaration
        ):
            classes.add(node.name)

        for _, node in tree.filter(
            javalang.tree.InterfaceDeclaration
        ):
            classes.add(node.name)

        # Analyze Java classes
        for _, node in tree.filter(
            javalang.tree.ClassDeclaration
        ):
            class_name = node.name

            # Detect inheritance
            if node.extends:
                relationships.add(
                    f"{class_name} inherits from {node.extends.name}"
                )

            # Detect implemented interfaces
            if node.implements:
                for interface in node.implements:
                    relationships.add(
                        f"{class_name} implements {interface.name}"
                    )

            # Identify fields and their types
            field_types = {}

            for field in node.fields:
                for declarator in field.declarators:
                    field_types[declarator.name] = field.type.name

                    relationships.add(
                        f"{class_name} contains field {declarator.name}"
                    )

            # Analyze methods and constructors
            members = (
                list(node.methods) +
                list(node.constructors)
            )

            for member in members:
                member_name = f"{class_name}.{member.name}"
                functions.add(member_name)

                variable_types = dict(field_types)

                # Identify local variable types
                for _, declaration in member.filter(
                    javalang.tree.LocalVariableDeclaration
                ):
                    variable_type = declaration.type.name

                    for declarator in declaration.declarators:
                        variable_types[declarator.name] = (
                            variable_type
                        )

                        if declarator.initializer:
                            for _, creator in declarator.filter(
                                javalang.tree.ClassCreator
                            ):
                                relationships.add(
                                    f"{member_name} creates "
                                    f"{creator.type.name}"
                                )

                # Detect method calls
                for _, invocation in member.filter(
                    javalang.tree.MethodInvocation
                ):
                    qualifier = invocation.qualifier

                    if qualifier in variable_types:
                        target_class = variable_types[qualifier]

                        relationships.add(
                            f"{qualifier}.{invocation.member} calls "
                            f"{target_class}.{invocation.member}"
                        )

                    elif qualifier == "this":
                        relationships.add(
                            f"{member_name} calls "
                            f"{class_name}.{invocation.member}"
                        )

                    else:
                        relationships.add(
                            f"Calls method {invocation.member}"
                        )

        # Analyze interface methods
        for _, node in tree.filter(
            javalang.tree.InterfaceDeclaration
        ):
            for method in node.methods:
                functions.add(
                    f"{node.name}.{method.name}"
                )

        # Detect object creation
        for _, creator in tree.filter(
            javalang.tree.ClassCreator
        ):
            relationships.add(
                f"Creates object of {creator.type.name}"
            )

        return {
            "error": None,
            "classes": sorted(classes),
            "functions": sorted(functions),
            "imports": sorted(imports),
            "relationships": sorted(relationships)
        }

    except javalang.parser.JavaSyntaxError as error:
        return empty_java_result(
            f"Java syntax error: {error}"
        )

    except Exception as error:
        return empty_java_result(
            f"Java analysis failed: {error}"
        )
