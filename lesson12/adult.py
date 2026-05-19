class Adult(Person):

    def calculate_bmi(self):
        return self.weight / (self.height ** 2)


    def get_bmi_category(self):

        bmi = self.calculate_bmi()

        if bmi < 18.5:
            return "Underweight"

        elif bmi < 24.9:
            return "Normal weight"

        elif bmi < 29.9:
            return "Overweight"

        else:
            return "Obese"