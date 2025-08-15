import os, json

class Rayshell:
    def __init__(self):
        path = "/states.json"
        with open (path, "r") as f:
            data = json.load(f)
        self.chapter = str(data["currentChapter"])
        self.scene = str(data["currentScene"])
        self.Dialogue = int(data["currentDialogue"])

    def loadStory(self, path):
        with open (path, "r") as f:
            data = json.load(f)
        
        if self.chapter == 1:
            if self.scene == 1:
                dialogues = data.get("dialogues", [])
        
        for dialogue in dialogues:
            return dialogue

        return dialogue

    def intercept(self, cmd):
        if cmd in ["hi" or "hey" or "hello" or "who are you"]:
            self.loadStory("rayshell1.json")
        


