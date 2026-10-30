
from analyzer.ai_explainer import explain_code

sample_code = '''
class Student:
    def display(self):
        print("Hello")
'''

result = explain_code(sample_code)

print(result)
