import pty, os, threading, select, signal, pyte

class Terminal:
    def __init__(self, shellPath = "/usr/local/bin/rayshell"):
        self.pid, self.masterfd =  pty.fork()
        self.listeners = []
        self.alive = True

        if self.pid == 0:
            os.execvp(shellPath, [shellPath])

        self.thread = threading.Thread(target=self.readFromPty, daemon=True)
        self.thread.start()
        self.screen = pyte.Screen(80, 24)
        self.stream = pyte.Stream(self.screen)
    
    def readFromPty(self):
        while self.alive:
            r,_,_ = select.select([self.masterfd], [], [], 0.1)
            if self.masterfd in r:
                try:
                    data = os.read(self.masterfd, 1024)
                    if not data:
                        break
                    text = data.decode(errors="ignore")
                    # self.stream.feed(data.decode(errors="ignore"))
                    # text = "\n".join(self.screen.display)

                    for callback in self.listeners:
                        callback(text)
                except Exception as e:
                    print(f"exception {e}")
        self.alive = False
    
    def sendCmd(self, cmd):
        if self.masterfd and self.alive:
            os.write(self.masterfd, (cmd).encode())
    
    def addListener(self, callback):
        self.listeners.append(callback)

    def close(self):
        self.alive = False
        try:
            os.kill(self.pid, signal.SIGHUP)
        except Exception:
            pass
        try:
            os.close(self.masterfd)
        except Exception:
            pass
