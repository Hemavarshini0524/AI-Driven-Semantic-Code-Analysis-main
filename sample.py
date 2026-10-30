
class Student:
    def __init__(self, name):
        self.name = name

    def display(self):
        print(self.name)


def main():
    student = Student("Rithu")
    student.display()


if __name__ == "__main__":
    main()
