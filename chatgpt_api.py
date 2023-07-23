__version__ = "1.0.0"

# Import required libraries
import requests
import json
import urllib3
import time
from typing import Literal

# api_key="this is an api key"
# url="http://127.0.0.1:5005/v1/chat/completions"

# api_key=open("C:\\openai.txt").read()
# url="https://api.openai.com/v1/chat/completions"

_api_key,_url=None,None
_debug_print_request=False
_debug_print_response=False

def init_chatgpt_api(
        api_key,
        url="https://api.openai.com/v1/chat/completions",
        debug_print_request=False,
        debug_print_response=False
        ):
    global _api_key,_url
    _api_key,_url=api_key,url
    global _debug_print_request,_debug_print_response
    _debug_print_request,_debug_print_response=debug_print_request,debug_print_response


def completion(
        messages:"list[dict]",
        functions:"list[dict]|None"=None,
        function_call:Literal["auto","none"]|str="auto",
        temperature=1.0
        )->"list[dict]":
    if _url is None: raise Exception("You must call init_chatgpt_api(api_key,url) before using the completion function.")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {_api_key}"
    }
    data = {
        "model": "gpt-3.5-turbo-0613",
        "temperature": temperature,
        "messages": messages
    }
    if functions is not None and len(functions)>0:
        data["functions"]=functions
        data["function_call"]=function_call
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
    

    
def purify_label(prediction:str,labels:"list[str]",default:str="None",search_from:Literal["first","last"]="last")->str:
    if default is None: raise Exception("You must specify a default value.")
    # find the label which appears first/last in the prediction string
    best_label=default
    best_index=-1
    for label in labels:
        # find the index of the label in the prediction string
        index=prediction.rfind(label)
        if index!=-1:
            if best_index==-1 or (
                search_from=="last" and index>best_index
                ) or (
                search_from=="first" and index<best_index
                ):
                best_label=label
                best_index=index
    return best_label