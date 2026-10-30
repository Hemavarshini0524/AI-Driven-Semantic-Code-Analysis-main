 
import streamlit as st
from pathlib import Path

from analyzer.code_analyzer import analyze_code
from analyzer.ai_explainer import explain_code
from analyzer.java_analyzer import analyze_java_code
from analyzer.java_explainer import explain_java_code
from analyzer.diagram_generator import generate_diagram


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

st.markdown("""
<div class="main-header">
    <div class="header-icon">🏗️</div>
    <div>
        <h1>AI Code Architect</h1>
        <p>Semantic Code Analysis & Software Architecture Modeling</p>
    </div>
</div>
""", unsafe_allow_html=True)


st.markdown("""
<div class="welcome-section">
    <h2>Welcome to Code Analysis Studio 👋</h2>
    <p>
        Transform your source code into meaningful insights.
        Analyze Python and Java programs, explore relationships,
        and visualize software architecture.
    </p>
</div>
""", unsafe_allow_html=True)


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
        [
            "Code Analyzer",
            "About Project"
        ],
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

    st.markdown("""
    - Python source code analysis
    - Java source code analysis
    - Class and function detection
    - Import identification
    - Relationship detection
    - Architecture diagram generation
    - Automated code explanation
    - Downloadable analysis reports
    """)

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


    # ==================================================
    # FILE UPLOAD
    # ==================================================

    uploaded_file = st.file_uploader(
        "Upload your source code",
        type=["py", "java"],
        help="Upload a Python (.py) or Java (.java) file."
    )


    # ==================================================
    # FILE ANALYSIS
    # ==================================================

    if uploaded_file is not None:

        try:

            source_code = uploaded_file.getvalue().decode("utf-8")

        except UnicodeDecodeError:

            st.error(
                "Unable to read the file. Please upload a UTF-8 source file."
            )

            st.stop()


        extension = uploaded_file.name.rsplit(".", 1)[-1].lower()

        language = (
            "Java" if extension == "java"
            else "Python"
        )


        st.success(
            f"Successfully uploaded: {uploaded_file.name}"
        )

        st.info(f"Detected Programming Language: {language}")


        # ==================================================
        # SOURCE CODE VIEWER
        # ==================================================

        with st.expander("📄 View Uploaded Source Code"):

            st.code(
                source_code,
                language=language.lower()
            )


        # ==================================================
        # SEMANTIC CODE ANALYSIS
        # ==================================================

        st.header("🔍 Semantic Code Analysis")

        try:

            if language == "Java":

                result = analyze_java_code(source_code)

            else:

                result = analyze_code(source_code)

        except Exception as error:

            result = {
                "error": f"Analysis failed: {error}",
                "classes": [],
                "functions": [],
                "imports": [],
                "relationships": []
            }


        # ==================================================
        # ANALYSIS RESULTS
        # ==================================================

        if result.get("error"):

            st.error(result["error"])

            classes = []
            functions = []
            imports = []
            relationships = []

            explanation = (
                "Code explanation unavailable because analysis failed."
            )

        else:

            classes = result.get("classes", [])
            functions = result.get("functions", [])
            imports = result.get("imports", [])
            relationships = result.get("relationships", [])


            st.success("Code analysis completed successfully!")


            # ==================================================
            # METRIC CARDS
            # ==================================================

            st.subheader("Analysis Overview")

            col1, col2, col3 = st.columns(3)

            with col1:

                st.metric(
                    "🏛️ Classes",
                    len(classes)
                )

            with col2:

                st.metric(
                    "⚙️ Methods / Functions",
                    len(functions)
                )

            with col3:

                st.metric(
                    "📦 Imports",
                    len(imports)
                )


            # ==================================================
            # ANALYSIS TABS
            # ==================================================

            tab1, tab2, tab3, tab4 = st.tabs([
                "🏛️ Classes",
                "⚙️ Methods",
                "📦 Imports",
                "🔗 Relationships"
            ])


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


            # ==================================================
            # SOFTWARE ARCHITECTURE DIAGRAM
            # ==================================================

            st.header("🏗️ Software Architecture Diagram")

            try:

                png_data = generate_diagram(
                    source_code,
                    language.lower()
                )

                st.image(
    png_data,
    caption=f"{language} UML Architecture Diagram"
)


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

            except Exception as error:

                st.error(
                    f"Could not generate diagram: {error}"
                )


            # ==================================================
            # CODE EXPLANATION
            # ==================================================

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


            # ==================================================
            # DOWNLOAD ANALYSIS REPORT
            # ==================================================

            st.header("📥 Download Analysis Report")

            report = f"""
AI-DRIVEN SEMANTIC CODE ANALYSIS
================================

Uploaded File: {uploaded_file.name}

Programming Language: {language}


CLASSES
-------
{chr(10).join(classes) or 'No classes found.'}


METHODS / FUNCTIONS
-------------------
{chr(10).join(functions) or 'No methods or functions found.'}


IMPORTS
-------
{chr(10).join(imports) or 'No imports found.'}


RELATIONSHIPS
-------------
{chr(10).join(relationships) or 'No relationships found.'}


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

        st.markdown("""
        <div class="upload-placeholder">
            <h2>📂 Ready to Analyze Your Code?</h2>
            <p>
                Upload a Python or Java source file to discover
                its classes, functions, dependencies and architecture.
            </p>
        </div>
        """, unsafe_allow_html=True)


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
