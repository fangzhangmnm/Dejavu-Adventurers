import sys
dejavu_store=sys.modules[__name__]

# ========= States ==========

dejavu_store.scenario_data=None
dejavu_store.current={}
dejavu_store.state="disabled"

from typing import Literal


def get_object(path):
    p=dejavu_store.scenario_data
    for key in path:
        p=p[key]
    return p

def get_scenario_data():
    return dejavu_store.scenario_data

renpy=object()


# ========= DSL =========

NARRATOR_NAME="SYSTEM"
ONGOING_OUTCOME_NAME="ONGOING"
PLAYER_QUIT_OUTCOME_NAME="PLAYER_QUIT"

renpy.NARRATOR_NAME=NARRATOR_NAME
renpy.ONGOING_OUTCOME_NAME=ONGOING_OUTCOME_NAME
renpy.PLAYER_QUIT_OUTCOME_NAME=PLAYER_QUIT_OUTCOME_NAME

def set_state(state:'Literal["disabled", "opening_dialogue","example_dialogue","playing"]'):
    assert state in ["disabled", "opening_dialogue","example_dialogue","playing"]
    dejavu_store.state=state

def write_dialogue(character_name,content,destination=None):
    destination=destination or get_object(dejavu_store.current['dialogue'])['content']
    destination.append({
        'type':'dialogue',
        'character':character_name,
        'content':content,
    })

def character(name,is_player=False):
    dejavu_store.scenario_data['characters'].setdefault(name,{
        'name':name,
        'description':"",
        'personality':"",
    })
    dejavu_store.current['character']=('characters',name)
    if is_player:
        dejavu_store.scenario_data['player_character_name']=name
    else:
        dejavu_store.scenario_data['npc_names'].append(name)
    return lambda content: say(name,content)

def example_narrator(content,history=None):
    history=history or dejavu_store.get_object(dejavu_store.current['dialogue'])['content']
    history.append({
        'type':'narrate',
        'content':content,
    })
renpy.example_narrator=example_narrator

def example_call(outcome_name,comment="",history=None):
    history=history or dejavu_store.get_object(dejavu_store.current['dialogue'])['content']
    history.append({
        'type':'call',
        'outcome_name':outcome_name,
        'comment':comment,
    })
renpy.example_call=example_call

def example_jump(outcome_name,comment=""):
    dialogue=dejavu_store.get_object(dejavu_store.current['dialogue'])
    dialogue['outcome_name']=outcome_name
    dialogue['outcome_comment']=comment
renpy.example_jump=example_jump

def scenario(name):
    dejavu_store.scenario_data={
        'name':name,
        'summary':"",
        'characters':{},
        'outcomes':{},
        'opening_dialogue':None,
        'example_dialogues':{},
        'player_character_name':None,
        'npc_names':[],
    }
renpy.scenario=scenario

def end_scenario():
    dejavu_store.set_state("disabled")
renpy.end_scenario=end_scenario

def summary(content):
    dejavu_store.scenario_data['summary']=content
renpy.summary=summary

def AICharacter(name):
    return character(name,is_player=False)
renpy.AICharacter=AICharacter

def PlayerCharacter(name):
    dejavu_store.scenario_data['player_character_name']=name
    return character(name,is_player=True)
renpy.PlayerCharacter=PlayerCharacter

def description(content):
    character=dejavu_store.get_object(dejavu_store.current['character'])
    character['description']=content
renpy.description=description

def personality(content):   
    character=dejavu_store.get_object(dejavu_store.current['character'])
    character['personality']=content
renpy.personality=personality

def outcome(name,label=None,type='outcome',once=False):
    dejavu_store.scenario_data['outcomes'].setdefault(name,{
        'name':name,
        'label':label or name,
        'condition':"",
        'type':type,
    })
    dejavu_store.current['outcome']=('outcomes',name)
renpy.outcome=outcome

def incident(name,label=None,once=True):
    outcome(name,label,type='incident',once=once)
renpy.incident=incident

def condition(content):
    outcome=dejavu_store.get_object(dejavu_store.current['outcome'])
    outcome['condition']=content
renpy.condition=condition

def opening_dialogue(name='Opening'):
    dejavu_store.scenario_data['opening_dialogue']={
        'name':name,
        'description':"",
        'content':[],
    }
    dejavu_store.current['dialogue']=('opening_dialogue',)
    dejavu_store.set_state("opening_dialogue")
renpy.opening_dialogue=opening_dialogue

def example_dialogue(name):
    dejavu_store.scenario_data['example_dialogues'].setdefault(name,{
        'name':name,
        'description':"",
        'content':[],
        'outcome_name':"",
        'outcome_comment':"",
    })
    dejavu_store.current['dialogue']=('example_dialogues',name)
    dejavu_store.set_state("example_dialogue")
renpy.example_dialogue=example_dialogue

# ========= prompts =========

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

def compose_summary_request(character_name,scenario_data,history):
    prompt="summarize the dialogue in 1 small paragraph from {character_name}'s perspective.\n{character_name}'s personality: {character_personality}\nPlease stay in the character, as that character is writing a diary. Only contain the main text, not the heading and signature.".format(
        character_name=character_name,
        character_personality=scenario_data["characters"][character_name]['personality'],
    )
    request=[{"role": "system", "content": prompt}]
    prompt=convert_history_plain_text(history)
    request.append({"role": "user", "content": prompt})
    return request


# ========= example llm calls =========


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

def perform_summary_query(character_name,scenario,history):
    try:
        from .chatgpt_api import completion
    except ImportError:
        from chatgpt_api import completion
    request=compose_summary_request(character_name,scenario,history)
    response=completion(request,temperature=0)
    summary=response[-1]["content"]
    summary=summary.replace("\n"," ")
    return summary

# ========= example game loop =========

    
def print_dialogue(character_name,content,interact=True):
    if character_name==NARRATOR_NAME:
        print("\033[90m"+content+"\033[0m")
    else:
        print("\033[92m"+character_name+"\033[0m"+": "+"\033[94m"+content+"\033[0m")
    # if interact: input("Press Enter to continue...")

def say(character_name,content):
    if dejavu_store.state=="opening_dialogue":
        print_dialogue(character_name,content,interact=True)
        write_dialogue(character_name,content)
    elif dejavu_store.state=="example_dialogue":
        write_dialogue(character_name,content)
    elif dejavu_store.state=="playing":
        write_dialogue(character_name,content,destination=dejavu_store.history)
        print_dialogue(character_name,content,interact=False)



def ai_conversation_loop(history):
    try:
        dejavu_store.history=history
        dejavu_store.removed_incidents=[]
        dejavu_store.set_state("playing")
        dejavu_store.outcome=ONGOING_OUTCOME_NAME
        player_character_name=dejavu_store.scenario_data['player_character_name']
        npc_names=dejavu_store.scenario_data['npc_names']
        while True:
            # player dialogue
            player_input=input("Your reply: ")
            if len(player_input.strip())>0:
                if player_input.lower() in ["quit","exit"]:
                    dejavu_store.outcome=PLAYER_QUIT_OUTCOME_NAME
                    break
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
            # npc dialogue
            dejavu_store.iNPC=0
            while dejavu_store.iNPC<len(npc_names):
                npc_name=npc_names[dejavu_store.iNPC]
                dejavu_store.iNPC+=1
                npc_input=perform_roleplay_query(npc_name,dejavu_store.scenario_data,dejavu_store.history)
                say(npc_name,npc_input)

            # check outcome
            outcome_name,outcome_type,outcome_comment=perform_check_outcome_query(dejavu_store.scenario_data,dejavu_store.history,removed_incidents=dejavu_store.removed_incidents)
            print("\033[90m"+outcome_comment+"\033[0m")
            if outcome_type=="incident":
                dejavu_store.removed_incidents.append(outcome_name)
                print("\033[91m"+"Incident: "+outcome_name+"\033[0m")
                gm_input=input("GM: ")
                say(NARRATOR_NAME,gm_input)
            elif outcome_type=="outcome":
                print("\033[91m"+"Outcome: "+outcome_name+"\033[0m")
                dejavu_store.outcome=outcome_name
                break
            else: #"ongoing"
                continue
    except KeyboardInterrupt:
        dejavu_store.outcome=PLAYER_QUIT_OUTCOME_NAME
    finally:
        dejavu_store.set_state("disabled")
    dejavu_store.npc_memory=[]
    for npc_name in npc_names:
        summary=perform_summary_query(npc_name,dejavu_store.scenario_data,dejavu_store.history)
        dejavu_store.npc_memory.append({"character_name":npc_name,"dialogue_summary":summary})
        print("\033[90m"+npc_name+"'s summary: "+summary+"\033[0m")
    


if __name__=="__main__":
    from example_adventure import *
    import json,os
    os.makedirs('./.tmp/',exist_ok=True)

    open("./.tmp/example_data.json","w").write(json.dumps(dejavu_store.scenario_data,indent=4))
    print("Scenario data saved to ./tmp/example_data.json")
    open("./.tmp/example_dialogue.txt","w").write('\n\n'.join([dialogues['name']+"\n"+convert_history_plain_text(dejavu_store.scenario_data['opening_dialogue']['content']+dialogues['content']) for dialogues in dejavu_store.scenario_data['example_dialogues'].values()]))
    print("Example dialogue saved to ./tmp/example_dialogue.txt")

    request=compose_roleplay_request("Captain Galen",dejavu_store.scenario_data,dejavu_store.scenario_data['opening_dialogue']['content'])
    open("./.tmp/example_roleplay_request.json","w").write(json.dumps(request,indent=4))
    print("Roleplay request saved to ./tmp/example_roleplay_request.json")

    request=compose_check_outcome_request(dejavu_store.scenario_data,dejavu_store.scenario_data['opening_dialogue']['content'])
    open("./.tmp/example_check_outcome_request.json","w").write(json.dumps(request,indent=4))
    print("Check outcome request saved to ./tmp/example_check_outcome_request.json")

    api_key=open("C:\\openai.txt").read()
    url="https://api.openai.com/v1/chat/completions"
    from chatgpt_api import init_chatgpt_api
    init_chatgpt_api(api_key,url,debug_print_request=False,debug_print_response=False)


    history=list(dejavu_store.scenario_data['opening_dialogue']['content'])
    ai_conversation_loop(history)