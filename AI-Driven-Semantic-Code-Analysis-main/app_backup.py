
import ast
from io import BytesIO

import matplotlib.pyplot as plt
import networkx as nx
import streamlit as st

from analyzer.code_analyzer import analyze_code
from analyzer.ai_explainer import explain_code
from analyzer.java_analyzer import analyze_java_code


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="AI Code Architecture Analyzer",
    page_icon="🏗️",
    layout="wide"
)


# ==================================================
# PROFESSIONAL FRONTEND STYLING
# ==================================================

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
        max-width: 1250px;
    }

    h1 {
        font-weight: 750;
        letter-spacing: -1px;
    }

    h2, h3 {
        font-weight: 650;
    }

    [data-testid="stMetric"] {
        background-color: var(--secondary-background-color);
        border: 1px solid rgba(128, 128, 128, 0.25);
        padding: 18px;
        border-radius: 12px;
    }

    [data-testid="stFileUploader"] {
        border: 1px dashed #64748b;
        border-radius: 12px;
        padding: 12px;
    }

    .stButton > button,
    .stDownloadButton > button {
        border-radius: 8px;
        font-weight: 600;
    }

    div[data-testid="stExpander"] {
        border-radius: 10px;
    }

    section[data-testid="stSidebar"] {
        border-right: 1px solid rgba(128, 128, 128, 0.2);
    }
</style>
""", unsafe_allow_html=True)


# ==================================================
# PYTHON ARCHITECTURE DIAGRAM
# ==================================================

def create_python_architecture_png(source_code):
    tree = ast.parse(source_code)
    graph = nx.DiGraph()

    # Detect classes and their methods.
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            graph.add_node(node.name, kind="Class")

            for item in node.body:
                if isinstance(
                    item,
                    (ast.FunctionDef, ast.AsyncFunctionDef)
                ):
                    method_name = f"{node.name}.{item.name}"
                    graph.add_node(method_name, kind="Method")
                    graph.add_edge(
                        node.name,
                        method_name,
                        label="contains"
                    )

    # Detect top-level functions.
    for node in tree.body:
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            graph.add_node(node.name, kind="Function")

    # Detect functions that create class instances.
    for node in tree.body:
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            for child in ast.walk(node):
                if (
                    isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Name)
                ):
                    class_name = child.func.id

                    if (
                        class_name in graph.nodes
                        and graph.nodes[class_name].get("kind") == "Class"
                    ):
                        graph.add_edge(
                            node.name,
                            class_name,
                            label="uses"
                        )

    if not graph.nodes:
        graph.add_node("Python File", kind="File")

    positions = nx.spring_layout(graph, seed=42)

    fig, ax = plt.subplots(figsize=(12, 7))

    color_map = {
        "Class": "lightblue",
        "Method": "lightyellow",
        "Function": "lightgreen",
        "File": "lightgray"
    }

    node_colors = [
        color_map.get(
            graph.nodes[node].get("kind"),
            "lightgray"
        )
        for node in graph.nodes
    ]

    nx.draw_networkx(
        graph,
        positions,
        ax=ax,
        labels={node: node for node in graph.nodes},
        node_color=node_colors,
        node_size=2800,
        font_size=8,
        arrows=True,
        arrowsize=18
    )

    edge_labels = nx.get_edge_attributes(graph, "label")

    nx.draw_networkx_edge_labels(
        graph,
        positions,
        edge_labels=edge_labels,
        ax=ax,
        font_size=8
    )

    ax.set_title("Python Software Architecture")
    ax.axis("off")

    image_buffer = BytesIO()

    fig.savefig(
        image_buffer,
        format="png",
        bbox_inches="tight",
        dpi=160
    )

    plt.close(fig)
    image_buffer.seek(0)

    return image_buffer.getvalue()


# ==================================================
# JAVA ARCHITECTURE DIAGRAM
# ==================================================

def create_java_architecture_png(source_code):
    import javalang

    tree = javalang.parse.parse(source_code)
    graph = nx.DiGraph()

    # Detect Java classes, methods, constructors and fields.
    for _, node in tree.filter(javalang.tree.ClassDeclaration):
        graph.add_node(node.name, kind="Class")

        for method in node.methods:
            method_name = f"{node.name}.{method.name}"
            graph.add_node(method_name, kind="Method")

            graph.add_edge(
                node.name,
                method_name,
                label="contains"
            )

        for constructor in node.constructors:
            constructor_name = f"{node.name}.{constructor.name}"
            graph.add_node(constructor_name, kind="Method")

            graph.add_edge(
                node.name,
                constructor_name,
                label="contains"
            )

        for field in node.fields:
            for declarator in field.declarators:
                field_name = f"{node.name}.{declarator.name}"
                graph.add_node(field_name, kind="Field")

                graph.add_edge(
                    node.name,
                    field_name,
                    label="contains"
                )

    # Detect Java interfaces and their methods.
    for _, node in tree.filter(javalang.tree.InterfaceDeclaration):
        graph.add_node(node.name, kind="Interface")

        for method in node.methods:
            method_name = f"{node.name}.{method.name}"
            graph.add_node(method_name, kind="Method")

            graph.add_edge(
                node.name,
                method_name,
                label="declares"
            )

    # Detect object creation.
    for _, node in tree.filter(javalang.tree.ClassCreator):
        class_name = node.type.name

        if class_name not in graph.nodes:
            graph.add_node(class_name, kind="Class")

        if "Java Program" not in graph.nodes:
            graph.add_node("Java Program", kind="Program")

        graph.add_edge(
            "Java Program",
            class_name,
            label="creates"
        )

    if not graph.nodes:
        graph.add_node("Java File", kind="File")

    positions = nx.spring_layout(graph, seed=42)

    fig, ax = plt.subplots(figsize=(12, 7))

    color_map = {
        "Class": "lightblue",
        "Interface": "plum",
        "Method": "lightyellow",
        "Field": "lightgreen",
        "Program": "lightgray",
        "File": "lightgray"
    }

    node_colors = [
        color_map.get(
            graph.nodes[node].get("kind"),
            "lightgray"
        )
        for node in graph.nodes
    ]

    nx.draw_networkx(
        graph,
        positions,
        ax=ax,
        labels={node: node for node in graph.nodes},
        node_color=node_colors,
        node_size=2800,
        font_size=8,
        arrows=True,
        arrowsize=18
    )

    edge_labels = nx.get_edge_attributes(graph, "label")

    nx.draw_networkx_edge_labels(
        graph,
        positions,
        edge_labels=edge_labels,
        ax=ax,
        font_size=8
    )

    ax.set_title("Java Software Architecture")
    ax.axis("off")

    image_buffer = BytesIO()

    fig.savefig(
        image_buffer,
        format="png",
        bbox_inches="tight",
        dpi=160
    )

    plt.close(fig)
    image_buffer.seek(0)

    return image_buffer.getvalue()


# ==================================================
# APPLICATION HEADER
# ==================================================

st.title("🏗️ Code Architecture Analyzer")

st.subheader(
    "AI-Driven Semantic Code Analysis "
    "and Software Architecture Modeling System"
)

st.caption(
    "Analyze Python and Java source code, discover program "
    "structure, and visualize software architecture."
)


# ==================================================
# SIDEBAR
# ==================================================

with st.sidebar:
    st.title("⚙️ Dashboard")
    st.write("**Supported Languages**")
    st.write("🐍 Python")
    st.write("☕ Java")

    st.divider()

    st.write("**Available Features**")
    st.write("• Semantic code analysis")
    st.write("• Class and method detection")
    st.write("• Import analysis")
    st.write("• Relationship detection")
    st.write("• Architecture visualization")
    st.write("• Downloadable reports")


# ==================================================
# FILE UPLOAD
# ==================================================

uploaded_file = st.file_uploader(
    "Upload a Python or Java source file",
    type=["py", "java"],
    help="Upload a .py or .java source code file."
)

if uploaded_file is None:
    st.info(
        "👆 Upload a Python or Java file to begin code analysis."
    )

    st.markdown("### What this application provides")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 🔍 Code Analysis")
        st.write(
            "Discover classes, functions, methods and imports."
        )

    with col2:
        st.markdown("#### 🏗️ Architecture")
        st.write(
            "Generate a visual representation of code structure."
        )

    with col3:
        st.markdown("#### 📄 Reports")
        st.write(
            "Review and download analysis results."
        )


# ==================================================
# ANALYZE UPLOADED FILE
# ==================================================

if uploaded_file is not None:

    try:
        source_code = uploaded_file.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        st.error(
            "The file could not be decoded as UTF-8. "
            "Please upload a valid source code file."
        )
        st.stop()

    extension = uploaded_file.name.rsplit(".", 1)[-1].lower()

    language = "Java" if extension == "java" else "Python"

    st.divider()

    col_file, col_language = st.columns(2)

    with col_file:
        st.success(f"📄 File: {uploaded_file.name}")

    with col_language:
        st.info(f"💻 Language: {language}")

    with st.expander("View Source Code", expanded=False):
        st.code(source_code, language=language.lower())

    # ----------------------------------------------
    # RUN THE CORRECT ANALYZER
    # ----------------------------------------------

    st.header("📊 Semantic Code Analysis")

    try:
        if language == "Java":
            result = analyze_java_code(source_code)
        else:
            result = analyze_code(source_code)

    except Exception as error:
        st.error(f"Code analysis failed: {error}")
        st.stop()

    if result.get("error"):
        st.error(result["error"])
        st.stop()

    classes = result.get("classes", [])
    functions = result.get("functions", [])
    imports = result.get("imports", [])
    relationships = result.get("relationships", [])

    # ----------------------------------------------
    # ANALYSIS OVERVIEW
    # ----------------------------------------------

    st.subheader("📈 Analysis Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Classes",
        len(classes)
    )

    col2.metric(
        "Functions / Methods",
        len(functions)
    )

    col3.metric(
        "Imports",
        len(imports)
    )

    col4.metric(
        "Relationships",
        len(relationships)
    )

    st.divider()

    # ----------------------------------------------
    # ORGANIZED ANALYSIS TABS
    # ----------------------------------------------

    tab_results, tab_diagram, tab_explanation, tab_report = st.tabs(
        [
            "📋 Analysis Results",
            "🏗️ Architecture Diagram",
            "💡 Code Explanation",
            "📥 Download Report"
        ]
    )

    # ==============================================
    # TAB 1: ANALYSIS RESULTS
    # ==============================================

    with tab_results:

        st.subheader("Classes")

        
# ==================================================
# ORGANIZED DASHBOARD TABS
# ==================================================

tab_results, tab_diagram, tab_explanation, tab_report = st.tabs([
    "📋 Analysis Results",
    "🏗️ Architecture Diagram",
    "💡 Code Explanation",
    "📥 Download Report"
])


# ==================================================
# TAB 1: ANALYSIS RESULTS
# ==================================================

with tab_results:
    st.subheader("📊 Analysis Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Classes", len(classes))
    col2.metric("Functions / Methods", len(functions))
    col3.metric("Imports", len(imports))
    col4.metric("Relationships", len(relationships))

    st.divider()

    st.subheader("Classes")
    if classes:
        for name in classes:
            st.write(f"• {name}")
    else:
        st.info("No classes found.")

    st.subheader("Methods / Functions")
    if functions:
        for name in functions:
            st.write(f"• {name}")
    else:
        st.info("No methods or functions found.")

    st.subheader("Imports")
    if imports:
        for name in imports:
            st.write(f"• {name}")
    else:
        st.info("No imports found.")

    st.subheader("Relationships")
    if relationships:
        for relationship in relationships:
            st.write(f"• {relationship}")
    else:
        st.info("No relationships found.")

    st.success("Code analysis completed!")


# ==================================================
# TAB 2: ARCHITECTURE DIAGRAM
# ==================================================

with tab_diagram:
    st.subheader("Software Architecture Diagram")
    st.caption(
    "Visual representation of the classes, methods, "
    "functions, and relationships detected in your code."
)

with st.expander("Diagram Legend", expanded=True):
    col1, col2, col3, col4 = st.columns(4)

    col1.markdown("🔵 **Class**")
    col2.markdown("🟡 **Method**")
    col3.markdown("🟢 **Function / Field**")
    col4.markdown("🟣 **Interface**")

    try:
        if language == "Java":
            png_data = create_java_architecture_png(source_code)
        else:
            png_data = create_python_architecture_png(source_code)

        st.image(
            png_data,
            caption=f"{language} Software Architecture",
            use_container_width=True
        )

        st.download_button(
            label="Download Architecture Diagram (PNG)",
            data=png_data,
            file_name=(
                f"{uploaded_file.name.rsplit('.', 1)[0]}"
                "_architecture.png"
            ),
            mime="image/png",
            key="download_architecture"
        )

    except Exception as error:
        st.error(f"Could not generate diagram: {error}")


# ==================================================
# TAB 3: CODE EXPLANATION
# ==================================================

with tab_explanation:
    st.subheader("Code Explanation")

    try:
        if language == "Python":
            explanation = explain_code(source_code)
        else:
            explanation = (
                "### Java Code Structure Summary\n\n"
                f"- **File:** `{uploaded_file.name}`\n"
                f"- **Classes detected:** {len(classes)}\n"
                f"- **Methods detected:** {len(functions)}\n"
                f"- **Imports detected:** {len(imports)}\n"
                f"- **Relationships detected:** {len(relationships)}\n\n"
                "This is a structural summary, not a full "
                "AI-generated explanation of Java program logic."
            )

        st.markdown(explanation)

    except Exception as error:
        explanation = f"Could not generate explanation: {error}"
        st.error(explanation)


# ==================================================
# TAB 4: DOWNLOAD REPORT
# ==================================================

with tab_report:
    st.subheader("Download Analysis Report")

    # Generate the explanation if the report tab is used
    # before the explanation tab has been visited.
    if "explanation" not in locals():
        if language == "Python":
            try:
                explanation = explain_code(source_code)
            except Exception as error:
                explanation = f"Explanation unavailable: {error}"
        else:
            explanation = (
                "Java structural summary: "
                f"{len(classes)} classes, "
                f"{len(functions)} methods/functions, "
                f"{len(imports)} imports."
            )

    report = f"""AI-Driven Semantic Code Analysis
===================================

Uploaded File: {uploaded_file.name}
Language: {language}

ANALYSIS OVERVIEW
-----------------
Classes: {len(classes)}
Functions / Methods: {len(functions)}
Imports: {len(imports)}
Relationships: {len(relationships)}

CLASSES
-------
{chr(10).join(str(item) for item in classes) or 'No classes found.'}

FUNCTIONS / METHODS
-------------------
{chr(10).join(str(item) for item in functions) or 'No functions or methods found.'}

IMPORTS
-------
{chr(10).join(str(item) for item in imports) or 'No imports found.'}

RELATIONSHIPS
-------------
{chr(10).join(str(item) for item in relationships) or 'No relationships found.'}

CODE EXPLANATION
----------------
{explanation}
"""

    st.download_button(
        label="Download Analysis Report (TXT)",
        data=report,
        file_name=(
            f"{uploaded_file.name.rsplit('.', 1)[0]}"
            "_analysis_report.txt"
        ),
        mime="text/plain",
        key="download_report"
    )
