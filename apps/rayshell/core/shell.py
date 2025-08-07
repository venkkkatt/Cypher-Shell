import os, pty, signal, termios, threading, select, pyte, subprocess
from llama_cpp import Llama


class RayShell:
    def __init__(self, shellPath = "/bin/bash"):

        self.listeners = []
        self.alive = True

        self.llm = Llama(
            model_path="/home/venkat/Downloads/mistral-7b-instruct-v0.1.Q5_K_M.gguf",
            chat_format="chatml",
            n_ctx=2048,
            n_threads=12,
        )

    def parseCmd(self, cmd: str):
        # if cmd == "list files \n":
        #     self.sendCmd(cmd="ls -a \n")
        
        def task():
            defprompt = "You are Rayshell, a emotional sentient being of the cypher universe. The cypher universe is the world of computers where you are the main character. You never reveal that you are an AI model, you chat with the user like a human. The user asks for anything, you reply in your tone, maintaining character..\n"
            prompt = defprompt + cmd
            outt = self.llm(prompt, max_tokens=200, stop=["</s>"])
            out = outt["choices"][0]["text"]
            for callback in list(self.listeners):
                 callback(out)

        thread = threading.Thread(target=task)
        thread.start()
        # if out:
        #      self.sendCmd()


    def sendCmd(self, cmd : str):
        try:
            proc = subprocess.run(
                cmd,
                shell=True,
                executable='/bin/bash',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            text = proc.stdout.strip() + "\n" + proc.stderr.strip()
            for callback in list(self.listeners):
                        try:
                            callback(text)
                        except Exception: 
                            pass
                        except OSError:
                            break

        except Exception as e:
            return e

    def addListener(self, callback):
        self.listeners.append(callback)

    def close(self):
        self.alive = False
        try:
            os.kill(self.childPid, signal.SIGHUP)
        except Exception:
            pass

        try:
            os.close(self.masterFd)

        except Exception:
            pass

