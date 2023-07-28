store=object()
dejavu_store=store.dejavu_store=object()
renpy=object()
renpy.substitute=lambda text: text
NARRATOR_NAME="SYSTEM"
ONGOING_OUTCOME_NAME="ONGOING"
PLAYER_QUIT_OUTCOME_NAME="PLAYER_QUIT"
class NoRollback:
    pass
def Character(name,*args,**kwargs):
    # color coding 
    def say(what,*args,**kwargs):
        if name==NARRATOR_NAME:
            print("\033[90m"+what+"\033[0m")
        else:
            print("\033[92m"+name+"\033[0m"+": "+"\033[94m"+what+"\033[0m")
    return say
narrator=Character(NARRATOR_NAME)
def log_text(text):
    print("\033[90m"+text+"\033[0m")
def log_object(obj):
    import json
    print("\033[90m"+json.dumps(obj,indent=4)+"\033[0m")

"""renpy
init offset=-100
init python hide:
"""

import requests
import json
import urllib3
import time
from typing import Literal

def on_new_scenario():
    assert dejavu_store.state=='disabled', "You cannot start a new scenario inside the ai dialogue loop"
    dejavu_store.current={}
    dejavu_store.state="disabled"
    dejavu_store.character_objects={}
    dejavu_store.diary_references={}
dejavu_store.on_new_scenario=on_new_scenario

def get_object(path):
    p=dejavu_store.scenario_data
    for key in path:
        p=p[key]
    return p
dejavu_store.get_object=get_object

def set_state(state:'Literal["disabled", "opening_dialogue","example_dialogue","playing"]'):
    assert state in ["disabled", "opening_dialogue","example_dialogue","playing"]
    dejavu_store.state=state
dejavu_store.set_state=set_state


def write_dialogue(character_name,content,destination=None):
    destination=destination or dejavu_store.get_object(dejavu_store.current['dialogue'])['content']
    if character_name==NARRATOR_NAME:
        destination.append({
            'type':'narrate',
            'content':content,
        })
    else:
        destination.append({
            'type':'dialogue',
            'character':character_name,
            'content':content,
        })
dejavu_store.write_dialogue=write_dialogue

def get_outcome_label(outcome_name):
    return dejavu_store.scenario_data['outcomes'][outcome_name]['label']
dejavu_store.get_outcome_label=get_outcome_label

def substitute(text):
    return renpy.substitute(text)

class DejavuCharacter:
    def __init__(self,name,is_player=False,*args,**kwargs):
        self.name=name
        self.is_player=is_player
        if self.name == NARRATOR_NAME:
            self.renpy_character=None
        else:
            self.renpy_character=Character(name,*args,**kwargs)
    def __call__(self,what,slience=False,no_substitution=False,*args,**kwargs):
        if not no_substitution: 
            # only substitute for example dialogue, and injected narrates
            # do not substitute for player input and ai generated dialogue
            what=substitute(what)
        if dejavu_store.state=="opening_dialogue":
            dejavu_store.write_dialogue(self.name,what)
            if not slience:(self.renpy_character or narrator)(what,*args,**kwargs)
        elif dejavu_store.state=="example_dialogue":
            dejavu_store.write_dialogue(self.name,what)
        elif dejavu_store.state=="playing":
            dejavu_store.write_dialogue(self.name,what,destination=dejavu_store.history)
            if not slience:(self.renpy_character or narrator)(what,*args,**kwargs)
dejavu_store.DejavuCharacter=DejavuCharacter

class RollBackHistory(NoRollback):
    def __init__(self):
        self.history={}
    def get(self,key,default=None):
        if key in self.history:
            return self.history[key]
        else:
            return default
    def set(self,key,value):
        self.history[key]=value
class RollBack:
    def __init__(self):
        self.history=RollBackHistory()
        self.counter=-1
    def get(self,default=None):
        self.counter+=1
        return self.history.get(self.counter,default=default)
    def set(self,value):
        self.history.set(self.counter,value)
dejavu_store.RollBack=RollBack


# ChatGPT API


dejavu_store._api_key,dejavu_store._url=None,None
dejavu_store._debug_print_request=False
dejavu_store._debug_print_response=False
dejavu_store._max_retry=5
dejavu_store._retry_delay=10

def init_chatgpt_api(api_key,proxy="https://api.openai.com/v1/chat/completions",debug_print_request=False,debug_print_response=False):
    dejavu_store._api_key,dejavu_store._url=api_key,proxy
    dejavu_store._debug_print_request,dejavu_store._debug_print_response=debug_print_request,debug_print_response


def completion(messages,temperature=1):
    if dejavu_store._url is None: raise Exception("You must call init_chatgpt_api(api_key,url) before using the completion function.")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {dejavu_store._api_key}"
    }
    data = {
        "model": "gpt-3.5-turbo-0613",
        # "model": "gpt-4-0613",
        "temperature": temperature,
        "messages": messages
    }
    if dejavu_store._debug_print_request: print("Request:",messages)
    completion=None
    i_retry=0
    while completion is None:
        response=None
        while response is None:
            try:
                response = requests.post(dejavu_store._url, headers=headers, data=json.dumps(data))
            except urllib3.exceptions.MaxRetryError:
                print("MaxRetryError, retrying in 5 seconds...")
                time.sleep(5)
            if response is None:
                print("No response, retrying in 5 seconds...")
                time.sleep(dejavu_store._retry_delay)
        if response.status_code == 200:
            completion = response.json()["choices"][0]["message"]
            messages.append(completion)
            if dejavu_store._debug_print_response: print("Response:",completion)
            return messages  
        else:
            if dejavu_store._debug_print_response: print(f"Error: {response.status_code}, {response.text}")
            # raise Exception(f"Error: {response.status_code}, {response.text}")
            print(f"Error: {response.status_code}, {response.text}")
            i_retry+=1
            if i_retry>=dejavu_store._max_retry:
                raise Exception(f"Error: {response.status_code}, {response.text}")
            time.sleep(dejavu_store._retry_delay)
    
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

def convert_history_plain_text(history):
    text=""
    for item in history:
        if item['type']=='dialogue':
            text+=item["character"]+": "+item["content"]+"\n"
        elif item['type']=='narrate':
            text+=item["content"]+"\n"
    return text

def convert_history_roleplay_style(history,perspective_character_name=None):
    request=[]
    for item in history:
        if item['type']=='dialogue':
            if item["character"]==perspective_character_name:
                request.append({"role": "assistant","content": item["content"]})
            else:
                request.append({"role": "user","content": item["character"]+": "+item["content"]})
        elif item['type']=='narrate':
            request.append({"role": "system","content": item["content"]})
        elif item['type']=='call':
            request.append({"role": "system","content": "[call: "+item["outcome_name"]+"]"})
    return request

def compose_roleplay_request(character_name,scenario_data,history=[]):
    character=scenario_data["characters"][character_name]
    other_characters=[c for c in scenario_data["characters"].keys() if c!=character_name]
    request=[]
    prompt="Write {character_name}'s next reply in a fictional chat with {other_characters}. Write 1 reply in 1 to 2 lines. Be proactive, creative, and drive the plot and conversation forward. Always stay in character and avoid repetition. \n\n{character_description}\n\n{character_name}'s personality: {character_personality}\n\nCircumstances and context of the dialogue: {scenario_summary}".format(
        character_name=character_name,
        other_characters=", ".join(other_characters),
        character_description=character['description'],
        character_personality=character['personality'],
        scenario_summary=scenario_data['summary'],
    )
    request.append({"role": "system", "content": prompt})

    for i,diary_text in enumerate(character['diary_list']):
        prompt="[{character_name}'s diary {id}]\n{diary_text}".format(character_name=character_name,id=i,diary_text=diary_text)
        request.append({"role": "system", "content": prompt})

    for i,example_dialogue in enumerate(scenario_data["example_dialogues"].values()):
        prompt="[Example Dialogue {id}]\n".format(id=i)
        request.append({"role": "system", "content": prompt})
        request.extend(convert_history_roleplay_style(example_dialogue["content"],perspective_character_name=character_name))
    prompt="[Your Own Dialogue]\ncomment: {comment}".format(comment=scenario_data["summary"])
    request.append({"role": "system", "content": prompt})
    request.extend(convert_history_roleplay_style(history,perspective_character_name=character_name))
    prompt="[Write the next reply only as {character_name}]".format(character_name=character["name"])
    request.append({"role": "system", "content": prompt})
    return request



def compose_check_outcome_request(scenario_data,history,remove_incidents=[]):
    request=[]
    prompt="Please read the dialogue of a role playing game and determine whether a certain condition is reached.\n\n"
    for i,outcome in enumerate(scenario_data["outcomes"].values()):
        if outcome['name'] in remove_incidents: continue
        if outcome['type']=='incident':
            prompt+="{id}. when {condition}, then reply \"your reason, {outcome_name}\"\n".format(id=i,condition=outcome["condition"],outcome_name=outcome["name"])
        else:
            prompt+="{id}. if you are sure that the conversation ends with {condition}, then reply \"your reason, {outcome_name}\"\n".format(id=i,condition=outcome["condition"],outcome_name=outcome["name"])
    prompt+="{id}. For most of the cases, the dialogue need to be follow up, please reply \"The conversation is ongoing, {outcome_name}\"\n".format(id=len(scenario_data["outcomes"]),outcome_name=ONGOING_OUTCOME_NAME)
    request.append({"role": "system", "content": prompt})

    for i,example_dialogue in enumerate(scenario_data["example_dialogues"].values()):
        prompt="[Example Dialogue {id}]".format(id=i)
        request.append({"role": "system", "content": prompt})
        prompt=convert_history_plain_text(example_dialogue["content"])
        request.append({"role": "user", "content": prompt})
        prompt="{REASON}, {outcome_name}".format(REASON=example_dialogue["outcome_comment"],outcome_name=example_dialogue["outcome_name"])
        request.append({"role": "assistant", "content": prompt})

    prompt="Remember: For most of the cases, the dialogue need to be follow up, please reply \"your reason, {outcome_name}\n[Your Own Dialogue]\n".format(outcome_name=ONGOING_OUTCOME_NAME)
    request.append({"role": "system", "content": prompt})
    prompt=convert_history_plain_text(history)
    request.append({"role": "user", "content": prompt})

    return request

def compose_summary_request(character_name,scenario_data,history):
    prompt="summarize the dialogue in 1 small paragraph from {character_name}'s perspective.\n{character_name}'s personality: {character_personality}\nPlease stay in the character, as that character is writing a diary. Only contain the main text, not the heading and signature.".format(
        character_name=character_name,
        character_personality=scenario_data["characters"][character_name]['personality'],
    )
    request=[{"role": "system", "content": prompt}]
    prompt=convert_history_plain_text(history)
    request.append({"role": "user", "content": prompt})
    return request

def completion_with_log(name,query,*args,**kwargs):
    if dejavu_store.log_level>0:
        log_text("performing {name} query...".format(name=name))
        if dejavu_store.log_level>1:
            log_text("query:")
            log_object(query)
    response=completion(query,*args,**kwargs)
    if dejavu_store.log_level>0:
        log_text("{name} query responsed".format(name=name))
        if dejavu_store.log_level>1:
            log_text("response:")
            log_object(response[-1])
    return response

def perform_roleplay_query(character_name,scenario,history):
    request=compose_roleplay_request(character_name,scenario,history)
    response=completion_with_log("perform_roleplay_query",request,temperature=0.5)
    return response[-1]["content"]

def perform_check_outcome_query(scenario,history,removed_incidents=[]):
    if len(scenario["outcomes"])-len(removed_incidents)<=0:
        return ONGOING_OUTCOME_NAME, "ongoing", "No outcome defined."
    request=compose_check_outcome_request(scenario,history,remove_incidents=removed_incidents)
    response=completion_with_log("check_outcome",request,temperature=0)
    response_text=response[-1]["content"]
    if dejavu_store.log_level>=1:
        log_text(response_text)
    target_labels=list(scenario['outcomes'].keys())+[ONGOING_OUTCOME_NAME]
    outcome_name=purify_label(response_text,target_labels,default=ONGOING_OUTCOME_NAME)
    if outcome_name==ONGOING_OUTCOME_NAME:
        outcome_type="ongoing"
    else:
        outcome_type=scenario["outcomes"][outcome_name]["type"]
    return outcome_name, outcome_type, response_text

def perform_summary_query(character_name,scenario,history):
    request=compose_summary_request(character_name,scenario,history)
    response=completion_with_log("summary",request,temperature=0)
    summary=response[-1]["content"]
    summary=summary.replace("\n"," ")
    return summary

dejavu_store.init_chatgpt_api=init_chatgpt_api
dejavu_store.perform_roleplay_query=perform_roleplay_query
dejavu_store.perform_check_outcome_query=perform_check_outcome_query
dejavu_store.perform_summary_query=perform_summary_query

dejavu_store.init_chatgpt_api(api_key=open("C:\\openai.txt").read(), proxy="https://api.openai.com/v1/chat/completions")

