
class Student {
    public void display() {
        System.out.println("Student");
    }
}

class Teacher {
    public void display() {
        System.out.println("Teacher");
    }
}

public class semantic_test {
    public static void main(String[] args) {
        Student student = new Student();
        Teacher teacher = new Teacher();

        student.display();
        teacher.display();
    }
}
