
class Student:
    def display(self):
        print("Student")


class Teacher:
    def display(self):
        print("Teacher")


def main():
    student = Student()
    teacher = Teacher()

    student.display()
    teacher.display()


main()
