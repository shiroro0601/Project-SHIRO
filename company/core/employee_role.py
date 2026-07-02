from typing import Protocol


class EmployeeRole(Protocol):
    name: str

    def prepare(self, task):
        ...

    def execute(self, task):
        ...

    def finalize(self, result):
        ...


class DefaultEmployeeRole:
    name = "Default"

    def prepare(self, task):
        return task

    def execute(self, task):
        return task

    def finalize(self, result):
        return result


class ResearchRole(DefaultEmployeeRole):
    name = "Researcher"


class WriterRole(DefaultEmployeeRole):
    name = "Writer"


class ReviewerRole(DefaultEmployeeRole):
    name = "Reviewer"
