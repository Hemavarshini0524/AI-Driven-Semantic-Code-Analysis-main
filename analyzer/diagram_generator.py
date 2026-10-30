
import ast
import javalang
import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO


def create_graph_image(graph, title="Software Architecture"):
    if len(graph.nodes) == 0:
        graph.add_node("No components found", kind="File")

    fig, ax = plt.subplots(figsize=(14, 9))

    positions = nx.spring_layout(
        graph,
        seed=42,
        k=1.5
    )

    colors = {
        "Class": "lightblue",
        "Method": "lightyellow",
        "Function": "lightgreen",
        "Field": "lightpink",
        "Interface": "plum",
        "File": "lightgray"
    }

    node_colors = [
        colors.get(
            graph.nodes[node].get("kind"),
            "lightgray"
        )
        for node in graph.nodes
    ]

    nx.draw_networkx(
        graph,
        positions,
        ax=ax,
        with_labels=True,
        node_color=node_colors,
        node_size=2800,
        font_size=8,
        font_weight="bold",
        arrows=True,
        arrowsize=18,
        edge_color="gray"
    )

    edge_labels = nx.get_edge_attributes(graph, "label")

    nx.draw_networkx_edge_labels(
        graph,
        positions,
        edge_labels=edge_labels,
        ax=ax,
        font_size=7
    )

    ax.set_title(title, fontsize=15)
    ax.axis("off")

    fig.tight_layout()

    image_buffer = BytesIO()

    fig.savefig(
        image_buffer,
        format="png",
        dpi=200,
        bbox_inches="tight"
    )

    plt.close(fig)

    image_buffer.seek(0)

    return image_buffer.getvalue()


def generate_python_graph(source_code):
    tree = ast.parse(source_code)
    graph = nx.DiGraph()

    class_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    }

    # Create class nodes and inheritance relationships
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            graph.add_node(node.name, kind="Class")

            for base in node.bases:
                if isinstance(base, ast.Name):
                    graph.add_node(base.id, kind="Class")
                    graph.add_edge(
                        node.name,
                        base.id,
                        label="inherits"
                    )

            # Add methods
            for item in node.body:
                if isinstance(
                    item,
                    (ast.FunctionDef, ast.AsyncFunctionDef)
                ):
                    method_id = f"{node.name}.{item.name}"

                    graph.add_node(method_id, kind="Method")
                    graph.add_edge(
                        node.name,
                        method_id,
                        label="contains"
                    )

    # Add standalone functions
    for node in tree.body:
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            graph.add_node(node.name, kind="Function")

    # Analyze class methods
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        class_name = node.name

        for method in node.body:
            if not isinstance(
                method,
                (ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                continue

            current = f"{class_name}.{method.name}"
            variable_types = {}

            # Detect object creation and attribute composition
            for child in ast.walk(method):
                if isinstance(child, ast.Assign):
                    if isinstance(child.value, ast.Call):
                        if isinstance(child.value.func, ast.Name):
                            target_class = child.value.func.id

                            if target_class in class_names:
                                for target in child.targets:
                                    if isinstance(target, ast.Name):
                                        variable_types[target.id] = target_class

                                    elif (
                                        isinstance(target, ast.Attribute)
                                        and isinstance(target.value, ast.Name)
                                        and target.value.id == "self"
                                    ):
                                        field_id = (
                                            f"{class_name}.{target.attr}"
                                        )
                                        graph.add_node(
                                            field_id,
                                            kind="Field"
                                        )
                                        graph.add_edge(
                                            class_name,
                                            field_id,
                                            label="contains"
                                        )
                                        graph.add_edge(
                                            class_name,
                                            target_class,
                                            label="composes"
                                        )

                                graph.add_edge(
                                    current,
                                    target_class,
                                    label="creates"
                                )

                # Detect self.method() calls
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Attribute):
                        if isinstance(child.func.value, ast.Name):
                            object_name = child.func.value.id
                            method_name = child.func.attr

                            if object_name == "self":
                                target = f"{class_name}.{method_name}"

                                if target in graph.nodes:
                                    graph.add_edge(
                                        current,
                                        target,
                                        label="calls"
                                    )

                            elif object_name in variable_types:
                                target_class = variable_types[object_name]
                                target = f"{target_class}.{method_name}"

                                if target in graph.nodes:
                                    graph.add_edge(
                                        current,
                                        target,
                                        label="calls"
                                    )

    # Analyze standalone functions
    for node in tree.body:
        if not isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue

        function_name = node.name
        variable_types = {}

        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                if isinstance(child.value, ast.Call):
                    if isinstance(child.value.func, ast.Name):
                        target_class = child.value.func.id

                        if target_class in class_names:
                            for target in child.targets:
                                if isinstance(target, ast.Name):
                                    variable_types[target.id] = target_class

                            graph.add_edge(
                                function_name,
                                target_class,
                                label="creates"
                            )

            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    if isinstance(child.func.value, ast.Name):
                        object_name = child.func.value.id

                        if object_name in variable_types:
                            target_class = variable_types[object_name]
                            target = (
                                f"{target_class}.{child.func.attr}"
                            )

                            if target in graph.nodes:
                                graph.add_edge(
                                    function_name,
                                    target,
                                    label="calls"
                                )

    return graph


def generate_java_graph(source_code):
    tree = javalang.parse.parse(source_code)
    graph = nx.DiGraph()

    class_names = set()
    interface_names = set()

    # Identify Java classes
    for _, node in tree.filter(javalang.tree.ClassDeclaration):
        class_names.add(node.name)

    # Identify Java interfaces
    for _, node in tree.filter(javalang.tree.InterfaceDeclaration):
        interface_names.add(node.name)

    # Add classes and relationships
    for _, node in tree.filter(javalang.tree.ClassDeclaration):
        class_name = node.name
        graph.add_node(class_name, kind="Class")

        if node.extends:
            parent = node.extends.name
            graph.add_node(parent, kind="Class")
            graph.add_edge(
                class_name,
                parent,
                label="inherits"
            )

        if node.implements:
            for interface in node.implements:
                graph.add_node(
                    interface.name,
                    kind="Interface"
                )
                graph.add_edge(
                    class_name,
                    interface.name,
                    label="implements"
                )

        # Detect fields and their types
        field_types = {}

        for field in node.fields:
            field_type = field.type.name

            for declarator in field.declarators:
                field_id = f"{class_name}.{declarator.name}"

                graph.add_node(field_id, kind="Field")
                graph.add_edge(
                    class_name,
                    field_id,
                    label="contains"
                )

                field_types[declarator.name] = field_type

                if field_type in class_names:
                    graph.add_edge(
                        class_name,
                        field_type,
                        label="composes"
                    )

        # Add methods
        for method in node.methods:
            method_id = f"{class_name}.{method.name}"

            graph.add_node(method_id, kind="Method")
            graph.add_edge(
                class_name,
                method_id,
                label="contains"
            )

            analyze_java_member(
                graph,
                method,
                method_id,
                class_name,
                class_names,
                field_types
            )

        # Add constructors
        for constructor in node.constructors:
            constructor_id = (
                f"{class_name}.{constructor.name}"
            )

            graph.add_node(constructor_id, kind="Method")
            graph.add_edge(
                class_name,
                constructor_id,
                label="contains"
            )

            analyze_java_member(
                graph,
                constructor,
                constructor_id,
                class_name,
                class_names,
                field_types
            )

    # Add interfaces and their methods
    for _, node in tree.filter(javalang.tree.InterfaceDeclaration):
        graph.add_node(node.name, kind="Interface")

        for method in node.methods:
            method_id = f"{node.name}.{method.name}"

            graph.add_node(method_id, kind="Method")
            graph.add_edge(
                node.name,
                method_id,
                label="declares"
            )

    return graph


def analyze_java_member(
    graph,
    member,
    member_id,
    class_name,
    class_names,
    field_types
):
    variable_types = dict(field_types)

    if not member.body:
        return

    # Detect local variable declarations
    for _, declaration in member.filter(
        javalang.tree.LocalVariableDeclaration
    ):
        variable_type = declaration.type.name

        for declarator in declaration.declarators:
            variable_types[declarator.name] = variable_type

            if variable_type in class_names:
                graph.add_edge(
                    member_id,
                    variable_type,
                    label="depends on"
                )

    # Detect object creation
    for _, creator in member.filter(
        javalang.tree.ClassCreator
    ):
        target_class = creator.type.name

        graph.add_node(target_class, kind="Class")
        graph.add_edge(
            member_id,
            target_class,
            label="creates"
        )

    # Detect method calls
    for _, invocation in member.filter(
        javalang.tree.MethodInvocation
    ):
        qualifier = invocation.qualifier

        if qualifier == "this":
            target = f"{class_name}.{invocation.member}"

            if target in graph.nodes:
                graph.add_edge(
                    member_id,
                    target,
                    label="calls"
                )

        elif qualifier in variable_types:
            target_class = variable_types[qualifier]
            target = f"{target_class}.{invocation.member}"

            if target in graph.nodes:
                graph.add_edge(
                    member_id,
                    target,
                    label="calls"
                )


def generate_diagram(source_code, language="python"):
    language = language.lower()

    if language == "python":
        graph = generate_python_graph(source_code)

    elif language == "java":
        graph = generate_java_graph(source_code)

    else:
        raise ValueError(
            "Unsupported language. Use 'python' or 'java'."
        )

    title = f"{language.title()} Software Architecture"

    return create_graph_image(graph, title)
