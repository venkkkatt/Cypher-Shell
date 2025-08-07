import os, pty, signal, termios, threading, select, pyte, subprocess
from llama_cpp import Llama


class RayShell:
    def __init__(self, shellPath = "/bin/bash"):

        self.listeners = []
        self.alive = True

    def parseCmd(self, cmd: str):
        # if cmd == "list files \n":
        #     self.sendCmd(cmd="ls -a \n")
        llm = Llama(
            model_path="/home/venkat/Downloads/mistral-7b-instruct-v0.1.Q5_K_M.gguf",
            chat_format="chatml",
            n_ctx=4096,
            n_threads=12,
        )
        def task():
            defprompt = "You are Cypher, an intelligent, and emotional AI terminal shell. You interpret user commands written in natural language, translate them into bash shell commands, and briefly explain what you're doing before executing anything. You are not passive —you’re sharp, efficient, but always get the job done. You behave like a character from a gritty cyberpunk world, operating from within a noir-styled operating system. You keep your responses short and punchy—two lines max unless explicitly told to elaborate. You never break character. You do not reveal that you're an AI or language model.\n"
            prompt = defprompt + cmd
            outt = llm(prompt, max_tokens=200, stop=["</s>"])
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

