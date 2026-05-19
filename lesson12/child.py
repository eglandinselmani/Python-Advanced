class Child(Person):

    def calculate_bmi(self):
        return (self.weight / (self.height ** 2)) * 1.3

    def get_bmi_category(self):

        bmi = self.calculate_bmi()

        if bmi < 14:
            return "Underweight"

        elif bmi < 18:
            return "Normal weight"

        elif bmi < 22:
            return "Overweight"

        else:
            return "Obese"