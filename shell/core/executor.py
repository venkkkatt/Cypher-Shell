import subprocess, os, ctypes
from shellBuiltins import BUILTINS, BuiltinFns

libc = ctypes.CDLL("libc.so.6")

class Executor:
    def __init__(self):
        self.cwd = os.getcwd()

    def run(self, node):
        if node.type.name == "COMMAND":
            return self.runCommand(node)
        elif node.type.name == "BINARYOP":
            return self.runBinary(node)
        elif node.type.name == "PIPELINE":
            return self.runPipeline(node)
        else:
            raise NotImplementedError(f"Node type {node.type} not yet supported")
        
    def runCommand(self, node):
        cmd = node.name
        args = node.args

        if cmd in BUILTINS:
            out = BuiltinFns(cmd, args).main()
            return out if out is not None else 0
        else:
            return self.runExternal(cmd, args)
        
    def runBinary(self, node):
        leftStatus = self.run(node.left)
        if node.op == "&&":
            if leftStatus == 0:
                return self.run(node.right)
            return leftStatus
        elif node.op == "||":
            if leftStatus != 0:
                return self.run(node.right)
            return leftStatus
        elif node.op == ";":
            return self.run(node.right)
        else:
            raise ValueError("Expecting a binary operator")
        
    def runExternal(self, cmd, args):
        
        pid = libc.fork()
        if pid == 0:
            try:
                argv = self.prepareArgv(cmd, args)
                libc.execvp(ctypes.c_char_p(cmd.encode()), argv)
            except FileNotFoundError:
                print("File not found")
            except Exception as e:
                print(f"{cmd}: {e}")
                os._exit(1)
        else:
            status = ctypes.c_int()
            libc.waitpid(pid, ctypes.byref(status), 0)
            return os.WEXITSTATUS(status.value)
    
    def runPipeline(self, node):
        n = len(node.cmds)
        fds = []

        for i in range(n-1):
            r, w = os.pipe()
            fds.append((r,w))
        
        pids = []

        for i, cmdNode in enumerate(node.cmds):
            pid = libc.fork()
            if pid == 0:
                if i > 0:
                    os.dup2(fds[i-1][0], 0)
                if i < (n - 1):
                    os.dup2(fds[i][1], 1)            
            
                for j, (rFd, wFd) in enumerate(fds):
                    if i-1 != j:
                        os.close(rFd)
                    if i != j:
                        os.close(wFd)
                
                exitCode = self.run(cmdNode)
                os._exit(exitCode if exitCode is not None else 0)
            else:
                pids.append(pid)

        for rFd, wFd in fds:
            try:
                os.close(rFd)
                os.close(wFd)
            except OSError:
                pass

        status = 0
        for pid in pids:
            s = ctypes.c_int()
            libc.waitpid(pid, ctypes.byref(s), 0)
            status = os.WEXITSTATUS(s.value)
        return status

    def prepareArgv(self, cmd, args):
        argv = [ctypes.create_string_buffer(s.encode()) for s in [cmd] + args]
        argc = len(argv)
        arrayType = ctypes.c_char_p * (argc + 1)
        cArgv = arrayType(*[ctypes.cast(arg, ctypes.c_char_p) for arg in argv], None)
        return cArgv
    