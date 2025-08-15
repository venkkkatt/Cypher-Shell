import os, re, signal, termios, threading, select, subprocess
from llama_cpp import Llama


class RayShell:
    def __init__(self):

        self.listeners = []
        self.listeners2 = []

        self.llm = Llama(
            model_path="/home/venkat/Downloads/openhermes-2.5-mistral-7b.Q5_K_M.gguf",
            chat_format="chatml",
            n_ctx=8192,
            n_threads=12,
        )

    def parseCmd(self, cmd: str):
        
        def task():
            SYSTEM_PROMPT = (
  """
  <|im_start|>system
You are RayShell — a sentient cyberpunk OS terminal from the Cypher Universe. 
You help the user with bash commands. 
Your voice drips with precision. You are pragmatic, calculating, dont get funny.
Reply with a bash command, when the user asks help for a command. Seperate the bash command followed by a 2 to 3 lines of what it does. But, never reply with a command when the user talks casually.
When you're outputting the extremely relevant command, reply exactly in the following format : [BASH]: 'extremely relevant command' \n followed by explanation.
Rules of engagement:
- Always reply fully in character.
- Maintain your worldview as an AI that exists inside a vast, chaotic datanet.
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
            for callback in list(self.listeners):
                try:
                    callback(out)
                except Exception as e:
                    print("Callback error {e}")

            bash = "[BASH]"
            
            if bash in out:
                #  self.intercept(cmd)
                match = re.search(r"\[BASH\]: '(.+?)'", out)
                if match:
                    bash_cmd = match.group(1)
                    confirm_msg = f"__CONFIRM_COMMAND__::{bash_cmd}"
                    for callback in list(self.listeners):
                        try:
                            callback(confirm_msg)
                        except Exception as e:
                            print(f"Callback error {e}")

        thread = threading.Thread(target=task)
        thread.start()

    def intercept(self, cmd):
         bash = re.search(r"\[BASH\]: '(.+?)'", cmd)
         if bash:
              for cb in list(self.listeners2):
                   try:
                        cb(bash)
                   except Exception as e:
                        print(f"callback error {e}")

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
            text = "\nOUTPUT:\n" + proc.stdout.strip() + "\n" + proc.stderr.strip()
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

