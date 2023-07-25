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
init python:
    

    NARRATOR_NAME="SYSTEM"
    ONGOING_OUTCOME_NAME="ONGOING"

    def _say(character_name,content,history=None,):
        history=history or get_object(dejavu.current['dialogue'])['content']
        history.append({
            'type':'dialogue',
            'character':character_name,
            'content':content,
        })

    def _character(name):
        dejavu.scenario_data['characters'].setdefault(name,{
            'name':name,
            'description':"",
            'personality':"",
        })
        dejavu.current['character']=('characters',name)
        return lambda content: _say(name,content)

    def narrator(content,history=None):
        history=history or get_object(dejavu.current['dialogue'])['content']
        history.append({
            'type':'narrate',
            'content':content,
        })

    def call(outcome_name,comment="",history=None):
        history=history or get_object(dejavu.current['dialogue'])['content']
        history.append({
            'type':'call',
            'outcome_name':outcome_name,
            'comment':comment,
        })

    def jump(outcome_name,comment=""):
        dialogue=get_object(dejavu.current['dialogue'])
        dialogue['outcome_name']=outcome_name
        dialogue['outcome_comment']=comment

    def scenario(name):
        dejavu.scenario_data={
            'name':name,
            'summary':"",
            'characters':{},
            'outcomes':{},
            'opening_dialogue':None,
            'example_dialogues':{},
            'player_character_name':None,
        }

    def summary(content):
        dejavu.scenario_data['summary']=content

    def AICharacter(name):
        return _character(name)

    def PlayerCharacter(name):
        dejavu.scenario_data['player_character_name']=name
        return _character(name)

    def description(content):
        character=get_object(dejavu.current['character'])
        character['description']=content

    def personality(content):   
        character=get_object(dejavu.current['character'])
        character['personality']=content

    def _outcome(name,label=None,type='outcome',once=False):
        dejavu.scenario_data['outcomes'].setdefault(name,{
            'name':name,
            'label':label or name,
            'condition':"",
            'type':type,
        })
        dejavu.current['outcome']=('outcomes',name)

    def outcome(name,label=None):
        _outcome(name,label,type='outcome')

    def incident(name,label=None,once=True):
        _outcome(name,label,type='incident',once=once)

    def condition(content):
        outcome=get_object(dejavu.current['outcome'])
        outcome['condition']=content


    def opening_dialogue(name='Opening'):
        dejavu.scenario_data['opening_dialogue']={
            'name':name,
            'description':"",
            'content':[],
        }
        dejavu.current['dialogue']=('opening_dialogue',)

    def example_dialogue(name):
        dejavu.scenario_data['example_dialogues'].setdefault(name,{
            'name':name,
            'description':"",
            'content':[],
            'outcome_name':"",
            'outcome_comment':"",
        })
        dejavu.current['dialogue']=('example_dialogues',name)

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






    
