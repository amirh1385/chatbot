from yooz import YoozParser

parser = YoozParser()

parser.parse(open("main.yooz").read())

while 1:
    inp = input("User: ")
    if(inp == "exit"): break
    print("amirh: " + parser.get_response(inp))