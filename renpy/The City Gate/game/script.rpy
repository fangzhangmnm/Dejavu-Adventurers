init offset=0

default dejavu.history=[]
default dejavu.scenario_data={}
default dejavu.say_to_renpy=True
default dejavu.say_to_history=True
default dejavu.say_to_dejavu=False

init python hide:
    import dejavu as api
    import json
    dejavu.api=api
    renpy_say=renpy.say
    def say(who,what,*args,**kwargs):
        def get_name(who):
            if who is None: return dejavu.api.NARRATOR_NAME
            else: return str(who)
        if dejavu.say_to_history:
            dejavu.api.say(get_name(who),what,history=dejavu.history)
        if dejavu.say_to_dejavu:
            dejavu.api.say(get_name(who),what)
        if dejavu.say_to_renpy:
            what+="{len_history}, {len_dejavu}".format(
                len_history=len(dejavu.history),
                len_dejavu=len(json.dumps(dejavu.scenario_data))
            )
            renpy_say(who,what,*args,**kwargs)
    renpy.say=say
init python:
    def call(outcome_name,comment="", *args, **kwargs):
        if dejavu.say_to_history:
            dejavu.api.call(outcome_name,comment=comment,history=dejavu.history)
        if dejavu.say_to_dejavu:
            dejavu.api.call(outcome_name,comment=comment)
    def jump_outcome(outcome_name,comment="", *args, **kwargs):
        dejavu.api.jump(outcome_name,comment=comment)
    def scenario(name, *args, **kwargs):
        dejavu.scenario_data=dejavu.api.scenario(name)
        dejavu.say_to_renpy,dejavu.say_to_history,dejavu.say_to_dejavu=False,False,False
    def end_scenario(*args, **kwargs):
        dejavu.say_to_renpy,dejavu.say_to_history,dejavu.say_to_dejavu=True,False,False
    def summary(content, *args, **kwargs):
        dejavu.api.summary(content)
    def AICharacter(name, *args, **kwargs):
        dejavu.character(name,is_player=False)
        return Character(name, *args, **kwargs)
    def PlayerCharacter(name, *args, **kwargs):
        dejavu.character(name,is_player=True)
        return Character(name, *args, **kwargs)
    def description(content, *args, **kwargs):
        dejavu.api.description(content)
    def personality(content, *args, **kwargs):
        dejavu.api.personality(content)
    def outcome(name,label=None,*args, **kwargs):
        dejavu.api.outcome(name,label=label)
    def incident(name,label=None,once=True,*args, **kwargs):
        dejavu.api.incident(name,label=label,once=once)
    def condition(name,*args, **kwargs):
        dejavu.api.condition(name)
    def opening_dialogue(name='Opening',*args, **kwargs):
        dejavu.api.opening_dialogue(name)
        dejavu.say_to_renpy,dejavu.say_to_history,dejavu.say_to_dejavu=True,True,True
    def example_dialogue(name,*args, **kwargs):
        dejavu.api.example_dialogue(name)
        dejavu.say_to_renpy,dejavu.say_to_history,dejavu.say_to_dejavu=False,False,True
    

label start:
    scenario "Demo Scenario"
    $ e=AICharacter("Eileen")
    opening_dialogue "Opening"
    e "Hello, I'm Eileen. Nice to meet you."
    e "I'm a character in this game."
    
    end_scenario "Demo Scenario"






    
