__version__ = "1.0.0"

# Import required libraries
import requests
import json
import urllib3
import time

# api_key="this is an api key"
# url="http://127.0.0.1:5005/v1/chat/completions"

# api_key=open("C:\\openai.txt").read()
# url="https://api.openai.com/v1/chat/completions"

_api_key,_url=None,None
_debug_print_request=False
_debug_print_response=False

def init_chatgpt_api(api_key,url="https://api.openai.com/v1/chat/completions",debug_print_request=False,debug_print_response=False):
    global _api_key,_url
    _api_key,_url=api_key,url
    global _debug_print_request,_debug_print_response
    _debug_print_request,_debug_print_response=debug_print_request,debug_print_response


def completion(messages,temperature=1):
    if _url is None: raise Exception("You must call init_chatgpt_api(api_key,url) before using the completion function.")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {_api_key}"
    }
    data = {
        "model": "gpt-3.5-turbo",
        "temperature": temperature,
        "messages": messages
    }
    if _debug_print_request: print("Request:",messages)
    response=None
    while response is None:
        try:
            response = requests.post(_url, headers=headers, data=json.dumps(data))
        except urllib3.exceptions.MaxRetryError:
            print("MaxRetryError, retrying in 5 seconds...")
            time.sleep(5)
    if response.status_code == 200:
        completion = response.json()["choices"][0]["message"]
        messages.append(completion)
        if _debug_print_response: print("Response:",completion)
        return messages  
    else:
        if _debug_print_response: print(f"Error: {response.status_code}, {response.text}")
        raise Exception(f"Error: {response.status_code}, {response.text}")
    
def purify_label(label,labels,default=None):
    if default is None: raise Exception("You must specify a default value.")
    for target in labels:
        if target in label:
            return target
    return default