from lexer import Lexer, TokenType, Token
from enum import Enum
from ast import CommandNode, PipeLineNode, BinaryOpNode
    
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    def peek(self):
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return Token(TokenType.EOF, None)
        
    def advance(self):
        tok = self.peek()
        self.pos += 1
        return tok
    
    def parse(self):
        return self.parseSequence()
    
    def parseSequence(self):
        node = self.parseLogical()
        while self.peek().type == TokenType.SEMICOLON:
            self.advance()
            right = self.parseLogical()
            node = BinaryOpNode(";", node, right)
        return node

    def parseLogical(self):
        node = self.parsePipeLine()
        while self.peek().type in(TokenType.AND, TokenType.OR):
            op = self.advance()
            right = self.parsePipeLine()
            node = BinaryOpNode(op.value, node, right)
        return node

    def parsePipeLine(self):
        node = self.parseCommand()
        cmds = [node]
        while self.peek().type == TokenType.PIPE:
            self.advance()
            cmds.append(self.parseCommand())
        if len(cmds) == 1:
            return node
        return PipeLineNode("PIPELINE", cmds)    
    
    def parseCommand(self):
        token = self.advance()
        if token.type not in (TokenType.WORD, TokenType.STRING):
            raise ValueError("The first word should be a command")
        
        cmd = token.value
        args = []

        while self.peek().type in (TokenType.WORD, TokenType.STRING):
            args.append(self.advance().value)

        # while True:
        #     token = self.peek()
        #     if token.type in (TokenType.EOF,):
        #         break
        #     elif token.type in (TokenType.REDIR_IN, TokenType.REDIR_OUT):
        #         break
        #     else:
        #         args.append(self.advance().value)
        
        return CommandNode(name = cmd, args = args)




        