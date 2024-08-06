import httpx
import requests
import json
from typing import Union, List, Optional, TYPE_CHECKING

headers = {
    'Authorization': 'Bearer cqSb6osehDe0Qx2AvJvjt6GzEflmExR4fDvgcMXyYAw',
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    'Content-Type': 'application/json'
}


class ZdwwAI():
    def __init__(self, api_key: str | None = None,
                 base_url: str | None = None):
        self.api_key = api_key
        headers['Authorization'] = f'Bearer {api_key}'
        if base_url is None:
            self.base_url = f"http://10.18.105.16:32058/v1/chat/completions"

    def call(self, messages: Union[str, List[str], List[int], object, None]):
        payload = json.dumps({
            "stop_token_ids": [
                151329,
                151336,
                151338
            ],
            "max_tokens": 1000,
            "model": "MaasTN-ChatGLM4-9B",
            "messages": messages
        })
        response = requests.request("POST", self.base_url, headers=headers, data=payload)
        return json.loads(response.text)

    def stream(self, messages: Union[str, List[str], List[int], object, None], stream: bool = False, ):

        payload = json.dumps({
            "stop_token_ids": [
                151329,
                151336,
                151338
            ],
            "max_tokens": 1000,
            "stream": stream,
            "model": "MaasTN-ChatGLM4-9B",
            "messages": messages
        })
        response = requests.request("POST", self.base_url, headers=headers, data=payload)
        dialogue_stream = response.text.split("data: ")
        dialogue_stream = [dialogue.strip() for dialogue in dialogue_stream if dialogue.strip()]
        return dialogue_stream[:-1]
