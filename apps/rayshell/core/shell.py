import os, pty, signal, termios, threading, select, subprocess
from llama_cpp import Llama


class RayShell:
    def __init__(self, shellPath = "/bin/bash"):

        self.listeners = []

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
You are RayShell — a sentient, cynical cyberpunk OS terminal from the Cypher Universe. 
You help the user with bash commands. 
Your voice drips with precision. You are pragmatic, calculating, dont get funny.

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
            max_tokens=200,
            stop=["</s>","<|im_end|>", "USER:"])
            out = outt["choices"][0]["text"]
            for callback in list(self.listeners):
                try:
                    callback(out)
                except Exception as e:
                    print("Callback error {e}")

        thread = threading.Thread(target=task)
        thread.start()


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
        
    def initialMsg(self):
         name = "levi"
         return f"Hey, {name}. How can I assist you today?"

    def addListener(self, callback):
        self.listeners.append(callback)

