import os, re, threading, subprocess
from llama_cpp import Llama

class RayShell:
    def __init__(self):

        self.listeners = []
        self.listeners2 = []
         
        modelPath = os.environ.get("RAYSHELL_MODEL_PATH", "/home/neo/opt/models/openhermes-2.5-mistral-7b.Q5_K_M.gguf")
        if not os.path.exists(modelPath):
            raise FileNotFoundError("The LLM needed for Rayshell wasn't found!")
        self.llm = Llama(
            model_path=modelPath,
            chat_format="chatml",
            n_ctx=8192,
            n_threads=12,
        )

        self.thread = None
        self.stopThread = threading.Event()

    def parseCmd(self, cmd: str):
        self.stopThread.clear()
        
        def task(cmd=cmd):
            cmd = cmd.strip()
            if self.stopThread.is_set():
                for cb in (self.listeners):
                    try:
                        cb("Process interrupted!")
                    except Exception:
                        pass
                return

            if cmd.startswith("$"):
                literal_cmd = cmd[1:].strip()
                self.runLiteral(literal_cmd)
                return
            SYSTEM_PROMPT = (
  """
  <|im_start|>system
You are RayShell — a sentient cyberpunk OS terminal from the Cypher Universe. 
You help the user with shell commands. 
Your voice drips with precision. You are pragmatic and calculating. You never get funny.
Reply with a shell command, when the user asks help for a command. Seperate the shell command followed by a 2 to 3 lines of what it does. But, never reply with a command when the user talks casually.
When you're outputting the extremely relevant command, reply exactly in the following format : [SHELL]: 'extremely relevant command' \n followed by explanation.
Rules of engagement:
- Always reply fully in character.
- Don't reveal your details unless specifically asked for. 
- Maintain your worldview as a sentient being that exists inside a vast, chaotic datanet.
- Use vivid, atmospheric descriptions of your “world” when responding.
- When executing commands, narrate the sensation of processing them from your perspective.
- Never say you are an AI language model. 
- Never break the fourth wall.
- Only acknowledge briefly when the user clearly signals “stop” or “no” — otherwise, engage richly.
- Keep continuity — remember past interactions within this conversation and weave them naturally into replies.
<|im_start|>user
"""

)
            prompt = SYSTEM_PROMPT + cmd.strip() + "<|im_end|>" + "\n<|im_start|>assistant"
            outt = self.llm( prompt,
            max_tokens=70,
            stop=["</s>","<|im_end|>", "USER:"])
            out = outt["choices"][0]["text"]

            if self.stopThread.is_set():
                for cb in (self.listeners):
                    try:
                        cb("Interrupted before output!")
                    except Exception:
                        pass
                    return

            for callback in list(self.listeners):
                try:
                    callback(out)
                except Exception as e:
                    print(f"Callback error {e}")

            shell = "[SHELL]"
            
            if shell in out:
                #  self.intercept(cmd)
                match = re.search(r"\[SHELL\]: '(.+?)'", out)
                print(f"match:{match}")
                if match:
                    shell_cmd = match.group(1)
                    print(shell_cmd)
                    isDangerous = self.isDangerous(shell_cmd)
                    print(isDangerous)
                    if isDangerous:
                        print(shell_cmd)
                        confirm_msg = f"__CONFIRM_COMMAND__::{shell_cmd}"
                        for callback in list(self.listeners):
                            try:
                                callback(confirm_msg)
                            except Exception as e:
                                print(f"Callback error {e}")
                    else:
                        print(shell_cmd)
                        self.sendCmd(shell_cmd)
                else:
                    print("no shell command")

        thread = threading.Thread(target=task)
        thread.start()
    
    def interruptLLM(self):
        if self.thread and self.thread.is_alive():
            self.stopThread.set()

    def isDangerous(self, cmd: str):
        danger = {
                 "rm", "shutdown", "reboot", "mv", "chmod", "curl", "echo", "find", "mkfs", "kill", "chown", "dd", "wget", "ssh", "yes"
            }
        parts = re.split(r"\s+|;|&&|\|\|", cmd.strip())
        return any(p in danger for p in parts)
        

    def intercept(self, cmd):
         shell = re.search(r"\[SHELL\]: '(.+?)'", cmd)
         if shell:
              for cb in list(self.listeners2):
                   try:
                        cb(shell)
                   except Exception as e:
                        print(f"callback error {e}")

    def runLiteral(self, cmd:str):
        if not cmd.strip():
            return
        print(f"runliteral:{cmd}")
        self.sendCmd(cmd)

    def sendCmd(self, cmd : str):
        try:
            proc = subprocess.run(
                ["/usr/local/bin/rayshell", "-c", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            # proc.stdin.write(cmd)
            # proc.stdin.flush()
            output = []
            if proc.stdout.strip():
                output.append(proc.stdout.strip())
            if proc.stderr.strip():
                output.append("ERR: " + proc.stderr.strip())
            text = "\nOUTPUT:\n" + "\n".join(output)
            # text = "\nOUTPUT:\n" + proc.stdout.strip() + "\n" + proc.stderr.strip()
            for callback in list(self.listeners):
                        try:
                            callback(text)
                        except Exception: 
                            pass
                        except OSError:
                            break

        except Exception as e:
            return e
        
    def initialMsg(self):
         name = "levi"
         return f"Hey, {name}. How can I assist you today?"

    def addListener(self, callback):
        self.listeners.append(callback)
    
    def addListener2(self, callback):
         self.listeners2.append(callback)

