
import java.util.Scanner;

class Student {
    private String name;
    private int marks;

    public Student(String name, int marks) {
        this.name = name;
        this.marks = marks;
    }

    public void displayDetails() {
        System.out.println("Student Name: " + name);
        System.out.println("Marks: " + marks);
    }

    public boolean hasPassed() {
        return marks >= 40;
    }
}

public class Sample {

    public static void main(String[] args) {
        Student student = new Student("Rithu", 85);

        student.displayDetails();

        if (student.hasPassed()) {
            System.out.println("Result: Pass");
        } else {
            System.out.println("Result: Fail");
        }
    }
}
