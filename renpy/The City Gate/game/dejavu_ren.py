renpy=object()
import chatgpt_ren as chatgpt

"""renpy
default dejavu.character_objects={}
default dejavu.scenario_object=None
default dejavu.current=dejavu.Current()
default dejavu.runtime=object()
default dejavu.narrator=dejavu.DejavuCharacter(name="narrator",is_narrator=True)
default dejavu.log_level=1
init python in dejavu:
"""
log_level=1

# ============ utilities ============
import json
import dataclasses

class EnhancedJSONEncoder(json.JSONEncoder):
        def default(self, o):
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            return "<non-serializable object>"
            # return super().default(o)

def log_object(json_object):
    for line in json.dumps(json_object,indent=4,cls=EnhancedJSONEncoder).split("\n"):
        renpy.log(line)

log=renpy.log


class RollBackHistory(renpy.store.NoRollback):
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

rollback=RollBack()
# ============ Data Model ============
from dataclasses import dataclass,field
from typing import Literal


character_objects:"dict[str,DejavuCharacter]"={}
scenario_object:"Scenario"=None
class Current:
    def __init__(self):
        self.say_state="disabled"
        self.character_name=""
        self.example_dialogue_name=""
        self.outcome_name=""
        self.user_input=""
    
current=Current()

@dataclass
class DejavuCharacter:
    name:str
    is_player:bool=False
    is_narrator:bool=False
    personality:str=""
    bio:str=""
    diaries:"list[str]"=field(default_factory=list)
    renpy_character:object=None
    def __call__(self,what,silence=False,no_substitution=False,*args,**kwargs):
        if self.is_narrator:
            self.renpy_character=renpy.store.narrator
        if not no_substitution:
            what=renpy.substitute(what)
        if current.say_state=="disabled":
            if not silence: self.renpy_character(what,*args,**kwargs)
        elif current.say_state=="opening_dialogue":
            get_current_dialogue().write_dialogue(self,what)
            if not silence: self.renpy_character(what,*args,**kwargs)
        elif current.say_state=="example_dialogue":
            get_current_dialogue().write_dialogue(self,what)
        elif current.say_state=="playing":
            get_current_dialogue().write_dialogue(self,what)
            if not silence: self.renpy_character(what,*args,**kwargs)
narrator=DejavuCharacter(name="narrator",is_narrator=True)

def get_current_dialogue():
    if current.say_state=="opening_dialogue":
        return scenario_object.opening_dialogue
    elif current.say_state=="example_dialogue":
        return scenario_object.example_dialogues[current.example_dialogue_name]
    elif current.say_state=="playing":
        return scenario_object.history
    else:
        assert False

@dataclass
class Dialogue:
    name:str
    items:"list[DialogueItem]"=field(default_factory=list)
    outcome_name:str=""
    outcome_comment:str=""
    def write_dialogue(self,character:DejavuCharacter,content:str):
        assert isinstance(character,DejavuCharacter)
        if character.is_narrator:
            self.items.append(DialogueItem(type="narrate",content=content))
        else:
            self.items.append(DialogueItem(type="say",who=character.name,content=content))
    def get_last(self,type="Literal['say','narrate','incident','comment','any']",default=None):
        for item in reversed(self.items):
            if item.type==type or type=="any":
                return item
        return default  

@dataclass
class DialogueItem:
    content:str
    type:"Literal['say','narrate','incident','comment']"
    who:str|None=None

@dataclass
class Scenario:
    name:str
    summary:str=""
    opening_dialogue:"Dialogue"=None
    example_dialogues:"dict[str,Dialogue]"=field(default_factory=dict)
    player_character_name:str="Player"
    npc_character_names:"list[str]"=field(default_factory=list)
    character_frequencies:"dict[str,float]"=field(default_factory=dict)
    history:"Dialogue"=None
    outcomes:"dict[str,Outcome]"=field(default_factory=dict)
    can_quit:bool=False
    quit_label:str="ERROR"
    def get_all_character_names(self):
        return [self.player_character_name]+self.npc_character_names
    def get_non_expired_outcomes(self):
        return [outcome for outcome in self.outcomes.values() if not outcome.expired]
    def get_outcome_label(self,outcome_name):
        if outcome_name not in self.outcomes:
            return "Unknown"
        return self.outcomes[outcome_name].label

@dataclass
class Outcome:
    name:str
    label:str
    condition:str=""
    type:"Literal['outcome','incident']"="outcome"
    once:bool=False
    expired:bool=False
    def on_trigger(self):
        if self.once and self.type=="incident":
            self.expired=True

# ============ Queries ============

chatgpt=renpy.store.chatgpt

ONGOING_OUTCOME_NAME="ONGOING"
PLAYER_QUIT_OUTCOME_NAME="PLAYER_QUIT"
NOBODY_NAME="NOBODY"

def convert_dialogue_to_text(dialogue:Dialogue):
    text=""
    for item in dialogue.items:
        if item.type=='say':
            text+=item.who+": "+item.content+"\n"
        elif item.type=='narrate':
            text+=item.content+"\n"
    return text

def convert_dialogue_to_json(dialogue:Dialogue,perspective_character_name:str="",mode:"Literal['roleplay','check_outcome']"="roleplay"):
    assert isinstance(perspective_character_name,str)
    request=[]
    for item in dialogue.items:
        if item.type=='say':
            if item.who==perspective_character_name:
                request.append({"role": "assistant","content": item.content})
            else:
                request.append({"role": "user","content": item.who+": "+item.content})
        elif item.type=='narrate':
            request.append({"role": "system","content": item.content})
        elif item.type=='incident':
            if mode=="roleplay":
                request.append({"role": "system","content": "[incident {who} is triggered, Please wait for system response]".format(who=item.who)})
            elif mode=="check_outcome":
                request.append({"role": "assistant","content": "{your_reason}, {outcome_name}".format(your_reason=item.content,outcome_name=item.who)})
    return request


def compose_roleplay_request(character_name):
    character_object=character_objects[character_name]
    other_characters=[c for c in scenario_object.get_all_character_names() if c!=character_name]
    history=scenario_object.history
    
    request=[]
    prompt="Write {character_name}'s next reply in a fictional chat with {other_characters}. Write 1 reply in 1 to 2 lines. Be proactive, creative, and drive the plot and conversation forward. Always stay in character and avoid repetition. \n\n{character_bio}\n\n{character_name}'s personality: {character_personality}\n\nCircumstances and context of the dialogue: {scenario_summary}".format(
        character_name=character_name,
        other_characters=", ".join(other_characters),
        character_bio=character_object.bio,
        character_personality=character_object.personality,
        scenario_summary=scenario_object.summary,
    )
    request.append({"role": "system", "content": prompt})

    for i,diary_text in enumerate(character_object.diaries):
        prompt="[{character_name}'s diary {id}]\n{diary_text}".format(character_name=character_name,id=i,diary_text=diary_text)
        request.append({"role": "system", "content": prompt})

    for i,example_dialogue in enumerate(scenario_object.example_dialogues.values()):
        prompt="[Example Dialogue {id}]\n".format(id=i)
        request.append({"role": "system", "content": prompt})
        request.extend(convert_dialogue_to_json(example_dialogue,perspective_character_name=character_name))
    prompt="[Your Own Dialogue]\ncomment: {comment}".format(comment=scenario_object.summary)
    request.append({"role": "system", "content": prompt})
    request.extend(convert_dialogue_to_json(history,perspective_character_name=character_name))
    prompt="[Write the next reply only as {character_name}]".format(character_name=character_object.name)
    request.append({"role": "system", "content": prompt})
    return request


def compose_check_outcome_request():
    request=[]
    prompt="Please read the dialogue of a role playing game and determine whether a certain condition is reached.\n\n"
    for i,outcome in enumerate(scenario_object.get_non_expired_outcomes()):
        if not outcome.expired:
            if outcome.type=='incident':
                prompt+="- {outcome_name}: when {condition}, then reply \"your reason, {outcome_name}\"\n".format(condition=outcome.condition,outcome_name=outcome.name)
            else:
                prompt+="- {outcome_name}: if you are sure that the conversation ends with {condition}, then reply \"your reason, {outcome_name}\"\n".format(condition=outcome.condition,outcome_name=outcome.name)
    prompt+="- {outcome_name}. For most of the cases, the dialogue need to be follow up, please reply \"The conversation is ongoing, {outcome_name}\"\n".format(outcome_name=ONGOING_OUTCOME_NAME)
    request.append({"role": "system", "content": prompt})

    for i,example_dialogue in enumerate(scenario_object.example_dialogues.values()):
        prompt="[Example Dialogue {id}]".format(id=i)
        request.append({"role": "system", "content": prompt})
        request.append({"role": "user", "content": convert_dialogue_to_text(example_dialogue)})
        # request.extend(convert_dialogue_to_json(example_dialogue,mode="check_outcome"))
        prompt="{REASON}, {outcome_name}".format(REASON=example_dialogue.outcome_comment,outcome_name=example_dialogue.outcome_name)
        request.append({"role": "assistant", "content": prompt})

    prompt="Remember: For most of the cases, the dialogue need to be follow up, please reply \"your reason, {outcome_name}\n[Your Own Dialogue]\n".format(outcome_name=ONGOING_OUTCOME_NAME)
    request.append({"role": "system", "content": prompt})
    # request.extend(convert_dialogue_to_json(scenario_object.history,mode="check_outcome"))
    request.append({"role": "user", "content": convert_dialogue_to_text(scenario_object.history)})

    return request



def compose_summary_request(character_name):
    prompt="summarize the dialogue in 1 small paragraph from {character_name}'s perspective. Please repharse and compress the dialogue into less than 100 words.\n{character_name}'s personality: {character_personality}\nPlease stay in the character, as that character is writing a diary.".format(
        character_name=character_name,
        character_personality=character_objects[character_name].personality,
    )
    request=[{"role": "system", "content": prompt}]
    prompt=convert_dialogue_to_text(scenario_object.history)
    request.append({"role": "user", "content": prompt})
    return request


def completion_with_log(name,query,*args,**kwargs):
    if log_level>0:
        log("performing {name} query...".format(name=name))
        if log_level>1:
            log("query:")
            log_object(query)
    response=chatgpt.completion(query,*args,**kwargs)
    if log_level>0:
        log("{name} query responsed".format(name=name))
        if log_level>1:
            log("response:")
            log_object(response[-1])
    return response


def perform_roleplay_query(character_name):
    request=compose_roleplay_request(character_name)
    response=completion_with_log("perform_roleplay_query",request,temperature=0.5)
    return response[-1]["content"]

def perform_check_outcome_query():
    if len(scenario_object.get_non_expired_outcomes())==0:
        return ONGOING_OUTCOME_NAME, "ongoing", "No outcome defined."
    request=compose_check_outcome_request()
    response=completion_with_log("check_outcome",request,temperature=0)
    response_text=response[-1]["content"]
    if log_level>=1:
        log(response_text)
    target_labels=list(scenario_object.outcomes.keys())+[ONGOING_OUTCOME_NAME]
    outcome_name=chatgpt.find_keyword_by_place(response_text,target_labels,default=ONGOING_OUTCOME_NAME)
    if outcome_name==ONGOING_OUTCOME_NAME:
        outcome_type="ongoing"
    else:
        outcome_type=scenario_object.outcomes[outcome_name].type
    return outcome_name, outcome_type, response_text

def perform_summary_query(character_name):
    request=compose_summary_request(character_name)
    response=completion_with_log("summary",request,temperature=0)
    summary=response[-1]["content"]
    summary=summary.replace("\n"," ")
    return summary

# ============ Domain Specific Language ============

from copy import deepcopy

_dsl_injection_list={}
def dsl_register(func):
    _dsl_injection_list[func.__name__]=func
    return func

def character(name,is_player=False,*args,**kwargs):
    current.character_name=name
    if name not in character_objects:
        renpy_character=renpy.store.Character(name,*args,**kwargs)
        character_objects[name]=DejavuCharacter(
            name=name,
            is_player=is_player,
            renpy_character=renpy_character,
            )
    return character_objects[name]

@dsl_register
def AICharacter(name,*args,**kwargs):
    return character(name,*args,**kwargs)

@dsl_register
def PlayerCharacter(name,*args,**kwargs):
    return character(name,is_player=True,*args,**kwargs)

@dsl_register
def personality(what,*args,**kwargs):
    character_objects[current.character_name].personality=what

@dsl_register
def bio(what,*args,**kwargs):
    character_objects[current.character_name].bio=what

@dsl_register
def scenario(name,*args,**kwargs):
    global scenario_object
    assert current.say_state=="disabled", "You can't start a new scenario in the middle of a dejavu_dialogue_loop."
    scenario_object=Scenario(name=name)

@dsl_register
def end_scenario(*args,**kwargs):
    scenario_object.history=deepcopy(scenario_object.opening_dialogue)
    current.say_state="disabled"
    # the default frequency of player is the sum of all non-player characters
    if scenario_object.character_frequencies[scenario_object.player_character_name]==0:
        scenario_object.character_frequencies[scenario_object.player_character_name]=sum(scenario_object.character_frequencies.values())

@dsl_register
def summary(what,*args,**kwargs):
    scenario_object.summary=what

@dsl_register
def characters(character_list):
    """character_list: [Player,"Aqua",2.0,Guard,Darkness]"""
    i=0
    while i<len(character_list):
        name_or_object=character_list[i]
        i+=1
        if isinstance(name_or_object,str):
            character_object=character_objects[name_or_object]
        elif isinstance(name_or_object,DejavuCharacter):
            character_object=name_or_object
        else:
            raise Exception("Invalid character_list")
        frequency=1.0 if not character_object.is_player else 0 # the default frequency of player is calculated later as the sum of all non-player characters
        if i<len(character_list) and isinstance(character_list[i],(int,float)):
            frequency=character_list[i]
            i+=1
        if character_object.is_player:
            scenario_object.player_character_name=character_object.name
        else:
            scenario_object.npc_character_names.append(character_object.name)
        scenario_object.character_frequencies[character_object.name]=frequency

@dsl_register
def opening_dialogue(dialogue_name="Opening",*args,**kwargs):
    scenario_object.opening_dialogue=Dialogue(name=dialogue_name)
    current.say_state="opening_dialogue"


@dsl_register
def example_dialogue(dialogue_name,*args,**kwargs):
    scenario_object.example_dialogues[dialogue_name]=Dialogue(name=dialogue_name)
    scenario_object.example_dialogues[dialogue_name].items.extend(deepcopy(scenario_object.opening_dialogue.items))
    current.say_state="example_dialogue"
    current.example_dialogue_name=dialogue_name

@dsl_register
def narrator_dejavu(what,*args,**kwargs):
    narrator(what,*args,**kwargs)

@dsl_register
def call_incident(name,comment="",*args,**kwargs):
    get_current_dialogue().items.append(DialogueItem(type="incident",who=name,content=comment))
    
@dsl_register
def jump_outcome(name,comment="",*args,**kwargs):
    get_current_dialogue().outcome_name=name
    get_current_dialogue().outcome_comment=comment


@dsl_register
def outcome(name,label=None,condition="",*args,**kwargs):
    scenario_object.outcomes[name]=Outcome(
        name=name,
        label=label or name,
        condition=condition,
        type="outcome",
        )
    current.outcome_name=name
    
@dsl_register
def incident(name,label=None,once=True,*args,**kwargs):
    scenario_object.outcomes[name]=Outcome(
        name=name,
        label=label or name,
        type="incident",
        once=once,
        )
    current.outcome_name=name

@dsl_register
def enable_quit(name,label=None,*args,**kwargs):
    scenario_object.can_quit=True
    scenario_object.quit_label=label or name
    
@dsl_register
def condition(what,*args,**kwargs):
    scenario_object.outcomes[current.outcome_name].condition=what


def dsl_injection():
    for key,value in _dsl_injection_list.items():
        renpy.store.__dict__[key]=value
dsl_injection()



# ============ Renpy Dialog Loop
# import random
import re


def roll_next_character_name():
    last_say_item=scenario_object.history.get_last(type="say",default=DialogueItem(content="",type="say",who=NOBODY_NAME))
    other_characters={name:frequency for name,frequency in scenario_object.character_frequencies.items() if name!=last_say_item.who}
    return renpy.random.choices(
        population=list(other_characters.keys()),
        weights=list(other_characters.values()),
        k=1,
        )[0]

def decide_next_character_name():
    if renpy.random.random()<.5:
        return roll_next_character_name()
    last_say_item=scenario_object.history.get_last(type="say",default=DialogueItem(content="",type="say",who=NOBODY_NAME))
    all_character_names=list(scenario_object.get_all_character_names())
    other_character_names=[name for name in all_character_names if name!=last_say_item.who]
    labels=['@'+name for name in other_character_names]+other_character_names
    mentioned_character=chatgpt.find_keyword_by_priority(last_say_item.content,labels,default=NOBODY_NAME,lower_case=False)
    if mentioned_character.startswith("@"): mentioned_character=mentioned_character[1:]
    if mentioned_character==NOBODY_NAME:
        return roll_next_character_name()
    else:
        correct_character_name=next((name for name in all_character_names if name==mentioned_character),NOBODY_NAME)
        assert correct_character_name!=NOBODY_NAME, "Character not found: "+mentioned_character
        return correct_character_name

def purify_ai_response(response_text):
    # CharacterName: Hello -> Hello
    response_text=re.sub(r"^[^:]+:","",response_text)
    return response_text

def purity_player_response(response_text):
    return response_text # feel free to prompt injection attack here


def write_diaries():
    for character_name in scenario_object.npc_character_names:
        diary=perform_summary_query(character_name)
        character_objects[character_name].diaries.append(diary)
        if log_level>=1:
            log("Diary of "+character_name+":")
            log(diary)

"""renpy
default dejavu.rollback=dejavu.RollBack()


label dejavu_dialogue_loop:
    python in dejavu:
        assert current.say_state=="disabled", "You need to call end_scenario() before starting the dejavu_dialogue_loop."
        current.say_state="playing"
        runtime.outcome_name=ONGOING_OUTCOME_NAME
        if log_level>=2:
            log("Compiled character objects:")
            log_object(character_objects)
            log("Compiled scenario:")
            log_object(scenario_object)
    while True:
        python in dejavu:
            # ============ Decide Next Character ============
            runtime.character_name=rollback.get()
            if runtime.character_name is None:
                runtime.character_name=decide_next_character_name()
                rollback.set(runtime.character_name)
        if dejavu.runtime.character_name==dejavu.scenario_object.player_character_name:
            # ============ Player Input ============
            python in dejavu:    
                runtime.user_input=rollback.get()
                if runtime.user_input is None:
                    renpy.suspend_rollback(True)
                    if scenario_object.can_quit:
                        runtime.user_input = renpy.input("What do you say ? (enter to skip, 'quit' to quit)", length=1000) or ""
                    else:
                        runtime.user_input = renpy.input("What do you say ? (enter to skip)", length=1000) or ""
                    runtime.user_input=purity_player_response(runtime.user_input)
                    renpy.suspend_rollback(False)
                    rollback.set(runtime.user_input)
            if dejavu.runtime.user_input.lower()=="quit" and dejavu.scenario_object.can_quit:
                python in dejavu:
                    runtime.outcome_name=PLAYER_QUIT_OUTCOME_NAME
                call dejavu_dialogue_loop_finally_block from dejavu_dialogue_loop_label_1
                jump  expression dejavu.scenario_object.quit_label
            if len(dejavu.runtime.user_input.strip())>0:
                python in dejavu:
                    character_objects[scenario_object.player_character_name](runtime.user_input,no_substitution=True)
        elif dejavu.runtime.character_name in dejavu.scenario_object.npc_character_names:
            # ============ NPC Input ============
            python in dejavu:
                runtime.user_input=rollback.get()
                if runtime.user_input is None:
                    runtime.user_input=perform_roleplay_query(runtime.character_name)
                    runtime.user_input=purify_ai_response(runtime.user_input)
                    rollback.set(runtime.user_input)
            if len(dejavu.runtime.user_input.strip())>0:
                python in dejavu:
                    character_objects[runtime.character_name](runtime.user_input,no_substitution=True)
        # ============ Check Outcome ============
        python in dejavu:
            runtime.outcome_name=rollback.get()
            if runtime.outcome_name is None:
                runtime.outcome_name=perform_check_outcome_query()
                rollback.set(runtime.outcome_name)
            runtime.outcome_name,runtime.outcome_type,runtime.outcome_comment=runtime.outcome_name
            runtime.outcome_label=scenario_object.get_outcome_label(runtime.outcome_name)
        if dejavu.runtime.outcome_type=="incident":
            python in dejavu:
                scenario_object.outcomes[runtime.outcome_name].on_trigger()
            call expression dejavu.runtime.outcome_label from dejavu_dialogue_loop_label_2
        elif dejavu.runtime.outcome_type=="outcome":
            call dejavu_dialogue_loop_finally_block from dejavu_dialogue_loop_label_3
            jump expression dejavu.runtime.outcome_label
        
            

    $ assert False, "should not reach here"
        




label dejavu_dialogue_loop_finally_block:
    $ dejavu.current.say_state="disabled"
    $ dejavu.write_diaries()
    return


















"""