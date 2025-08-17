from enum import Enum
import json

class ASTNodeType(Enum):
    COMMAND = "COMMAND"
    PIPELINE = "PIPELINE"
    BINARYOP = "BINARYOP"
    ASSIGNMENT = "ASSIGNMENT"
    REDIRECTION = "REDIRECTION"
    SUBSHELL = "SUBSHELL"
    IFNODE = "IFNODE"
    FORNODE = "FORNODE"
    CASENODE = "CASENODE"

class ASTNode:
    def __init__(self, type_, **kwargs):
        self.type = type_
        self.__dict__.update(kwargs)
    def __repr__(self):
        return (f"{self.type}: {self.__dict__}")
    
class CommandNode(ASTNode):
    def __init__(self, name, args):
        super().__init__(ASTNodeType.COMMAND, name=name, args=args)
    def __repr__(self):
        return f"CommandNode(name = '{self.name}', args = {self.args})"
    def toDict(self):
        return {
            "type" : self.type.value,
            "name" : self.name,
            "args" : self.args
        }

class BinaryOpNode(ASTNode):
    def __init__(self, op, left, right):
        super().__init__(ASTNodeType.BINARYOP, op=op, left=left, right=right)
    
    def __repr__(self):
        return f"BinaryOpNode(op = '{self.op}', left = {self.left}, right = {self.right})"
    
    def toDict(self):
        return {
            "type" : self.type.value,
            "op" : self.op,
            "left" : self.left.toDict(),
            "right" : self.right.toDict()
        }

class PipeLineNode(ASTNode):
    def __init__(self, name, cmds):
        super().__init__(ASTNodeType.PIPELINE, name=name, cmds=cmds)
    def __repr__(self):
        return f"PipeLineNode(cmds = {self.cmds})"
    def toDict(self):
        return {
            "type" : self.type.value,
            "cmds" : [cmd.toDict() for cmd in self.cmds]
        }

def saveASTtoJson(node, filename = "ast.json"):
    with open (filename, "w") as f:
        json.dump(node.toDict(), f, indent=4)