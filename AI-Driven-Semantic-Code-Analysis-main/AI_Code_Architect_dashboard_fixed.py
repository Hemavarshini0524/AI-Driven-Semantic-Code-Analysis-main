import streamlit as st

from pathlib import Path

import zipfile

import ast

import re

import textwrap

from io import BytesIO

import matplotlib.pyplot as plt

import networkx as nx

from analyzer.code_analyzer import analyze_code

from analyzer.ai_explainer import explain_code

from analyzer.java_analyzer import analyze_java_code

from analyzer.java_explainer import explain_java_code

from analyzer.diagram_generator import generate_diagram

from analyzer.project_analyzer import analyze_project

def create_project_architecture_diagram(project_files, dependencies):

    """

    Draw a file-level architecture/dependency diagram for a ZIP project.

    This is a project dependency diagram, not a class-level UML diagram.

    """

    graph = nx.DiGraph()

    for filename in project_files:

        graph.add_node(str(filename))

    for dependency in dependencies:

        if not isinstance(dependency, dict):

            continue

        source_file = dependency.get("source")

        target_file = dependency.get("target")

        relationship = dependency.get("relationship", "depends on")

        if source_file and target_file:

            graph.add_edge(

                str(source_file),

                str(target_file),

                label=str(relationship)

            )

    figure_width = max(9, min(16, 2.2 * max(1, len(graph.nodes))))

    figure_height = max(5, min(12, 1.3 * max(1, len(graph.nodes))))

    fig, ax = plt.subplots(figsize=(figure_width, figure_height))

    try:

        if len(graph.nodes) == 0:

            ax.text(0.5, 0.5, "No source files to display", ha="center", va="center")

            ax.axis("off")

        else:

            if len(graph.nodes) <= 12:

                positions = nx.spring_layout(graph, seed=42, k=1.4)

            else:

                positions = nx.kamada_kawai_layout(graph)

            nx.draw_networkx_nodes(

                graph, positions, ax=ax,

                node_size=2600, node_color="#DCEBFF",

                edgecolors="#2457A7", linewidths=1.5

            )

            nx.draw_networkx_labels(

                graph, positions, ax=ax,

                font_size=8, font_weight="bold"

            )

            if graph.number_of_edges():

                nx.draw_networkx_edges(

                    graph, positions, ax=ax,

                    arrows=True, arrowstyle="-|>", arrowsize=18,

                    edge_color="#52657A", width=1.6,

                    connectionstyle="arc3,rad=0.08",

                    min_source_margin=18, min_target_margin=18

                )

                edge_labels = nx.get_edge_attributes(graph, "label")

                nx.draw_networkx_edge_labels(

                    graph, positions, edge_labels=edge_labels,

                    ax=ax, font_size=7, rotate=False,

                    label_pos=0.5

                )

            else:

                ax.text(

                    0.5, 0.02,

                    "No cross-file dependency edges were detected.",

                    transform=ax.transAxes, ha="center", fontsize=9

                )

            ax.set_title(

                "Project File Dependency Architecture",

                fontsize=14, fontweight="bold", pad=18

            )

            ax.axis("off")

        fig.tight_layout()

        image_buffer = BytesIO()

        fig.savefig(image_buffer, format="png", dpi=180, bbox_inches="tight")

        image_buffer.seek(0)

        return image_buffer.getvalue()

    finally:

        plt.close(fig)

def extract_project_classes(source_files):

    """Extract class names, attributes, methods and inheritance from Python/Java files."""

    records = []

    for filename, source in source_files.items():

        suffix = Path(filename).suffix.lower()

        if suffix == ".py":

            try:

                tree = ast.parse(source)

            except SyntaxError:

                continue

            for node in ast.walk(tree):

                if isinstance(node, ast.ClassDef):

                    methods = [

                        child.name for child in node.body

                        if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))

                    ]

                    attributes = sorted({

                        target.attr

                        for child in ast.walk(node)

                        if isinstance(child, (ast.Assign, ast.AnnAssign))

                        for target in (

                            child.targets if isinstance(child, ast.Assign)

                            else [child.target]

                        )

                        for target in (ast.walk(target) if isinstance(target, ast.Attribute) else [])

                        if isinstance(target, ast.Attribute) and isinstance(target.value, ast.Name)

                        and target.value.id == "self"

                    })

                    bases = [

                        base.id for base in node.bases if isinstance(base, ast.Name)

                    ] + [

                        base.attr for base in node.bases if isinstance(base, ast.Attribute)

                    ]

                    records.append({

                        "name": node.name, "file": filename,

                        "methods": methods[:8], "attributes": attributes[:8],

                        "bases": bases

                    })

        elif suffix == ".java":

            class_pattern = re.compile(

                r'\b(?:class|interface|enum)\s+([A-Za-z_$][\w$]*)'

                r'(?:\s+extends\s+([A-Za-z_$][\w$]*))?'

            )

            for match in class_pattern.finditer(source):

                name, base = match.groups()

                # Approximate member extraction within the class body.

                start = match.end()

                brace = source.find("{", start)

                body = ""

                if brace >= 0:

                    depth = 0

                    for i in range(brace, len(source)):

                        if source[i] == "{":

                            depth += 1

                        elif source[i] == "}":

                            depth -= 1

                            if depth == 0:

                                body = source[brace + 1:i]

                                break

                methods = re.findall(

                    r'\b(?:public|protected|private)?\s*(?:static\s+)?'

                    r'[\w<>\[\],.?]+\s+(\w+)\s*\([^;{}]*\)\s*\{',

                    body

                )

                records.append({

                    "name": name, "file": filename,

                    "methods": methods[:8], "attributes": [], "bases": [base] if base else []

                })

    return records

def create_combined_class_uml(source_files):

    """Render a compact class-level UML-style diagram from extracted source declarations."""

    classes = extract_project_classes(source_files)

    if not classes:

        return None, classes

    graph = nx.DiGraph()

    by_name = {item["name"]: item for item in classes}

    for item in classes:

        graph.add_node(item["name"])

        for base in item["bases"]:

            if base in by_name:

                graph.add_edge(item["name"], base, label="inherits")

    # Show likely associations where a class refers to another class in its file.

    for item in classes:

        source = source_files.get(item["file"], "")

        for other in classes:

            if other["name"] != item["name"] and other["name"] in source:

                if not graph.has_edge(item["name"], other["name"]):

                    graph.add_edge(item["name"], other["name"], label="uses")

    width = max(10, min(18, 3.2 * len(classes)))

    height = max(6, min(14, 2.2 * len(classes)))

    fig, ax = plt.subplots(figsize=(width, height))

    try:

        if len(classes) == 1:

            positions = {classes[0]["name"]: (0, 0)}

        else:

            positions = nx.spring_layout(graph, seed=17, k=2.0)

        nx.draw_networkx_edges(

            graph, positions, ax=ax, arrows=True, arrowstyle="-|>",

            arrowsize=18, edge_color="#53677F", width=1.5,

            connectionstyle="arc3,rad=0.08"

        )

        for item in classes:

            name = item["name"]

            attrs = "\n".join(f"- {x}" for x in item["attributes"]) or "- (not extracted)"

            methods = "\n".join(f"+ {x}()" for x in item["methods"]) or "+ (no methods found)"

            label = f"{name}\n{item['file']}\n{'─' * 22}\n{attrs}\n{'─' * 22}\n{methods}"

            x, y = positions[name]

            ax.text(

                x, y, label, ha="center", va="center", fontsize=7,

                bbox=dict(boxstyle="round,pad=0.6", facecolor="#E8F1FF",

                          edgecolor="#2457A7", linewidth=1.4)

            )

        if graph.number_of_edges():

            nx.draw_networkx_edge_labels(

                graph, positions, edge_labels=nx.get_edge_attributes(graph, "label"),

                ax=ax, font_size=8, rotate=False

            )

        ax.set_title("Combined Project Class Diagram (UML-style)", fontsize=14, fontweight="bold")

        ax.axis("off")

        fig.tight_layout()

        output = BytesIO()

        fig.savefig(output, format="png", dpi=180, bbox_inches="tight")

        output.seek(0)

        return output.getvalue(), classes

    finally:

        plt.close(fig)

def explain_combined_class_uml(classes):

    if not classes:

        return "No class declarations were extracted from the supported source files."

    lines = [

        f"Detected **{len(classes)} class/interface/enum declaration(s)** across the uploaded project.",

        "The diagram shows extracted class names, source files, selected attributes, methods and recognized inheritance."

    ]

    for item in classes:

        lines.append(

            f"- **{item['name']}** in \`{item['file']}\`: "

            f"{len(item['attributes'])} attribute(s), {len(item['methods'])} method(s)."

        )

        for base in item["bases"]:

            lines.append(f"  - Inherits from \`{base}\`.")

    lines.append(

        "\nThis is a static, UML-style approximation. Python attributes and Java members "

        "are extracted using syntax/structural patterns; dynamic relationships and some "

        "complex Java syntax may not be represented."

    )

    return "\n".join(lines)

def explain_project_architecture(project_files, dependencies, project_errors):

    """Explain the file-level architecture using the analyzer's reported results."""

    lines = [

        "### Project architecture overview",

        f"The ZIP contains **{len(project_files)} supported source file(s)**.",

        f"The analyzer detected **{len(dependencies)} cross-file relationship(s)**."

    ]

    if dependencies:

        lines.append("\n### What the relationships mean")

        for item in dependencies:

            if not isinstance(item, dict):

                continue

            source = item.get("source", "Unknown source")

            target = item.get("target", "Unknown target")

            relation = item.get("relationship", "depends on")

            lines.append(f"- \`{source}\` **{relation}** \`{target}\`.")

    else:

        lines.append(

            "\nNo cross-file relationships were detected. The files may be "

            "independent, or their relationships may not be recognized by the analyzer."

        )

    lines.append("\n### Files included")

    for filename in project_files:

        lines.append(f"- \`{filename}\`")

    lines.append("\n### Analysis notes")

    if project_errors:

        lines.append(

            f"The analyzer reported **{len(project_errors)} warning(s)**. "

            "Review the warnings in the analysis results."

        )

    else:

        lines.append("The analyzer reported no parsing warnings for this project.")

    lines.append(

        "\n**Diagram scope:** This is a file-level project architecture diagram. "

        "Its nodes represent source files and its arrows represent detected "

        "cross-file dependencies. It is not a class-level UML diagram."

    )

    return "\n".join(lines)

def explain_uml_diagram(classes, functions, relationships, imports):

    """Create a plain-language explanation from detected source-code elements."""

    sections = []

    sections.append("### 1. Architecture overview")

    if classes:

        class_names = ", ".join(str(name) for name in classes)

        sections.append(

            f"The analyzer detected {len(classes)} class(es): {class_names}."

        )

    else:

        sections.append(

            "No classes were detected. The diagram may therefore show "

            "functions or other source-code elements instead."

        )

    sections.append("\n### 2. Classes")

    if classes:

        for class_name in classes:

            sections.append(

                f"- **{class_name}** is a class identified in the uploaded source file. "

                "Its exact responsibility depends on the code inside the class."

            )

    else:

        sections.append("- No classes were detected.")

    sections.append("\n### 3. Methods and functions")

    if functions:

        sections.append(

            f"The analyzer detected {len(functions)} method(s) or function(s):"

        )

        for function_name in functions:

            sections.append(f"- \`{function_name}\`")

    else:

        sections.append("- No methods or functions were detected.")

    sections.append("\n### 4. Relationships")

    if relationships:

        for relationship in relationships:

            sections.append(f"- {relationship}")

        sections.append(

            "These are the relationships reported by the static analyzer."

        )

    else:

        sections.append(

            "The analyzer did not detect any explicit class relationships "

            "in this file. This does not necessarily mean that no relationships exist."

        )

    sections.append("\n### 5. Imported dependencies")

    if imports:

        for imported_module in imports:

            sections.append(f"- \`{imported_module}\`")

        sections.append(

            "Imports show which external or other code modules this file refers to."

        )

    else:

        sections.append("- No imports were detected.")

    sections.append("\n### 6. Overall interpretation")

    sections.append(

        "The UML-style diagram is a structural view of the elements detected "

        "in the uploaded source code. Use the class, method, relationship and "

        "dependency details above to understand how the detected parts fit together. "

        "This explanation is generated from static-analysis results; it is not "

        "a generative-AI interpretation."

    )

    return "\n".join(sections)

# ==================================================

# PAGE CONFIGURATION

# ==================================================

st.set_page_config(

    page_title="AI Code Architect",

    page_icon="🏗️",

    layout="wide"

)

# ==================================================

# CUSTOM FRONTEND STYLING

# ==================================================

css_path = Path(__file__).parent / "styles.css"

if css_path.exists():

    with open(css_path, "r", encoding="utf-8") as css_file:

        st.markdown(

            f"<style>{css_file.read()}</style>",

            unsafe_allow_html=True

        )

# ==================================================

# Consistent dashboard styling; overrides older styles.css rules.

st.markdown("<style>\n" + r""":root{--navy:#17233f;--purple:#7055b5;--purple-dark:#594196;--ink:#202b40;--muted:#66748a;--canvas:#f5f6fb;--line:#e4e7f0}

.stApp,[data-testid="stAppViewContainer"]>.main{background:var(--canvas);color:var(--ink)}

.block-container{max-width:1420px;padding:1.8rem 2.4rem 3rem}

[data-testid="stSidebar"]{background:#edf0f8;border-right:1px solid #e0e4ef}

[data-testid="stSidebar"]>div:first-child{padding:1.4rem 1rem}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,[data-testid="stSidebar"] label{color:#27344d!important}

[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3{color:var(--navy)!important}

.main-header{display:flex;align-items:center;gap:20px;padding:25px 30px;margin:0 0 22px;border-radius:16px;color:#fff;background:linear-gradient(112deg,#17233f 0%,#293b62 68%,#49396f 100%);box-shadow:0 8px 22px rgba(23,35,63,.12)}

.main-header h1{color:#fff!important;font-size:2rem!important;margin:0!important;letter-spacing:-.5px}

.main-header p{color:#dce3f2!important;margin:7px 0 0!important;font-size:.98rem}

.header-icon{display:flex;align-items:center;justify-content:center;width:58px;height:58px;border-radius:13px;background:rgba(255,255,255,.12);font-size:30px}

.welcome-section{background:#fff;border:1px solid var(--line);border-left:4px solid var(--purple);border-radius:13px;padding:18px 22px;margin-bottom:24px;box-shadow:0 3px 12px rgba(25,35,60,.035)}

.welcome-section h2{color:var(--navy)!important;font-size:1.35rem!important;margin:0 0 7px!important}

.welcome-section p{color:var(--muted)!important;margin:0!important;line-height:1.6}

h1,h2,h3{color:var(--navy)!important;letter-spacing:-.25px}h1{font-size:2rem!important}h2{font-size:1.55rem!important}h3{font-size:1.18rem!important}

[data-testid="stFileUploader"]{background:#fff;border:1px solid #dfe3ef;border-radius:12px;padding:12px}

[data-testid="stFileUploader"] section{background:#f7f8fc;border:1px dashed #c9c3e2;border-radius:9px}

[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:12px;padding:16px 18px;box-shadow:0 3px 12px rgba(25,35,60,.035)}

[data-testid="stMetricLabel"]{color:var(--muted)!important}[data-testid="stMetricValue"]{color:var(--purple-dark)!important;font-weight:750}

.stButton>button,.stDownloadButton>button{background:var(--purple)!important;color:#fff!important;border:1px solid var(--purple)!important;border-radius:9px!important;min-height:44px;font-weight:650!important;padding:.55rem 1rem!important}

.stButton>button *,.stDownloadButton>button *{color:#fff!important;opacity:1!important}

.stButton>button:hover,.stDownloadButton>button:hover{background:var(--purple-dark)!important;border-color:var(--purple-dark)!important}

[data-testid="stExpander"],[data-testid="stDataFrame"],[data-testid="stTable"]{border-radius:11px}

.stTabs [data-baseweb="tab-list"]{gap:8px;border-bottom:1px solid var(--line)}

.stTabs [data-baseweb="tab"]{background:#eeebf7;border-radius:8px 8px 0 0;padding:9px 15px}

.stTabs [aria-selected="true"]{background:#ded6f0!important;color:#3d2b70!important}

[data-testid="stAlert"]{border-radius:10px}hr{border-color:var(--line)!important}

@media(max-width:900px){.block-container{padding:1rem 1rem 2rem}.main-header{padding:18px}.main-header h1{font-size:1.5rem!important}}

""" + "\n</style>", unsafe_allow_html=True)

# MODERN DASHBOARD HEADER

# ==================================================

st.html(

    textwrap.dedent("""

    <div class="main-header">

        <div class="header-icon">🏗️</div>

        <div>

            <h1>AI Code Architect</h1>

            <p>Semantic Code Analysis & Software Architecture Modeling</p>

        </div>

    </div>

    """),

    unsafe_allow_html=True

)

st.html(

    textwrap.dedent("""

    <div class="welcome-section">

        <h2>Welcome to Code Analysis Studio 👋</h2>

        <p>

            Transform your source code into meaningful insights.

            Analyze Python and Java programs, explore relationships,

            and visualize software architecture.

        </p>

    </div>

    """),

    unsafe_allow_html=True

)

# ==================================================

# SIDEBAR

# ==================================================

with st.sidebar:

    st.markdown("## 🏗️ AI Code Architect")

    st.caption("Software Architecture Analysis")

    st.divider()

    st.markdown("### Navigation")

    page = st.radio(

        "Choose a section",

        ["Code Analyzer", "About Project"],

        label_visibility="collapsed"

    )

    st.divider()

    st.markdown("### Supported Languages")

    st.markdown("🐍 Python")

    st.markdown("☕ Java")

    st.divider()

    st.caption("AI-Driven Semantic Code Analysis")

# ==================================================

# ABOUT PROJECT PAGE

# ==================================================

if page == "About Project":

    st.header("About the Project")

    st.write(

        """

        AI-Driven Semantic Code Analysis and Automated Software

        Architecture Modeling System helps developers understand

        source code structure and visualize software relationships.

        """

    )

    st.subheader("Main Features")

    st.markdown(

        """

        \\- Python source code analysis

        \\- Java source code analysis

        \\- Class and function detection

        \\- Import identification

        \\- Relationship detection

        \\- Architecture diagram generation

        \\- Rule-based code explanation

        \\- Downloadable analysis reports

        """

    )

    st.info(

        "Upload Python or Java source files in the Code Analyzer section."

    )

# ==================================================

# MAIN CODE ANALYZER

# ==================================================

else:

    st.header("Code Analysis Workspace")

    st.write(

        "Upload a complete project ZIP to inspect dependencies across files, "

        "or upload one Python/Java file for detailed analysis."

    )

    # --------------------------------------------------

    # MULTI-FILE PROJECT ANALYSIS

    # --------------------------------------------------

    st.subheader("📁 Analyze an Entire Project")

    project_zip = st.file_uploader(

        "Upload project as a ZIP file",

        type=["zip"],

        help="ZIP should contain .py and/or .java source files."

    )

    if project_zip is not None:

        try:

            source_files = {}

            total_uncompressed_size = 0

            max_files = 200

            max_total_size = 20 * 1024 * 1024

            with zipfile.ZipFile(BytesIO(project_zip.getvalue())) as archive:

                for item in archive.infolist():

                    if item.is_dir():

                        continue

                    # Ignore operating-system metadata and hidden folders.

                    parts = Path(item.filename).parts

                    if any(part.startswith(".") or part == "__MACOSX" for part in parts):

                        continue

                    extension = Path(item.filename).suffix.lower()

                    if extension not in {".py", ".java"}:

                        continue

                    if len(source_files) >= max_files:

                        st.warning(f"Only the first {max_files} supported source files are analyzed.")

                        break

                    total_uncompressed_size += item.file_size

                    if total_uncompressed_size > max_total_size:

                        raise ValueError("The ZIP contains more than 20 MB of supported source files.")

                    if item.file_size > 2 * 1024 * 1024:

                        st.warning(f"Skipped {item.filename}: file is larger than 2 MB.")

                        continue

                    try:

                        source_files[item.filename] = archive.read(item).decode("utf-8")

                    except UnicodeDecodeError:

                        st.warning(f"Skipped {item.filename}: it is not UTF-8 text.")

            if not source_files:

                st.warning("No readable Python (.py) or Java (.java) files were found in this ZIP.")

            else:

                st.info(f"Found {len(source_files)} supported source file(s). Analyzing project...")

                project_result = analyze_project(source_files)

                if project_result.get("error"):

                    st.error(project_result["error"])

                else:

                    st.success("Multi-file project analysis completed.")

                    project_files = project_result.get("files", [])

                    project_dependencies = project_result.get("dependencies", [])

                    project_errors = project_result.get("errors", [])

                    metric_a, metric_b, metric_c = st.columns(3)

                    metric_a.metric("Source files", len(project_files))

                    metric_b.metric("Dependencies", len(project_dependencies))

                    metric_c.metric("Analysis warnings", len(project_errors))

                    st.subheader("📄 Files analyzed")

                    st.write(project_files)

                    st.subheader("🔗 Cross-file relationships")

                    if project_dependencies:

                        st.dataframe(project_dependencies, use_container_width=True)

                    else:

                        st.info(

                            "No cross-file dependencies were detected. "

                            "This can happen when files do not import, inherit from, "

                            "or create objects from classes in other uploaded files."

                        )

                    st.subheader("🧭 File dependency summary")

                    for detail in project_result.get("file_details", []):

                        with st.expander(detail["filename"]):

                            if detail["dependencies"]:

                                for dependency in detail["dependencies"]:

                                    st.markdown(f"- \`{dependency}\`")

                            else:

                                st.caption("No outgoing file dependencies detected.")

                    # --------------------------------------------------

                    # PROJECT-LEVEL ARCHITECTURE DIAGRAM

                    # --------------------------------------------------

                    st.subheader("🏗️ Project Architecture Diagram")

                    st.caption(

                        "This diagram shows source files and the cross-file "

                        "dependencies detected by the project analyzer."

                    )

                    try:

                        project_diagram = create_project_architecture_diagram(

                            project_files,

                            project_dependencies

                        )

                        st.image(

                            project_diagram,

                            caption="Project File Dependency Architecture"

                        )

                        st.download_button(

                            "⬇️ Download Project Architecture Diagram",

                            data=project_diagram,

                            file_name="project_architecture.png",

                            mime="image/png",

                            key="project_architecture_download"

                        )

                    except Exception as diagram_error:

                        st.error(

                            f"Could not create the project architecture diagram: "

                            f"{diagram_error}"

                        )

                    st.subheader("📖 Understand Your Project Architecture")

                    project_explanation = explain_project_architecture(

                        project_files,

                        project_dependencies,

                        project_errors

                    )

                    with st.container(border=True):

                        st.markdown(project_explanation)

                    # --------------------------------------------------

                    # COMBINED CLASS-LEVEL UML-STYLE DIAGRAM

                    # --------------------------------------------------

                    st.subheader("🧩 Combined Class-Level UML Diagram")

                    st.caption(

                        "Classes are extracted from all Python and Java files in the ZIP. "

                        "This is a static UML-style approximation."

                    )

                    try:

                        combined_uml_png, combined_classes = create_combined_class_uml(source_files)

                        if combined_uml_png:

                            st.image(combined_uml_png, caption="Combined project class diagram")

                            st.download_button(

                                "⬇️ Download Combined UML Diagram",

                                data=combined_uml_png,

                                file_name="combined_project_uml.png",

                                mime="image/png",

                                key="combined_project_uml_download"

                            )

                        else:

                            st.info("No class declarations were found in the uploaded source files.")

                        st.subheader("📖 Explanation of the Combined UML")

                        st.markdown(explain_combined_class_uml(combined_classes))

                    except Exception as uml_error:

                        st.error(f"Could not generate the combined class diagram: {uml_error}")

                    if project_errors:

                        with st.expander("⚠️ Files with warnings or parsing errors"):

                            for warning in project_errors:

                                st.warning(warning)

                    project_report = [

                        "MULTI-FILE PROJECT ANALYSIS",

                        "===========================",

                        "",

                        f"Files analyzed: {len(project_files)}",

                        f"Dependencies detected: {len(project_dependencies)}",

                        "",

                        "FILES",

                        "-----",

                        *project_files,

                        "",

                        "DEPENDENCIES",

                        "------------",

                    ]

                    for dependency in project_dependencies:

                        project_report.append(

                            f"{dependency['source']} --{dependency['relationship']}--> "

                            f"{dependency['target']}"

                        )

                    project_report.extend([

                        "",

                        "PROJECT ARCHITECTURE EXPLANATION",

                        "--------------------------------",

                        project_explanation,

                        "",

                        "WARNINGS",

                        "--------",

                        *project_errors

                    ])

                    st.download_button(

                        "⬇️ Download Project Analysis Report",

                        data="\n".join(project_report),

                        file_name="project_dependency_report.txt",

                        mime="text/plain",

                        key="project_report_download"

                    )

        except zipfile.BadZipFile:

            st.error("This ZIP file is invalid or damaged. Please create a new ZIP and try again.")

        except Exception as error:

            st.error(f"Project analysis could not be completed: {error}")

    st.divider()

    st.subheader("🔬 Analyze a Single Source File")

    uploaded_file = st.file_uploader(

        "Upload your source code",

        type=["py", "java"],

        help="Upload a Python (.py) or Java (.java) file."

    )

    if uploaded_file is not None:

        try:

            source_code = uploaded_file.getvalue().decode("utf-8")

        except UnicodeDecodeError:

            st.error(

                "Unable to read the file. Please upload a UTF-8 source file."

            )

            st.stop()

        extension = uploaded_file.name.rsplit(".", 1)[-1].lower()

        language = "Java" if extension == "java" else "Python"

        st.success(f"Successfully uploaded: {uploaded_file.name}")

        st.info(f"Detected Programming Language: {language}")

        with st.expander("📄 View Uploaded Source Code"):

            st.code(source_code, language=language.lower())

        # --------------------------------------------------

        # SEMANTIC CODE ANALYSIS

        # --------------------------------------------------

        st.header("🔍 Semantic Code Analysis")

        try:

            if language == "Java":

                result = analyze_java_code(source_code)

            else:

                result = analyze_code(source_code)

            if not isinstance(result, dict):

                raise TypeError(

                    "The analyzer returned an unexpected result format."

                )

        except Exception as error:

            result = {

                "error": f"Analysis failed: {error}",

                "classes": [],

                "functions": [],

                "imports": [],

                "relationships": []

            }

        if result.get("error"):

            st.error(result["error"])

            classes = []

            functions = []

            imports = []

            relationships = []

        else:

            classes = result.get("classes", []) or []

            functions = result.get("functions", []) or []

            imports = result.get("imports", []) or []

            relationships = result.get("relationships", []) or []

            st.success("Code analysis completed successfully!")

            # --------------------------------------------------

            # METRIC CARDS

            # --------------------------------------------------

            st.subheader("Analysis Overview")

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric("🏛️ Classes", len(classes))

            with col2:

                st.metric("⚙️ Methods / Functions", len(functions))

            with col3:

                st.metric("📦 Imports", len(imports))

            # --------------------------------------------------

            # ANALYSIS TABS

            # --------------------------------------------------

            tab1, tab2, tab3, tab4 = st.tabs(

                [

                    "🏛️ Classes",

                    "⚙️ Methods",

                    "📦 Imports",

                    "🔗 Relationships"

                ]

            )

            with tab1:

                st.subheader("Detected Classes")

                if classes:

                    for name in classes:

                        st.markdown(f"- \`{name}\`")

                else:

                    st.info("No classes found.")

            with tab2:

                st.subheader("Detected Methods and Functions")

                if functions:

                    for name in functions:

                        st.markdown(f"- \`{name}\`")

                else:

                    st.info("No methods or functions found.")

            with tab3:

                st.subheader("Detected Imports")

                if imports:

                    for name in imports:

                        st.markdown(f"- \`{name}\`")

                else:

                    st.info("No imports found.")

            with tab4:

                st.subheader("Detected Relationships")

                if relationships:

                    for relationship in relationships:

                        st.markdown(f"- {relationship}")

                else:

                    st.info("No relationships found.")

            # --------------------------------------------------

            # SOFTWARE ARCHITECTURE DIAGRAM

            # --------------------------------------------------

            st.header("🏗️ Software Architecture Diagram")

            diagram_generated = False

            png_data = None

            try:

                png_data = generate_diagram(

                    source_code,

                    language.lower()

                )

                if png_data:

                    st.image(

                        png_data,

                        caption=f"{language} UML Architecture Diagram"

                    )

                    diagram_generated = True

                    st.subheader("Diagram Legend")

                    col1, col2, col3, col4 = st.columns(4)

                    col1.markdown("🔵 **Class**")

                    col2.markdown("🟡 **Method**")

                    col3.markdown("🟢 **Function / Field**")

                    col4.markdown("🟣 **Interface**")

                    st.download_button(

                        label="⬇️ Download Architecture Diagram",

                        data=png_data,

                        file_name=(

                            f"{uploaded_file.name.rsplit('.', 1)[0]}"

                            "_architecture.png"

                        ),

                        mime="image/png",

                        key="diagram_download"

                    )

                    st.success(

                        "Architecture diagram generated successfully!"

                    )

                else:

                    st.warning(

                        "The diagram generator did not return an image."

                    )

            except Exception as error:

                st.error(f"Could not generate diagram: {error}")

            # --------------------------------------------------

            # UML DIAGRAM EXPLANATION

            # --------------------------------------------------

            st.subheader("📖 Understand Your UML Diagram")

            uml_explanation = explain_uml_diagram(

                classes,

                functions,

                relationships,

                imports

            )

            with st.container(border=True):

                st.markdown(uml_explanation)

            # --------------------------------------------------

            # CODE EXPLANATION

            # --------------------------------------------------

            st.header("🧠 Code Explanation")

            try:

                if language == "Python":

                    explanation = explain_code(source_code)

                else:

                    explanation = explain_java_code(source_code)

            except Exception as error:

                explanation = (

                    f"Code explanation could not be generated: {error}"

                )

            with st.container(border=True):

                st.markdown(explanation)

            # --------------------------------------------------

            # DOWNLOAD ANALYSIS REPORT

            # --------------------------------------------------

            st.header("📥 Download Analysis Report")

            report = f"""

AI-DRIVEN SEMANTIC CODE ANALYSIS

\\================================

Uploaded File: {uploaded_file.name}

Programming Language: {language}

CLASSES

\\-------

{chr(10).join(str(item) for item in classes) or 'No classes found.'}

METHODS / FUNCTIONS

\\-------------------

{chr(10).join(str(item) for item in functions) or 'No methods or functions found.'}

IMPORTS

\\-------

{chr(10).join(str(item) for item in imports) or 'No imports found.'}

RELATIONSHIPS

\\-------------

{chr(10).join(str(item) for item in relationships) or 'No relationships found.'}

UML DIAGRAM EXPLANATION

\\----------------------

{uml_explanation}

CODE EXPLANATION

\\----------------

{explanation}

"""

            st.download_button(

                label="⬇️ Download Complete Analysis Report",

                data=report,

                file_name=(

                    f"{uploaded_file.name.rsplit('.', 1)[0]}"

                    "_analysis_report.txt"

                ),

                mime="text/plain",

                key="report_download"

            )

    else:

        st.html(

            textwrap.dedent("""

            <div class="upload-placeholder">

                <h2>📂 Ready to Analyze Your Code?</h2>

                <p>

                    Upload a Python or Java source file to discover

                    its classes, functions, dependencies and architecture.

                </p>

            </div>

            """),

            unsafe_allow_html=True

        )

# ==================================================

# FOOTER

# ==================================================

st.divider()

st.html(

    textwrap.dedent("""

    <div style="text-align:center; color:#64748b; padding:15px;">

        AI Code Architect | Semantic Code Analysis &

        Automated Software Architecture Modeling

    </div>

    """),

    unsafe_allow_html=True

)

