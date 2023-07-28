renpy=object()

character_objects:"dict[Character]"={}
scenario_object:"Scenario"=None
current=object()
"""renpy
default dejavu.character_objects={}
default dejavu.scenario_object=None
default dejavu.current=object()


init python in dejavu:
"""

# ============ Data Model ============
from dataclasses import dataclass,field
from typing import Literal

@dataclass
class Character:
    name:str
    is_player:bool=False
    is_narrator:bool=False
    personality:str=""
    bio:str=""
    diaries:"list[str]"=field(default_factory=list)
    renpy_character:object=None
    def __call__(self,what,silence=False,no_substitution=False,*args,**kwargs):
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

narrator=Character(name="Narrator",is_narrator=True)

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
    items:"list[DialogueItem]"=[]
    outcome_name:str=""
    outcome_comment:str=""
    def write_dialogue(self,character:Character,content:str):
        assert isinstance(character,Character)
        if character.is_narrator:
            self.items.append(DialogueItem(type="narrate",content=content))
        else:
            self.items.append(DialogueItem(type="say",who=character.name,content=content))

@dataclass
class DialogueItem:
    type:"Literal['say','narrate','incident','comment']"
    who:str|None=None
    content:str

@dataclass
class Scenario:
    name:str
    summary:str=""
    opening_dialogue:"Dialogue"=None
    example_dialogues:"dict[str,Dialogue]"={}
    player_character_name:str="Player"
    npc_character_names:"list[str]"=[]
    npc_character_frequencies:"dict[str,float]"={}
    history:"Dialogue"=None


# ============ Domain Specific Language ============

_dsl_injection_list={}
def dsl_register(func):
    _dsl_injection_list[func.__name__]=func
    return func

def character(name,is_player=False,*args,**kwargs):
    current.character_name=name
    if name not in character_objects:
        renpy_character=renpy.store.Character(name,*args,**kwargs)
        character_objects[name]=Character(
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
    assert current.say_state=="disabled", "You can't start a new scenario in the middle of a ai_game_loop."
    scenario_object=Scenario(name=name,*args,**kwargs)

@dsl_register
def end_scenario(*args,**kwargs):
    current.say_state="disabled"

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
        elif isinstance(name_or_object,Character):
            character_object=name_or_object
        else:
            raise Exception("Invalid character_list")
        frequency=1.0
        if i<len(character_list) and isinstance(character_list[i],(int,float)):
            frequency=character_list[i]
            i+=1
        if character_object.is_player:
            scenario_object.player_character_name=character_object.name
        else:
            scenario_object.npc_character_names.append(character_object.name)
            scenario_object.npc_character_frequencies[character_object.name]=frequency

@dsl_register
def opening_dialogue(dialogue_name="Opening",*args,**kwargs):
    scenario_object.opening_dialogue=Dialogue(name=dialogue_name)
    current.say_state="opening_dialogue"


@dsl_register
def example_dialogue(dialogue_name,*args,**kwargs):
    scenario_object.example_dialogues[dialogue_name]=Dialogue(name=dialogue_name)
    current.say_state="example_dialogue"
    current.example_dialogue_name=dialogue_name

@dsl_register
def end_dialogue(*args,**kwargs):
    current.say_state="disabled"

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

def dsl_injection():
    renpy.store.__dict__.update(_dsl_injection_list)
dsl_injection()
