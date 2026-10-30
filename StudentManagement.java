
import java.util.ArrayList;
import java.util.List;

// Student class
class Student {
    private int id;
    private String name;
    private double marks;

    public Student(int id, String name, double marks) {
        this.id = id;
        this.name = name;
        this.marks = marks;
    }

    public void displayDetails() {
        System.out.println("ID: " + id);
        System.out.println("Name: " + name);
        System.out.println("Marks: " + marks);
    }

    public boolean hasPassed() {
        return marks >= 40;
    }
}

// Management class
class StudentManager {
    private List<Student> students = new ArrayList<>();

    public void addStudent(Student student) {
        students.add(student);
    }

    public void displayAllStudents() {
        for (Student student : students) {
            student.displayDetails();
            System.out.println("Passed: " + student.hasPassed());
            System.out.println("----------------");
        }
    }
}

// Main application
public class StudentManagement {

    public static void main(String[] args) {

        StudentManager manager = new StudentManager();

        Student s1 = new Student(101, "Rahul", 85);
        Student s2 = new Student(102, "Anita", 35);
        Student s3 = new Student(103, "Kiran", 72);

        manager.addStudent(s1);
        manager.addStudent(s2);
        manager.addStudent(s3);

        manager.displayAllStudents();
    }
}
