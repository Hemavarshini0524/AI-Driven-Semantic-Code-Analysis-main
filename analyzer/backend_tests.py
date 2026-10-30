from analyzer.code_analyzer import analyze_code
from analyzer.java_analyzer import analyze_java_code
from analyzer.project_analyzer import analyze_project
from analyzer.diagram_generator import generate_diagram

def test_python_analysis():
    code = """
class Student:
    def display(self):
        print("Hello")

student = Student()
student.display()
"""
    result = analyze_code(code)

    assert result["error"] is None, result["error"]
    assert "Student" in result["classes"]
    assert "Student.display" in result["functions"]

    print("PASS: Python code analysis")


def test_invalid_python():
    code = "class Student("
    result = analyze_code(code)

    assert result["error"] is not None

    print("PASS: Invalid Python code detection")


def test_java_analysis():
    code = """
class Student {
    void display() {
        System.out.println("Hello");
    }
}
"""
    result = analyze_java_code(code)

    assert result["error"] is None, result["error"]
    assert "Student" in result["classes"]
    assert "Student.display" in result["functions"]

    print("PASS: Java code analysis")


def test_invalid_java():
    code = "class Student {"
    result = analyze_java_code(code)

    assert result["error"] is not None

    print("PASS: Invalid Java code detection")


def test_project_dependencies():
    files = {
        "student.py": """
class Student:
    pass
""",
        "main.py": """
from student import Student
student = Student()
"""
    }

    result = analyze_project(files)

    assert result["error"] is None, result["error"]

    dependency_found = any(
        item["source"] == "main.py"
        and item["target"] == "student.py"
        for item in result["dependencies"]
    )

    assert dependency_found, result["dependencies"]

    print("PASS: Cross-file dependency analysis")


def test_python_diagram():
    code = """
class Student:
    def display(self):
        pass
"""
    image = generate_diagram(code, "python")

    assert isinstance(image, bytes)
    assert len(image) > 0

    print("PASS: Python architecture diagram generation")


def test_java_diagram():
    code = """
class Student {
    void display() {
        System.out.println("Hello");
    }
}
"""
    image = generate_diagram(code, "java")

    assert isinstance(image, bytes)
    assert len(image) > 0

    print("PASS: Java architecture diagram generation")


def run_all_tests():
    tests = [
        test_python_analysis,
        test_invalid_python,
        test_java_analysis,
        test_invalid_java,
        test_project_dependencies,
        test_python_diagram,
        test_java_diagram
    ]

    passed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as error:
            print(f"FAIL: {test.__name__}: {error}")

    print("\n----------------------------")
    print(f"Tests passed: {passed}/{len(tests)}")
    print("----------------------------")


if __name__ == "__main__":
    run_all_tests()
