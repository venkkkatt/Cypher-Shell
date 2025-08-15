from lexer import Lexer

def repl():
    while True:
        try:
            line = input("rayshell> ")
        except EOFError:
            break
        except KeyboardInterrupt:
            print()
            continue

        if line.strip() == "exit":
            break
        
        lexer = Lexer(line=line)
        tokens = lexer.nextToken()
        for token in tokens:
            print(token)
        # print(line)
repl()
