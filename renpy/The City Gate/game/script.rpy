init offset=0

default dejavu.history=[]
default dejavu.state=None
default dejavu.say_to_renpy=True
default dejavu.say_to_history=True
default dejavu.say_to_dejavu=False

init python hide:
    import dejavu as api
    import json
    dejavu.api=api
    def log_object(obj):
        for line in json.dumps(obj,indent=4).split("\n"):
            renpy.log(line)
    renpy.log_object=log_object
    class DejavuSayer:
        def __init__(self,func):
            self.func=func
        def __call__(self,*args,**kwargs):
            renpy.log("Before State")
            renpy.log_object(dejavu.state)
            dejavu.api.import_state(dejavu.state)
            result=self.func(*args,**kwargs)
            dejavu.state=dejavu.api.export_state()
            renpy.log("After State")
            renpy.log_object(dejavu.state)
            return result
    dejavu.persistent=lambda func:DejavuSayer(func)
    renpy_say=renpy.say
    def say(who,what,*args,**kwargs):
        if isinstance(who,DejavuSayer):
            who(what,*args,**kwargs)
        else:
            if dejavu.say_to_history or dejavu.say_to_dejavu:
                renpy.log("Before State")
                renpy.log_object(dejavu.state)
                dejavu.api.import_state(dejavu.state)
                get_name=lambda who:str(who) if who is not None else dejavu.api.NARRATOR_NAME
                if dejavu.say_to_history:
                    dejavu.api.say(get_name(who),what,history=dejavu.history)
                if dejavu.say_to_dejavu:
                    dejavu.api.say(get_name(who),what)
                dejavu.state=dejavu.api.export_state()
                renpy.log("After State")
                renpy.log_object(dejavu.state)
            if dejavu.say_to_renpy:
                renpy_say(who,what,*args,**kwargs)
    renpy.say=say
init python:
    @dejavu.persistent
    def call(outcome_name,comment="", *args, **kwargs):
        if dejavu.say_to_history:
            dejavu.api.call(outcome_name,comment=comment,history=dejavu.history)
        if dejavu.say_to_dejavu:
            dejavu.api.call(outcome_name,comment=comment)
    @dejavu.persistent
    def jump_outcome(outcome_name,comment="", *args, **kwargs):
        dejavu.api.jump(outcome_name,comment=comment)
    @dejavu.persistent
    def scenario(name, *args, **kwargs):
        dejavu.scenario_data=dejavu.api.scenario(name)
        dejavu.say_to_renpy,dejavu.say_to_history,dejavu.say_to_dejavu=False,False,False
    @dejavu.persistent
    def end_scenario(*args, **kwargs):
        dejavu.say_to_renpy,dejavu.say_to_history,dejavu.say_to_dejavu=True,False,False
    @dejavu.persistent
    def summary(content, *args, **kwargs):
        dejavu.api.summary(content)
    @dejavu.persistent
    def AICharacter(name, *args, **kwargs):
        dejavu.api.character(name,is_player=False)
        return Character(name, *args, **kwargs)
    @dejavu.persistent
    def PlayerCharacter(name, *args, **kwargs):
        dejavu.api.character(name,is_player=True)
        return Character(name, *args, **kwargs)
    @dejavu.persistent
    def description(content, *args, **kwargs):
        dejavu.api.description(content)
    @dejavu.persistent
    def personality(content, *args, **kwargs):
        dejavu.api.personality(content)
    @dejavu.persistent
    def outcome(name,label=None,*args, **kwargs):
        dejavu.api.outcome(name,label=label)
    @dejavu.persistent
    def incident(name,label=None,once=True,*args, **kwargs):
        dejavu.api.incident(name,label=label,once=once)
    @dejavu.persistent
    def condition(name,*args, **kwargs):
        dejavu.api.condition(name)
    @dejavu.persistent
    def opening_dialogue(name='Opening',*args, **kwargs):
        dejavu.api.opening_dialogue(name)
        dejavu.say_to_renpy,dejavu.say_to_history,dejavu.say_to_dejavu=True,True,True
    @dejavu.persistent
    def example_dialogue(name,*args, **kwargs):
        dejavu.api.example_dialogue(name)
        dejavu.say_to_renpy,dejavu.say_to_history,dejavu.say_to_dejavu=False,False,True
    

label start:
    scenario "Demo Scenario"
    $ e=AICharacter("Eileen")
    opening_dialogue "Opening"
    e "Hello, I'm Eileen. Nice to meet you."
    e "I'm a character in this game."
    $i=0
    while True:
        $i+=1
        e "This is the [i]-th time I say something."
    
    end_scenario "Demo Scenario"






    
