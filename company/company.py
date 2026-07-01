"""
Project SHIRO v0.8
会社クラス
"""

from company.ceo import CEO


class Company:

    def __init__(self, name: str):

        self.name = name

        self.ceo = CEO()

    def hire(self, employee):

        self.ceo.add_employee(employee)

    def info(self):

        print("=" * 40)
        print(self.name)
        print("=" * 40)

        print()

        print("社員一覧")

        for department, employee in self.ceo.employees.items():

            print(
                f"{department} : {employee.name}"
            )

        print()