
from analyzer.java_explainer import explain_java_code

sample_code = """
class Student {

    String name;

    Student(String name) {
        this.name = name;
    }

    void display() {
        System.out.println("Hello");
    }
}
"""

result = explain_java_code(sample_code)

print(result)
