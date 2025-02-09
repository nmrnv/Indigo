import json

import requests


class ChatGPTClient:
    def __init__(self, access_key: str):
        self.access_key = access_key
        self.model = "gpt-3.5-turbo"

    def define_word(self, word: str):
        prompt = (
            "Give me a list of json objects for all definitions of the"
            f" word '{word}' with keys definition, part of speech,"
            " examples, synonyms, and antonyms. The definition should be"
            " detailed. Don’t say anything else, just print the json"
            " formatted message."
        )
        response = requests.post(
            url="https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {self.access_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(
                {
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                }
            ),
        )
        if not response.ok:
            ...
        message = response.json()["choices"][0]["message"]
        definitions = message["content"].replace("\n", "")
        breakpoint()
