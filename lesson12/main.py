name = input("Enter name: ")
age = int(input("Enter age: "))
weight = float(input("Enter weight: "))
height = float(input("Enter height: "))

if age >= 18:
    person = Adult(name, age, weight, height)

else:
    person = Child(name, age, weight, height)

    person.print_info()