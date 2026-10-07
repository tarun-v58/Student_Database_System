class StudentNotFoundError(Exception):
    def __init__(self, student_id: int):
        self.student_id = student_id
        super().__init__(f"Student with id {student_id} not found")


class DuplicateEmailError(Exception):
    def __init__(self, email: str):
        self.email = email
        super().__init__("A student with this email already exists")