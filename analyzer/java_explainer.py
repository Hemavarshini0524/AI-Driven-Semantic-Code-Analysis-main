
import javalang


def explain_java_code(source_code):

    if not isinstance(source_code, str):
        return "Unable to explain: Java source code must be a string."

    if not source_code.strip():
        return "Unable to explain: Java source code is empty."

    try:
        tree = javalang.parse.parse(source_code)

    except javalang.parser.JavaSyntaxError as error:
        return (
            "Cannot explain Java code because of a syntax error. "
            "Please check the class, method, and bracket structure."
        )

    except Exception as error:
        return f"Java explanation failed: {error}"

    explanations = []

    explanations.append("JAVA CODE EXPLANATION")
    explanations.append("=" * 45)

    # Imports
    explanations.append("\n1. IMPORTED PACKAGES")

    if tree.imports:
        for item in tree.imports:
            explanations.append(f"- {item.path}")
    else:
        explanations.append("No imports were found.")

    # Classes
    explanations.append("\n2. CLASSES")

    class_count = 0
    method_count = 0
    constructor_count = 0

    for _, node in tree.filter(
        javalang.tree.ClassDeclaration
    ):
        class_count += 1

        explanations.append(
            f"\nClass: {node.name}"
        )

        if node.extends:
            explanations.append(
                f"- Inherits from: {node.extends.name}"
            )

        if node.implements:
            interfaces = [
                item.name for item in node.implements
            ]
            explanations.append(
                "- Implements: " + ", ".join(interfaces)
            )

        for field in node.fields:
            for declarator in field.declarators:
                explanations.append(
                    f"- Field: {declarator.name} "
                    f"(Type: {field.type.name})"
                )

        for method in node.methods:
            method_count += 1
            explanations.append(
                f"- Method: {method.name}"
            )
            explanations.append(
                f"  Return type: "
                f"{method.return_type.name if method.return_type else 'void'}"
            )

            parameters = [
                parameter.name
                for parameter in method.parameters
            ]

            explanations.append(
                "  Parameters: " +
                (", ".join(parameters) if parameters else "None")
            )

        for constructor in node.constructors:
            constructor_count += 1
            explanations.append(
                f"- Constructor: {constructor.name}"
            )

    # Interfaces
    explanations.append("\n3. INTERFACES")

    interface_count = 0

    for _, node in tree.filter(
        javalang.tree.InterfaceDeclaration
    ):
        interface_count += 1

        explanations.append(
            f"\nInterface: {node.name}"
        )

        for method in node.methods:
            explanations.append(
                f"- Declares method: {method.name}"
            )

    if interface_count == 0:
        explanations.append("No interfaces were found.")

    # Object creation
    explanations.append("\n4. OBJECT CREATION")

    objects = set()

    for _, node in tree.filter(
        javalang.tree.ClassCreator
    ):
        objects.add(node.type.name)

    if objects:
        for object_name in sorted(objects):
            explanations.append(
                f"- Creates object of {object_name}"
            )
    else:
        explanations.append("No object creation was detected.")

    # Method calls
    explanations.append("\n5. METHOD CALLS")

    calls = set()

    for _, node in tree.filter(
        javalang.tree.MethodInvocation
    ):
        calls.add(node.member)

    if calls:
        for call in sorted(calls):
            explanations.append(
                f"- Calls method: {call}"
            )
    else:
        explanations.append("No method calls were detected.")

    # Summary
    explanations.append("\n6. PROGRAM STRUCTURE")

    explanations.append(
        f"- Total classes: {class_count}"
    )

    explanations.append(
        f"- Total interfaces: {interface_count}"
    )

    explanations.append(
        f"- Total methods: {method_count}"
    )

    explanations.append(
        f"- Total constructors: {constructor_count}"
    )

    explanations.append(
        f"- Total imports: {len(tree.imports)}"
    )

    explanations.append("\n7. ANALYSIS SUMMARY")

    explanations.append(
        "This explanation was generated using static Java "
        "source-code analysis. It identifies classes, "
        "interfaces, methods, imports, and basic relationships."
    )

    explanations.append(
        "The program was not executed, so runtime behavior "
        "cannot be guaranteed."
    )

    return "\n".join(explanations)
