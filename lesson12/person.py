from abc import ABC, abstractmethod

class Person(ABC):

    def __init__(self, name, age, weight, height):
        self.name = name
        self.age = age
        self._weight = weight
        self._height = height
    @property
    def weight(self):
        return self._weight

    @weight.setter
    def weight(self, value):
        if value > 0:
            self._weight = value
    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        if value > 0:
            self._height = value
    @abstractmethod
    def calculate_bmi(self):
        pass

    @abstractmethod
    def get_bmi_category(self):
        pass
    def print_info(self):

        print("Name:", self.name)
        print("Age:", self.age)
        print("Weight:", self.weight)
        print("Height:", self.height)
        print("BMI:", round(self.calculate_bmi(), 2))
        print("Category:", self.get_bmi_category())