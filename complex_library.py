
from datetime import datetime, timedelta
from collections import defaultdict
from functools import wraps
import json
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


# Decorator to log function execution
def log_execution(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logging.info("Executing %s", func.__name__)
        result = func(*args, **kwargs)
        logging.info("Finished %s", func.__name__)
        return result
    return wrapper


# Custom exception
class LibraryError(Exception):
    pass


class BookNotAvailableError(LibraryError):
    pass


# Base class
class Person:
    def __init__(self, name, email):
        self.name = name
        self.email = email

    def get_details(self):
        return {
            "name": self.name,
            "email": self.email
        }


# Inherited class
class Member(Person):
    def __init__(self, member_id, name, email):
        super().__init__(name, email)
        self.member_id = member_id
        self.borrowed_books = []

    def borrow_book(self, book):
        if not book.available:
            raise BookNotAvailableError(
                f"{book.title} is currently unavailable"
            )

        book.available = False
        self.borrowed_books.append(book)
        logging.info("%s borrowed %s", self.name, book.title)

    def return_book(self, book):
        if book not in self.borrowed_books:
            raise LibraryError("This book was not borrowed by the member")

        book.available = True
        self.borrowed_books.remove(book)
        logging.info("%s returned %s", self.name, book.title)


# Book entity
class Book:
    def __init__(self, book_id, title, author, category):
        self.book_id = book_id
        self.title = title
        self.author = author
        self.category = category
        self.available = True

    def get_book_info(self):
        return {
            "id": self.book_id,
            "title": self.title,
            "author": self.author,
            "category": self.category,
            "available": self.available
        }


# Library management service
class Library:
    def __init__(self):
        self.books = {}
        self.members = {}
        self.borrow_history = defaultdict(list)

    @log_execution
    def add_book(self, book):
        self.books[book.book_id] = book
        logging.info("Added book: %s", book.title)

    @log_execution
    def register_member(self, member):
        self.members[member.member_id] = member
        logging.info("Registered member: %s", member.name)

    def search_books(self, keyword):
        keyword = keyword.lower()

        return [
            book for book in self.books.values()
            if keyword in book.title.lower()
            or keyword in book.author.lower()
            or keyword in book.category.lower()
        ]

    @log_execution
    def issue_book(self, member_id, book_id):
        member = self.members.get(member_id)
        book = self.books.get(book_id)

        if member is None:
            raise LibraryError("Member not found")

        if book is None:
            raise LibraryError("Book not found")

        member.borrow_book(book)

        self.borrow_history[member_id].append({
            "book_id": book_id,
            "borrowed_at": datetime.now().isoformat()
        })

    def calculate_late_fee(self, borrowed_date, return_date):
        due_date = borrowed_date + timedelta(days=14)
        late_days = max((return_date - due_date).days, 0)

        return late_days * 5

    def generate_report(self):
        total_books = len(self.books)
        available_books = sum(
            1 for book in self.books.values()
            if book.available
        )

        return {
            "total_books": total_books,
            "available_books": available_books,
            "borrowed_books": total_books - available_books,
            "registered_members": len(self.members)
        }


# Data persistence service
class LibraryStorage:
    def __init__(self, filename="library_data.json"):
        self.filename = filename

    def save_data(self, library):
        data = {
            "books": [
                book.get_book_info()
                for book in library.books.values()
            ],
            "members": [
                member.get_details()
                for member in library.members.values()
            ]
        }

        with open(self.filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)

    def load_data(self):
        try:
            with open(self.filename, "r", encoding="utf-8") as file:
                return json.load(file)
        except FileNotFoundError:
            logging.warning("Storage file not found")
            return {}


# Application controller
class LibraryApplication:
    def __init__(self):
        self.library = Library()
        self.storage = LibraryStorage()

    def setup_sample_data(self):
        book1 = Book(101, "Python Programming", "John Smith", "Technology")
        book2 = Book(102, "Data Structures", "Alice Brown", "Computer Science")
        book3 = Book(103, "Artificial Intelligence", "David Wilson", "AI")

        member1 = Member(1, "Rahul", "rahul@example.com")
        member2 = Member(2, "Anita", "anita@example.com")

        self.library.add_book(book1)
        self.library.add_book(book2)
        self.library.add_book(book3)

        self.library.register_member(member1)
        self.library.register_member(member2)

    def run_demo(self):
        self.setup_sample_data()

        try:
            self.library.issue_book(1, 101)

            results = self.library.search_books("Python")
            for book in results:
                print(book.get_book_info())

            print("Library Report:")
            print(self.library.generate_report())

            self.storage.save_data(self.library)

        except LibraryError as error:
            logging.error("Library operation failed: %s", error)


if __name__ == "__main__":
    application = LibraryApplication()
    application.run_demo()
