renpy=object()

character_objects={}
scenario_objects={}
current=object()
"""renpy
default dejavu.character_objects={}
default dejavu.scenario_objects={}
default dejavu.current=object()


init python in dejavu:
"""

# ============ Data Model ============

        
class Character:
    @classmethod
    def get(cls,name)->"Character":
        return character_objects[name]
    @classmethod
    def get_current(cls)->"Character":
        return character_objects[current.character]
    @classmethod
    def set_current(cls,name,*args,**kwargs)->"Character":
        current.character=name
        if name not in character_objects:
            character_objects[name]=Character(name,*args,**kwargs)
        return character_objects[name]
    
    def __init__(self,name,is_player=False,*args,**kwargs):
        self.name=name
        self.is_player=is_player
        self.personality=""
        self.bio=""
        self.diaries=[]
        self.renpy_character=renpy.store.Character(name,*args,**kwargs)
    def __call__(self,what,*args,**kwargs):
        dispatch_say(self.name,what,*args,**kwargs)
    def add_diary(self,diary_text):
        self.diaries.append(diary_text)

def dispatch_say(who,what,*args,**kwargs):
    who_name=who.name if isinstance(who,Character) else who
    if who_name is None:
        renpy_character=renpy.store.narrator
    else:
        renpy_character=Character.get(who_name).renpy_character
    if current.say_state=="disabled":
        renpy_character(what,*args,**kwargs)
    elif current.say_state=="opening_dialogue":
        Dialogue.get_current().add_dialogue_or_narrate(who_name,what)
        renpy_character(what,*args,**kwargs)
    elif current.say_state=="example_dialogue":
        Dialogue.get_current().add_dialogue_or_narrate(who_name,what)
    elif current.say_state=="playing":
        Dialogue.get_current().add_dialogue_or_narrate(who_name,what)
        renpy_character(what,*args,**kwargs)


class Scenario:
    @classmethod
    def get_current(cls)->"Scenario":
        return scenario_objects[current.scenario]
    @classmethod
    def set_current(cls,name)->"Scenario":
        current.scenario=name
        if name not in scenario_objects:
            scenario_objects[name]=Scenario(name)
        return scenario_objects[name]
    def __init__(self,name):
        self.name=name
        self.summary=""
        self.player_character_name=""
        self.npc_character_names=[]
        self.npc_say_frequencies={}
        self.opening_dialogue=None
        self.example_dialogues={}
        self.outcomes={}
    def add_character(self,name_or_object,frequency=1.0):
        name=name_or_object.name if isinstance(name_or_object,Character) else name_or_object
        character_object=Character.get(name)
        if character_object.is_player:
            self.player_character_name=name
        else:
            self.npc_character_names.append(name)
            self.npc_say_frequencies[name]=frequency
    def set_current_opening_dialogue(self,dialogue_name):
        current.say_state="opening_dialogue"
        current.dialogue_parent="scenario"
        self.opening_dialogue=self.opening_dialogue or Dialogue(dialogue_name)
        self.current_dialogue=self.opening_dialogue
        return self.opening_dialogue
    def set_current_example_dialogue(self,dialogue_name):
        current.say_state="example_dialogue"
        current.dialogue_parent="scenario"
        if dialogue_name not in self.example_dialogues:
            self.example_dialogues[dialogue_name]=Dialogue(dialogue_name)
        self.current_dialogue=self.example_dialogues[dialogue_name]
        return self.example_dialogues[dialogue_name]
    def get_current_dialogue(self)->"Dialogue":
        return self.current_dialogue
    def set_current_outcome(self,outcome_name,label=None,type='outcome',once=False):
        self.outcomes[outcome_name]=Outcome(outcome_name,label=label,type=type,once=once)
        return self.outcomes[outcome_name]
    def get_current_outcome(self)->"Outcome":
        return self.current_outcome
    
class Outcome:
    def __init__(self,name,label=None,type='outcome',once=False):
        self.name=name
        self.label=label or name
        self.type=type
        self.once=once
        self.condition=""




class Dialogue:
    @classmethod
    def get_current(cls):
        if current.dialogue_parent=="scenario":
            return Scenario.get_current().get_current_dialogue()
        elif current.dialogue_parent=="history":
            raise NotImplementedError
    def __init__(self,name):
        self.name=name
        self.items=[]
        self.outcome=None
        self.outcome_comment=""
    def add_dialogue_or_narrate(self,who,what):
        who_name=who.name if isinstance(who,Character) else who
        if who is None:
            self.items.append({"type":"narrate","what":what})
        else:
            self.items.append({"type":"dialogue","who":who,"what":what})
    def add_incident(self,name,comment=""):
        self.items.append({"type":"incident","name":name,"comment":comment})
    def set_outcome(self,name,comment=""):
        self.outcome=name
        self.outcome_comment=comment



# ============ Domain Specific Language ============

_dsl_injection_list={}
def dsl_register(func):
    _dsl_injection_list[func.__name__]=func
    return func

@dsl_register
def AICharacter(name,*args,**kwargs):
    return Character.set_current(name,*args,**kwargs)

@dsl_register
def PlayerCharacter(name,*args,**kwargs):
    return Character.set_current(name,is_player=True,*args,**kwargs)

@dsl_register
def personality(what,*args,**kwargs):
    Character.get_current().personality=what

@dsl_register
def bio(what,*args,**kwargs):
    Character.get_current().bio=what

@dsl_register
def scenario(name,*args,**kwargs):
    return Scenario.set_current(name)

@dsl_register
def end_scenario(*args,**kwargs):
    global state
    state="disabled"

@dsl_register
def summary(what,*args,**kwargs):
    Scenario.get_current().summary=what

@dsl_register
def characters(character_list):
    """character_list: [Player,"Aqua",2.0,Guard,Darkness]"""
    i=0
    while i<len(character_list):
        name_or_object=character_list[i]
        i+=1
        frequency=1.0
        if i<len(character_list) and isinstance(character_list[i],(int,float)):
            frequency=character_list[i]
            i+=1
        Scenario.get_current().add_character(name_or_object,frequency)

@dsl_register
def opening_dialogue(dialogue_name="Opening",*args,**kwargs):
    return Scenario.get_current().set_current_opening_dialogue(dialogue_name)

@dsl_register
def example_dialogue(dialogue_name,*args,**kwargs):
    return Scenario.get_current().set_current_example_dialogue(dialogue_name)

@dsl_register
def end_dialogue(*args,**kwargs):
    global state
    state="disabled"

@dsl_register
def narrator_dejavu(what,*args,**kwargs):
    dispatch_say(None,what,*args,**kwargs)

@dsl_register
def call_incident(name,comment="",*args,**kwargs):
    Dialogue.get_current().add_incident(name,comment)

@dsl_register
def jump_outcome(name,comment="",*args,**kwargs):
    Dialogue.get_current().set_outcome(name,comment)



def dsl_injection():
    renpy.store.__dict__.update(_dsl_injection_list)
dsl_injection()
