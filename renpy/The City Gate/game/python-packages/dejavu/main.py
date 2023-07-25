import sys
this=sys.modules[__name__]


this.scenario_data=None
this._p={}



def say(character_name,content,history=None,):
    history=history or this._pdialogue['content']
    history.append({
        'type':'dialogue',
        'character':character_name,
        'content':content,
    })

def narrator(content,history=None):
    history=history or this._pdialogue['content']
    history.append({
        'type':'narrate',
        'content':content,
    })

def call(outcome_name,comment="",history=None):
    history=history or this._pdialogue['content']
    history.append({
        'type':'call',
        'outcome_name':outcome_name,
        'comment':comment,
    })

def jump(outcome_name,comment=""):
    this._pdialogue['outcome_name']=outcome_name
    this._pdialogue['outcome_comment']=comment

def scenario(name):
    this.scenario_data={
        'name':name,
        'summary':"",
        'characters':{},
        'outcomes':{},
        'opening_dialogue':None,
        'example_dialogues':{},
        'player_character_name':None,
    }
    this._p=this.scenario_data

def load_scenario(scenario_data):
    this.scenario_data=scenario_data
    this._p=this.scenario_data

def summary(content):
    this.scenario_data['summary']=content


def character(name,is_player=False):
    this._p=this._pcharacter=this.scenario_data['characters'].setdefault(name,{
        'name':name,
        'description':"",
        'personality':"",
    })
    if is_player:
        this.scenario_data['player_character_name']=name
    return lambda content: say(name,content)

def description(content):
    this._pcharacter['description']=content

def personality(content):   
    this._pcharacter['personality']=content

def outcome(name,label=None,type='outcome'):
    this._p=this._poutcome=this.scenario_data['outcomes'].setdefault(name,{
        'name':name,
        'label':label or name,
        'condition':"",
        'type':type,
    })

def incident(name,label=None,once=True):
    outcome(name,label,type='incident')
    this._poutcome['once']=once

def condition(content):
    this._poutcome['condition']=content


def opening_dialogue(name='Opening'):
    this._p=this._pdialogue=this.scenario_data['opening_dialogue']={
        'name':name,
        'description':"",
        'content':[],
    }

def example_dialogue(name):
    this._p=this._pdialogue=this.scenario_data['example_dialogues'].setdefault(name,{
        'name':name,
        'description':"",
        'content':[],
        'outcome_name':"",
        'outcome_comment':"",
    })




NARRATOR_NAME="SYSTEM"
ONGOING_OUTCOME_NAME="ONGOING"

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
    request=[]
    prompt="Write {character_name}'s next reply in a fictional chat. Write 1 reply in 1 to 2 lines. Be proactive, creative, and drive the plot and conversation forward. Always stay in character and avoid repetition. \n\n{character_description}\n\n{character_name}'s personality: {character_personality}\n\nCircumstances and context of the dialogue: {scenario_summary}".format(
        character_name=character_name,
        character_description=character['description'],
        character_personality=character['personality'],
        scenario_summary=scenario_data['summary'],
    )
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


def perform_roleplay_query(character_name,scenario,history):
    try:
        from .chatgpt_api import completion
    except ImportError:
        from chatgpt_api import completion
    request=compose_roleplay_request(character_name,scenario,history)
    response=completion(request,temperature=0.5)
    return response[-1]["content"]

def perform_check_outcome_query(scenario,history,removed_incidents=[]):
    try:
        from .chatgpt_api import completion,purify_label
    except ImportError:
        from chatgpt_api import completion,purify_label
    request=compose_check_outcome_request(scenario,history,remove_incidents=removed_incidents)
    response=completion(request,temperature=0)
    response_text=response[-1]["content"]
    target_labels=list(scenario['outcomes'].keys())+[ONGOING_OUTCOME_NAME]
    outcome_name=purify_label(response_text,target_labels,default=ONGOING_OUTCOME_NAME)
    if outcome_name==ONGOING_OUTCOME_NAME:
        outcome_type="ongoing"
    else:
        outcome_type=scenario["outcomes"][outcome_name]["type"]
    return outcome_name, outcome_type, response_text

def example_game_loop(scenario):
    player_character_name=scenario["player_character_name"]
    npc_names=list(scenario["characters"].keys());npc_names.remove(player_character_name)
    history=[]
    removed_incidents=[]
    def say(character_name,content):
        print("\033[92m"+character_name+"\033[0m"+": "+"\033[94m"+content+"\033[0m")
        this.say(character_name,content,history=history)
    for item in scenario["opening_dialogue"]["content"]:
        if item["type"]=="dialogue":
            say(item["character"],item["content"])
        elif item["type"]=="narrate":
            say(NARRATOR_NAME,item["content"])
    try:
        while True:
            player_input=None
            while player_input is None:
                player_input=input("Your reply: ")
            if player_input.lower() in ["quit","exit"]:
                return ONGOING_OUTCOME_NAME
            elif "\me " in player_input:
                dialogue,action=player_input.split("\me ")
                if len(dialogue.strip())>0:
                    say(player_character_name,dialogue)
                if len(action.strip())>0:
                    say(NARRATOR_NAME,player_character_name+" "+action)
            elif player_input.startswith("\gm "):
                say(NARRATOR_NAME,player_input[4:])
            else:
                say(player_character_name,player_input)
            for npc_name in npc_names:
                npc_input=perform_roleplay_query(npc_name,scenario,history)
                say(npc_name,npc_input)
            outcome_name,outcome_type,outcome_comment=perform_check_outcome_query(scenario,history,removed_incidents=removed_incidents)
            print("\033[90m"+outcome_comment+"\033[0m")
            if outcome_type=="incident":
                print("\033[91m"+"Incident: "+outcome_name+"\033[0m")
                removed_incidents.append(outcome_name)
            elif outcome_type=="outcome":
                print("\033[91m"+"Outcome: "+outcome_name+"\033[0m")
                return outcome_name
            else: #ongoing
                pass

    except KeyboardInterrupt:
        return ONGOING_OUTCOME_NAME

if __name__=="__main__":
    from example_adventure import *
    import json,os
    os.makedirs('./.tmp/',exist_ok=True)

    open("./.tmp/example_data.json","w").write(json.dumps(this.scenario_data,indent=4))
    print("Scenario data saved to ./tmp/example_data.json")

    text=''
    for dialogues in this.scenario_data['example_dialogues'].values():
        text+=dialogues['name']+"\n"
        text+=convert_history_plain_text(this.scenario_data['opening_dialogue']['content']+dialogues['content'])
        text+="\n\n"
    open("./.tmp/example_dialogue.txt","w").write(text)
    print("Example dialogue saved to ./tmp/example_dialogue.txt")

    history=this.scenario_data['opening_dialogue']['content']

    request=compose_roleplay_request("Captain Galen",this.scenario_data,history)
    open("./.tmp/example_roleplay_request.json","w").write(json.dumps(request,indent=4))
    print("Roleplay request saved to ./tmp/example_roleplay_request.json")

    request=compose_check_outcome_request(this.scenario_data,history)
    open("./.tmp/example_check_outcome_request.json","w").write(json.dumps(request,indent=4))
    print("Check outcome request saved to ./tmp/example_check_outcome_request.json")

    api_key=open("C:\\openai.txt").read()
    url="https://api.openai.com/v1/chat/completions"
    from chatgpt_api import init_chatgpt_api
    init_chatgpt_api(api_key,url,debug_print_request=False,debug_print_response=False)
    example_game_loop(this.scenario_data)