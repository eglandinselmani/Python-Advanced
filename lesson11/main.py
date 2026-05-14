import os

file2 = open("example.txt","r")

file2.close()


with open("example.txt","r") as file:
    content = file.read()
    print(content)

with open("example.txt" , "w") as file:
    file.writelines("hi from main")


lista = ["hello world!\n","Welcome to python!\n"]

with open("example.txt", "w") as file:
    file.writelines(lista)


if os.path.exists("example.txt"):
    print("file ekziston")
else:
    print("file fds nuk ekziston")


with open("example.txt" ,"a") as file:
    file.write("hello sfd main")

name="Eglandin"
age=354324

with open("outupt.txt","w") as file:
    file.write("Name:" + name + "\n")
    file.write("age: " + str(age) +"\n")









