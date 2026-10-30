
from analyzer.ai_explainer import explain_code

code = """
class Student:
    def display(self):
        print("Hello Student")
"""

result = explain_code(code)

print("\n===== AI CODE EXPLANATION =====\n")
print(result)
