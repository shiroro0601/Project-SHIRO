"""
Project SHIRO v0.8
社員基底クラス
"""

from abc import ABC, abstractmethod

from company.logger import Logger
from company.task import Task
from company.artifact import Artifact


class Employee(ABC):
    """
    全社員の親クラス
    """

    def __init__(self, name: str, department: str):

        self.name = name
        self.department = department

        self.logger = Logger()

    def log(self, message: str) -> None:
        self.logger.write(
            self.department,
            self.name,
            message
        )

    @abstractmethod
    def run(self, task: Task) -> Artifact:
        """
        タスクを実行する
        """
        pass