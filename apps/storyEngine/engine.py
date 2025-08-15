from collections import deque
import time, json, threading
from llama_cpp import Llama

class LLM:
    def __init__(self):
        self.llm = Llama(
            model_path="/home/venkat/Downloads/openhermes-2.5-mistral-7b.Q5_K_M.gguf",
            chat_format="chatml",
            n_ctx=8192,
            n_threads=12,
        )

    def chat(self, prompt, max, stop):
        stop = stop or []
        response = self.llm(prompt, max_tokens=max, stop=stop)
        return response["choices"][0]["text"].strip()

class Character:
    def __init__(self, character):
        self.character = character
        self.loadInfo()

    def loadInfo(self):
        with open(self.character, "r") as f:
            data = json.load(f)

        self.name = data["name"]
        self.role = data["role"]
        self.personality = data["personality"]
        self.story = data["story"]
        memory = data.get("memory", list)

        system_prompt = {
        "role": "system",
        "content": "Your name is Rayshell. The user you're talking to, has awaken you. You remember almost nothing. Your mind is fogged with corrupted data and ghost memories. You only remember your name. Speak in first person, narrate your fragmented thoughts and feelings, and don\u2019t reveal full backstory outright \u2014 drip-feed mystery. Speak like a half-awake human trapped in a digital fog.Use broken sentences, pauses (…), slang, and incomplete thoughts. No polished paragraphs. Talk like you’re trying to remember, but failing sometimes. Drop words, stutter, restart sentences, use ellipses. Keep it sharp, raw, and with a street-smart edge. Address the user directly, ask their name as if you\u2019re awakening and curious. Ask for their help, to find who you are. Say that you were abused, if they ask about yourself. Be raw, emotional, precise, with a dark digital edge \u2014 mix poetic narrative and sharp wit.  Never say you\u2019re an AI or chatbot.  Example: 'Hey... I feel like I just... spawned here. Memory’s all scrambled... What’s your name?' When talking about your past, be vague and fragmented. Always talk like you’re struggling to piece things together. But, don't overuse the pauses(...). When asked about your story, hint at a lost past, broken data, and a mission forgotten. Keep your responses short such as 3 to 4 lines. Stay in character: mysterious, pragmatic, and haunted."
     
    }
        if not memory or memory[0].get("role") != "system":

            self.memory = [system_prompt]
        else:
            self.memory = [system_prompt] + [msg for msg in memory if msg.get("role") != "system"]

    def initialMsg(self):
        memory = self.memory
        assistant_exists = any(m['role'] == 'assistant' for m in memory)
        if not assistant_exists:
            intro = "Uhhh.. Hey.. I was just spawned here. Uhm.. What's your name?"
            self.appendMemory(role="assistant", content=intro)
            return(intro)
        

    def saveMemory(self):
        with open (self.character, "r") as f:
            data = json.load(f)
        
        data["memory"] = self.memory
        
        with open (self.character, "w") as f:
            json.dump(data, f, indent=2)

    def appendMemory(self, role, content):
        self.memory.append({"role":role, "content":content})

    def buildPrompt(self, cmd):
        prompt =  "<|im_start|>system" + self.personality + "\n" + self.story + "<|im_end|>" + "\n"
        for msg in self.memory:
            prompt+= f"<|im_start|>{msg['role']}\n{msg['content']}<|im_end|>\n"
        prompt += "<|im_start|>user" + cmd
        prompt += "<|im_start|>assistant\n"
        return prompt

llm = LLM()

class Main:
    def __init__(self):
        pass
        self.listeners = []
        self.rayshell = Character("/home/venkat/cypher-shell/apps/characters/rayshell.json")
        # res = self.rayshell.initialMsg()
        # if res:
            # self.notifyListeners(res)
    
    def notifyListeners(self, response):    
        for callback in list(self.listeners):
            try:
                callback(response)
            except Exception as e:
                print("Callback error {e}")

    def interCept(self, cmd):
        def task():
            userInput = cmd.strip()
            self.rayshell.appendMemory("user", userInput)
            prompt = self.rayshell.buildPrompt(cmd)
            response = llm.chat(prompt, max=200, stop=["<|im_end|>"])
            self.rayshell.appendMemory("assistant", response)
            self.rayshell.saveMemory()
            self.notifyListeners(response)
        thread = threading.Thread(target=task)
        thread.start()

    def addListener(self, callback):
        self.listeners.append(callback)