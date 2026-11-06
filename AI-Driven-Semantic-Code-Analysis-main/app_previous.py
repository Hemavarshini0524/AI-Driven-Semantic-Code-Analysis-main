import streamlit as st
from pathlib import Path

from analyzer.code_analyzer import analyze_code
from analyzer.ai_explainer import explain_code
from analyzer.java_analyzer import analyze_java_code
from analyzer.java_explainer import explain_java_code
from analyzer.diagram_generator import generate_diagram


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
            sections.append(f"- `{function_name}`")
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
            sections.append(f"- `{imported_module}`")
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
# MODERN DASHBOARD HEADER
# ==================================================

st.markdown(
    """
    <div class="main-header">
        <div class="header-icon">🏗️</div>
        <div>
            <h1>AI Code Architect</h1>
            <p>Semantic Code Analysis & Software Architecture Modeling</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="welcome-section">
        <h2>Welcome to Code Analysis Studio 👋</h2>
        <p>
            Transform your source code into meaningful insights.
            Analyze Python and Java programs, explore relationships,
            and visualize software architecture.
        </p>
    </div>
    """,
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
        - Python source code analysis
        - Java source code analysis
        - Class and function detection
        - Import identification
        - Relationship detection
        - Architecture diagram generation
        - Rule-based code explanation
        - Downloadable analysis reports
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
        "Upload your Python or Java source code to begin analysis."
    )

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
                        st.markdown(f"- `{name}`")
                else:
                    st.info("No classes found.")

            with tab2:
                st.subheader("Detected Methods and Functions")
                if functions:
                    for name in functions:
                        st.markdown(f"- `{name}`")
                else:
                    st.info("No methods or functions found.")

            with tab3:
                st.subheader("Detected Imports")
                if imports:
                    for name in imports:
                        st.markdown(f"- `{name}`")
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
================================

Uploaded File: {uploaded_file.name}
Programming Language: {language}

CLASSES
-------
{chr(10).join(str(item) for item in classes) or 'No classes found.'}

METHODS / FUNCTIONS
-------------------
{chr(10).join(str(item) for item in functions) or 'No methods or functions found.'}

IMPORTS
-------
{chr(10).join(str(item) for item in imports) or 'No imports found.'}

RELATIONSHIPS
-------------
{chr(10).join(str(item) for item in relationships) or 'No relationships found.'}

UML DIAGRAM EXPLANATION
----------------------
{uml_explanation}

CODE EXPLANATION
----------------
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
        st.markdown(
            """
            <div class="upload-placeholder">
                <h2>📂 Ready to Analyze Your Code?</h2>
                <p>
                    Upload a Python or Java source file to discover
                    its classes, functions, dependencies and architecture.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )


# ==================================================
# FOOTER
# ==================================================

st.divider()

st.markdown(
    """
    <div style="text-align:center; color:#64748b; padding:15px;">
        AI Code Architect | Semantic Code Analysis &
        Automated Software Architecture Modeling
    </div>
    """,
    unsafe_allow_html=True
)
