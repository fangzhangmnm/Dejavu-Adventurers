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

#################################################################################
#################################################################################
#################################################################################


"""renpy
init offset=-100


default dejavu_store.scenario_data=None # don't put objects here. pure json. should be static
default dejavu_store.current={} # pointers to the objects in scenario_data we are currently writing to
default dejavu_store.state="disabled"
default dejavu_store.character_objects={} # stores the DejavuCharacter objects
default dejavu_store.diary_references={} # stores the diary list references. Will be cleared when new scenario starts
default dejavu_store.log_level=2
        


define NARRATOR_NAME="SYSTEM"
define ONGOING_OUTCOME_NAME="ONGOING"
define PLAYER_QUIT_OUTCOME_NAME="PLAYER_QUIT"

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

def log_text(text):
    for line in text.split("\n"):
        renpy.log(line)
    renpy.log("")

def log_object(obj):
    import json
    text=json.dumps(obj,indent=4,default=lambda o: '<not serializable>')
    for line in text.split("\n"):
        renpy.log(line)
    renpy.log("")

def call_incident(outcome_name,comment="",history=None,*args,**kwargs):
    history=history or dejavu_store.get_object(dejavu_store.current['dialogue'])['content']
    history.append({
        'type':'call',
        'outcome_name':outcome_name,
        'comment':comment,
    })

def jump_outcome(outcome_name,comment="",*args,**kwargs):
    dialogue=dejavu_store.get_object(dejavu_store.current['dialogue'])
    dialogue['outcome_name']=outcome_name
    dialogue['outcome_comment']=comment

def scenario(name,*args,**kwargs):
    dejavu_store.scenario_data={
        'name':name,
        'summary':"",
        'characters':{},
        'outcomes':{},
        'opening_dialogue':{
            'name':"Opening",
            'description':"",
            'content':[],
        },
        'example_dialogues':{},
        'player_character_name':"Player",
        'npc_names':[],
    }
    inject_DSL()

def end_scenario(what="",*args,**kwargs):
    dejavu_store.set_state("disabled")

def summary(content,*args,**kwargs):
    dejavu_store.scenario_data['summary']=content


def character(name,is_player=False,*args,**kwargs):
    assert name!=NARRATOR_NAME
    dejavu_store.scenario_data['characters'].setdefault(name,{
        'name':name,
        'description':"",
        'personality':"",
        'diary_list':[],
    })
    dejavu_store.current['character']=('characters',name)
    if is_player:
        dejavu_store.scenario_data['player_character_name']=name
    else:
        dejavu_store.scenario_data['npc_names'].append(name)
    dejavu_store.character_objects[name]=dejavu_store.DejavuCharacter(name,is_player=is_player,*args,**kwargs)
    return dejavu_store.character_objects[name]

def AICharacter(name,*args,**kwargs):
    return character(name,is_player=False,*args,**kwargs)

def PlayerCharacter(name,*args,**kwargs):
    dejavu_store.scenario_data['player_character_name']=name
    return character(name,is_player=True,*args,**kwargs)

dejavu_narrator=dejavu_store.DejavuCharacter(NARRATOR_NAME)

def description(content,*args,**kwargs):
    character=dejavu_store.get_object(dejavu_store.current['character'])
    character['description']=content

def personality(content,*args,**kwargs):   
    character=dejavu_store.get_object(dejavu_store.current['character'])
    character['personality']=content

def read_diary(diary_list:list):
    character=dejavu_store.get_object(dejavu_store.current['character'])
    character['diary_list'].extend(diary_list)

def write_diary(diary_list_reference:list):
    character=dejavu_store.get_object(dejavu_store.current['character'])
    dejavu_store.diary_references[character['name']]=diary_list_reference

def outcome(name,label=None,type='outcome',once=False,*args,**kwargs):
    dejavu_store.scenario_data['outcomes'].setdefault(name,{
        'name':name,
        'label':label or name,
        'condition':"",
        'type':type,
    })
    dejavu_store.current['outcome']=('outcomes',name)

def incident(name,label=None,once=True,*args,**kwargs):
    outcome(name,label,type='incident',once=once)

def condition(content,*args,**kwargs):
    outcome=dejavu_store.get_object(dejavu_store.current['outcome'])
    outcome['condition']=content

def opening_dialogue(name='Opening',*args,**kwargs):
    dejavu_store.scenario_data['opening_dialogue']['name']=name
    dejavu_store.current['dialogue']=('opening_dialogue',)
    dejavu_store.set_state("opening_dialogue")

def example_dialogue(name,*args,**kwargs):
    dejavu_store.scenario_data['example_dialogues'].setdefault(name,{
        'name':name,
        'description':"",
        'content':[],
        'outcome_name':"",
        'outcome_comment':"",
    })
    dejavu_store.current['dialogue']=('example_dialogues',name)
    dejavu_store.set_state("example_dialogue")

def inject_DSL():
    store.call_incident=call_incident
    store.jump_outcome=jump_outcome
    store.scenario=scenario
    store.end_scenario=end_scenario
    store.summary=summary
    store.character=character
    store.AICharacter=AICharacter
    store.PlayerCharacter=PlayerCharacter
    store.narrator=dejavu_narrator
    store.description=description
    store.personality=personality
    store.read_diary=read_diary
    store.write_diary=write_diary
    store.outcome=outcome
    store.incident=incident
    store.condition=condition
    store.opening_dialogue=opening_dialogue
    store.example_dialogue=example_dialogue

    store.log_text=log_text
    store.log_object=log_object
inject_DSL()

"""renpy
default dejavu_store.rollback=dejavu_store.RollBack() # initialize the rollback system at the new game

label dejavu_dialogue_loop:
    python:
        assert dejavu_store.state=='disabled', "You must call end_scenario() before calling dejavu_dialogue_loop."
        dejavu_store.history=list(dejavu_store.scenario_data['opening_dialogue']['content'])
        dejavu_store.removed_incidents=[]
        dejavu_store.set_state("playing")
        dejavu_store.outcome=ONGOING_OUTCOME_NAME
        dejavu_store.player_character_name=dejavu_store.scenario_data['player_character_name']
        dejavu_store.npc_names=dejavu_store.scenario_data['npc_names']
        if dejavu_store.log_level>1:
            log_text("Compiled scenario:")
            log_object(dejavu_store.scenario_data)
    while True:
        # player input
        python:
            dejavu_store.user_input=dejavu_store.rollback.get()
            if dejavu_store.user_input is None:
                renpy.suspend_rollback(True)
                dejavu_store.user_input = renpy.input("What do you say ? (enter to skip, 'quit' to quit)", length=1000) or "" # need to put in separate statement to make fix_rollback work
                dejavu_store.rollback.set(dejavu_store.user_input)
                renpy.suspend_rollback(False)
        if dejavu_store.user_input.lower() in ["quit","exit"]:
            $ dejavu_store.outcome=PLAYER_QUIT_OUTCOME_NAME
            call dejavu_dialogue_loop_finally_block from dejavu_dialogue_loop_label_1
            return
        if len(dejavu_store.user_input)>0:
            $ dejavu_store.Player=dejavu_store.character_objects[dejavu_store.player_character_name]
            $ dejavu_store.Player(dejavu_store.user_input,no_substitution=True)

        # npc dialogue
        $ dejavu_store.iNPC=0
        while dejavu_store.iNPC<len(dejavu_store.npc_names):
            python:
                dejavu_store.NPC=dejavu_store.character_objects[dejavu_store.npc_names[dejavu_store.iNPC]]
                dejavu_store.npc_name=dejavu_store.npc_names[dejavu_store.iNPC]
                dejavu_store.ai_reply=dejavu_store.rollback.get()
                if dejavu_store.ai_reply is None:
                    dejavu_store.ai_reply=dejavu_store.perform_roleplay_query(dejavu_store.npc_name,dejavu_store.scenario_data, dejavu_store.history)
                    dejavu_store.rollback.set(dejavu_store.ai_reply)
                dejavu_store.iNPC+=1
            $ dejavu_store.NPC(dejavu_store.ai_reply,no_substitution=True)

            # check outcome. 
            # unfortunately, we need to do this after each NPC dialogue, because AI might be distracted by the other NPC's dialogue
            python:
                dejavu_store.outcome_tuple=dejavu_store.rollback.get()
                if dejavu_store.outcome_tuple is None:
                    dejavu_store.outcome_tuple=dejavu_store.perform_check_outcome_query(dejavu_store.scenario_data,dejavu_store.history,removed_incidents=dejavu_store.removed_incidents)
                    dejavu_store.rollback.set(dejavu_store.outcome_tuple)
                dejavu_store.outcome_name,dejavu_store.outcome_type,dejavu_store.outcome_comment=dejavu_store.outcome_tuple
            
            if dejavu_store.outcome_type=="incident":
                $ dejavu_store.removed_incidents.append(dejavu_store.outcome_name)
                call expression dejavu_store.get_outcome_label(dejavu_store.outcome_name) from dejavu_dialogue_loop_label_2
            elif dejavu_store.outcome_type=="outcome":
                call dejavu_dialogue_loop_finally_block from dejavu_dialogue_loop_label_3
                jump expression dejavu_store.get_outcome_label(dejavu_store.outcome_name)

    $ assert False
    
label dejavu_dialogue_loop_finally_block:
    $ dejavu_store.set_state("disabled")

    python: # summary the dialogue for each character into their diary
        for name,diary_references in dejavu_store.diary_references.items():
            dejavu_store.summary_text=dejavu_store.rollback.get()
            if dejavu_store.summary_text is None:
                dejavu_store.summary_text=dejavu_store.perform_summary_query(name,dejavu_store.scenario_data,dejavu_store.history)
                dejavu_store.rollback.set(dejavu_store.summary_text)
            diary_references.append(dejavu_store.summary_text)

    return
"""