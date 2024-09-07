import pickle
from functools import wraps
from collections import UserDict
from datetime import datetime, date, timedelta
from abc import ABC, abstractmethod


class UserDisplay(ABC):

    @abstractmethod
    def show_contact(self, record):
        pass

    @abstractmethod
    def show_all_contacts(self, records):
        pass

    @abstractmethod
    def show_message(self, message):
        pass

    @abstractmethod
    def show_error(self, error_message):
        pass


class ConsoleDisplay(UserDisplay):

    def show_contact(self, record):
        print(
            f"Contact name: {record.name.value}, phones: {'; '.join(p.value for p in record.phones)}, birthday: {record.birthday}.")

    def show_all_contacts(self, records):
        if records:
            for record in records.values():
                self.show_contact(record)
        else:
            print("No contacts found.")

    def show_message(self, message):
        print(message)

    def show_error(self, error_message):
        print(f"Error: {error_message}")


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    pass


class Phone(Field):
    def __init__(self, value):
        if value.isdigit() and len(value) == 10:
            super().__init__(value)
        else:
            raise ValueError("Phone must be 10 digits.")


class Birthday(Field):
    def __init__(self, value):
        try:
            datetime.strptime(value, '%d.%m.%Y')
            super().__init__(value)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY.")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone_number: str):
        phone = Phone(phone_number)
        self.phones.append(phone)

    def remove_phone(self, phone_number: str):
        phone = self.find_phone(phone_number)
        self.phones.remove(phone)

    def edit_phone(self, old_number: str, new_number: str):
        phone = self.find_phone(old_number)
        if phone:
            self.add_phone(new_number)
            self.remove_phone(old_number)
        else:
            raise ValueError(f"Phone number {old_number} not found.")

    def find_phone(self, phone_number: str):
        for phone in self.phones:
            if phone.value == phone_number:
                return phone
        return None

    def add_birthday(self, new_birthday):
        birthday = Birthday(new_birthday)
        self.birthday = birthday

    def __str__(self):
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}, birthday: {self.birthday}."


class AddressBook(UserDict):
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self, days=7):
        upcoming_birthdays = []
        today = date.today()

        for record in self.data.values():
            if record.birthday:
                birthday_date = datetime.strptime(record.birthday.value, '%d.%m.%Y').date()
                birthday_this_year = birthday_date.replace(year=today.year)

                if birthday_this_year < today:
                    birthday_this_year = birthday_date.replace(year=today.year + 1)

                days_until_birthday = (birthday_this_year - today).days

                if 0 <= days_until_birthday <= days:
                    congratulation_date = adjust_for_weekend(birthday_this_year)
                    upcoming_birthdays.append(
                        {"name": record.name.value, "congratulation_date": congratulation_date.strftime('%d.%m.%Y')})

        return upcoming_birthdays

    def __str__(self):
        return "\n".join(str(record) for record in self.data.values())


def find_next_weekday(start_date, weekday):
    days_ahead = weekday - start_date.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return start_date + timedelta(days=days_ahead)


def adjust_for_weekend(birthday):
    if birthday.weekday() >= 5:
        return find_next_weekday(birthday, 0)
    return birthday


# Error handler
def input_error(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            return "Enter name and phone/birthday please."
        except KeyError:
            return "Please enter username."
        except IndexError:
            return "Invalid! Please provide the correct arguments."

    return inner


def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


# Saving data
def save_data(book, filename='addressbook.pkl'):
    with open(filename, 'wb') as f:
        pickle.dump(book, f)


def load_data(filename='addressbook.pkl'):
    try:
        with open(filename, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


# User interaction functions
@input_error
def add_contact(args, book: AddressBook, display: UserDisplay):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    display.show_message(message)


@input_error
def change_contact(args, book: AddressBook, display: UserDisplay):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        display.show_message("Contact changed.")
    else:
        display.show_error("Contact not found.")


@input_error
def show_phone_num(args, book: AddressBook, display: UserDisplay):
    name = args[0]
    record = book.find(name)
    if record:
        display.show_message(', '.join(phone.value for phone in record.phones))
    else:
        display.show_error("Contact not found.")


def show_contacts(book: AddressBook, display: UserDisplay):
    display.show_all_contacts(book.data)


@input_error
def add_birthday(args, book: AddressBook, display: UserDisplay):
    name, birthday, *_ = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        display.show_message("Birthday added.")
    else:
        display.show_error("Contact not found.")


@input_error
def show_birthday(args, book: AddressBook, display: UserDisplay):
    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        display.show_message(record.birthday.value)
    else:
        display.show_error("No birthday found for this contact.")


@input_error
def birthdays(book: AddressBook, display: UserDisplay):
    upcoming_birthdays = book.get_upcoming_birthdays()
    if not upcoming_birthdays:
        display.show_message("No birthdays in the next 7 days.")
    else:
        display.show_message("\n".join(f"{b['name']}: {b['congratulation_date']}" for b in upcoming_birthdays))


def main():
    book = load_data()
    display = ConsoleDisplay()

    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            display.show_message("Good bye!")
            break

        elif command == "hello":
            display.show_message("How can I help you?")

        elif command == "add":
            add_contact(args, book, display)

        elif command == "change":
            change_contact(args, book, display)

        elif command == "phone":
            show_phone_num(args, book, display)

        elif command == "all":
            show_contacts(book, display)

        elif command == "add-birthday":
            add_birthday(args, book, display)

        elif command == "show-birthday":
            show_birthday(args, book, display)

        elif command == "birthdays":
            birthdays(book, display)

        else:
            print("Invalid command.")

    save_data(book)


if __name__ == "__main__":
    main()