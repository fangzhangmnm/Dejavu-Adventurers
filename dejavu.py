#========== Renpy interface ==========

selected_dialogue = None
selected_character = None
selected_scenario = None
selected_object = None
characters={}
scenarios={}
NARRATOR_NAME="SYSTEM"
ONGOING="ONGOING"

def say(name,content):
    global selected_dialogue
    selected_dialogue.append({"name": str(name), "content": content})

def narrate(content):
    global selected_dialogue
    selected_dialogue.append({"name": NARRATOR_NAME, "content": content})

def character(name):
    global selected_character,selected_object
    selected_object=selected_character=characters.setdefault(name, {
        "name": name, 
        "description": "", 
        "personality": "",
        "example_dialogues": [],
        })
    return _character(name)

def personality(content):
    global selected_character
    selected_character["personality"]=content

def description(content):
    global selected_object
    selected_object["description"]=content

def example_dialogue(name):
    global selected_object,selected_dialogue,selected_scenario
    selected_dialogue=[]
    selected_object={
        "name":name,
        "content": selected_dialogue,
        "outcome": None,
        "comment": None,
        }
    selected_scenario["example_dialogues"].append(selected_object)

def scenario(name):
    global selected_scenario,selected_dialogue,selected_object
    selected_object=selected_scenario=scenarios.setdefault(name, {
        "name": name, 
        "description": "",
        "opening_dialogue": [],
        "example_dialogues": [],
        "outcomes": [],
        })
    selected_dialogue=selected_scenario["opening_dialogue"]
    return selected_object

def outcome(name,condition_or_comment):
    global selected_scenario,selected_object
    if selected_object is selected_scenario:
        selected_scenario["outcomes"].append({
            "name": name,
            "condition": condition_or_comment,
            })
    elif selected_dialogue is selected_object["content"] and selected_object in selected_scenario["example_dialogues"]:
        selected_object["outcome"]=name
        selected_object["comment"]=condition_or_comment
    else: 
        raise Exception("outcome() must be called in scenario() or example_dialogue()")




#========== ChatGPT prompts ==========

from chatgpt_api import completion,purify_label


def convert_history_roleplay_style(character_to_play,history):
    character_to_play=get_character_object(character_to_play)
    request=[]
    for dialogue in history:
        if dialogue["name"]==character_to_play["name"]:
            request.append({"role": "assistant","content": dialogue["content"]})
        else:
            request.append({"role": "user","content": dialogue["name"]+": "+dialogue["content"]})
    return request

def convert_history_plain_text(history):
    text=""
    for dialogue in history:
        text+=dialogue["name"]+": "+dialogue["content"]+"\n"
    return text


def roleplay(character,scenario,history=[]):
    character=get_character_object(character)
    scenario=get_scenario_object(scenario)
    request=[]
    prompt="Write {character_name}'s next reply in a fictional chat. Write 1 reply only in internet RP style, italicize actions, and avoid quotation marks. Use markdown. Be proactive, creative, and drive the plot and conversation forward. Write at least 1 paragraph, up to 4. Always stay in character and avoid repetition. Player's speech does not indicate they have taken the action. You must wait until {NARRATOR_NAME}'s description in order to comfirm whether player had performed their promised action. \n\n{character_description}\n\n{character_name}'s personality: {character_personality}\n\nCircumstances and context of the dialogue: {scenario_description}".format(
        character_name=character["name"],
        character_description=character["description"],
        character_personality=character["personality"],
        scenario_description=scenario["description"],
        NARRATOR_NAME=NARRATOR_NAME,
        )
    request.append({"role": "system", "content": prompt})

    for i,example_dialogue in enumerate(scenario["example_dialogues"]):
        prompt="[Example Dialogue {id}]\ncomment: {comment}".format(id=i,comment=example_dialogue["comment"])
        request.append({"role": "system", "content": prompt})
        request.extend(convert_history_roleplay_style(character["name"],example_dialogue["content"]))
    prompt="[Your Own Dialogue]\ncomment: {comment}".format(comment=scenario["description"])
    request.append({"role": "system", "content": prompt})
    request.extend(convert_history_roleplay_style(character["name"],history))
    prompt="[Write the next reply only as {character_name}]".format(character_name=character["name"])
    request.append({"role": "system", "content": prompt})

    response=completion(request,temperature=0.5)
    content=response[-1]["content"]
    return content

def check_outcome(scenario,history):
    if isinstance(scenario,str):scenario=scenarios[scenario]
    request=[]
    prompt="Please read the dialogue of a role playing game and determine whether the conversation can be continued, or a certain outcome is reached. Player's speech does not indicate they have taken the action. If player need to perform something, you must wait until {NARRATOR_NAME}'s description in order to comfirm whether player had performed their promised action.\n\n".format(
        NARRATOR_NAME=NARRATOR_NAME,
        )
    for i,outcome in enumerate(scenario["outcomes"]):
        prompt+="{id}. if {condition}, then reply \"REASON, {outcome_name}\"\n".format(id=i,condition=outcome["condition"],outcome_name=outcome["name"])
    prompt+="{id}. For most of the cases, the dialogue need to be follow up, please reply \"REASON, {outcome_name}\"\n".format(id=len(scenario["outcomes"]),outcome_name=ONGOING)
    request.append({"role": "system", "content": prompt})

    for i,example_dialogue in enumerate(scenario["example_dialogues"]):
        prompt="[Example Dialogue {id}]\n".format(id=i)
        prompt+=convert_history_plain_text(example_dialogue["content"])
        request.append({"role": "user", "content": prompt})
        assert example_dialogue["outcome"] is not None
        prompt="{REASON}, {outcome_name}".format(outcome_name=example_dialogue["outcome"],REASON=example_dialogue["comment"])
        request.append({"role": "assistant", "content": prompt})

    prompt="[Your Own Dialogue]\n"
    prompt+=convert_history_plain_text(history)
    request.append({"role": "user", "content": prompt})

    response=completion(request,temperature=0)
    response_text=response[-1]["content"]

    target_labels=[outcome["name"] for outcome in scenario["outcomes"]]+[ONGOING]
    outcome=purify_label(response_text,target_labels,default=ONGOING)
    return outcome, response_text



def example_game_loop(player_character,npcs,scenario):
    history=[]
    def print_and_log(name,content):
        print("\033[92m"+name+"\033[0m"+": "+"\033[94m"+content+"\033[0m")
        history.append({"name": name, "content": content})
    for dialogue in scenario["opening_dialogue"]:
        print_and_log(dialogue["name"],dialogue["content"])
    try:
        while True:
            player_input=None
            while player_input is None:
                player_input=input("Your reply: ")
            if player_input=="exit":
                return ONGOING
            elif "\me " in player_input:
                dialogue,action=player_input.split("\me ")
                if len(dialogue.strip())>0:
                    print_and_log(player_character["name"],dialogue)
                if len(action.strip())>0:
                    print_and_log(NARRATOR_NAME,player_character["name"]+" "+action)
            else:
                print_and_log(player_character["name"],player_input)
            for npc in npcs:
                npc_input=roleplay(npc,scenario,history)
                print_and_log(npc["name"],npc_input)
            outcome,outcome_comment=check_outcome(scenario,history)
            # print("\033[91m"+outcome_comment+"\033[0m")
            if outcome!=ONGOING:
                print("\033[91m"+"Outcome: "+outcome+"\033[0m")
                return outcome
    except KeyboardInterrupt:
        return ONGOING

class _character:
    def __init__(self,name):
        self.name=name
    def __call__(self,content):
        say(self.name,content)
    def __getitem__(self,key):
        return characters[self.name][key]
    def __setitem__(self,key,value):
        characters[self.name][key]=value
    def __str__(self):
        return self.name
    
def get_character_object(name_or_object_or_dict):
    if isinstance(name_or_object_or_dict,_character): return name_or_object_or_dict
    if isinstance(name_or_object_or_dict,str): return _character(name_or_object_or_dict)
    if isinstance(name_or_object_or_dict,dict): return _character(name_or_object_or_dict["name"])

def get_scenario_object(name_or_object_or_dict):
    if isinstance(name_or_object_or_dict,str): return scenarios[name_or_object_or_dict]
    if isinstance(name_or_object_or_dict,dict): return name_or_object_or_dict



#========== Example Adventure Book ==========

Guard=character("Captain Galen")
personality("greedy, stubborn, unreasonable, pride, arrogant")
description("Captain Galen is the guard for the city gate. He is supposed to examine the travelers and collect taxes from them. But he is very greedy, and he always tries to find excuses to collect more taxes. He is also very stubborn and unreasonable. He is very proud of his position, and he thinks he is the most powerful person in the city.")

npcs=[Guard]
Player=character("Adventurer")

demo_scenario=scenario("Guard Challenge")
description("The player attempts to enter the city, but being rejected by the city guard. The guard must be unreasonable and is very hard to persuade. The player have to either bribe the guard, use persuasion, intimidation or deception to enter the city, but neither of them is easy.")

outcome("Passed", "The guard allows the player to enter the city.")
outcome("Fight", "The conflict escalates and the guard attacks the player.")
# outcome("Failed", "The conversion is unable to proceed in any means.") # this will cause early termination of the conversation

narrate("The player approaches the city gate, the gate is closed shut. The guard is standing in front of the gate.")
Guard("Halt! State your business and provide your documentation.")

# example_dialogue("An unsuccessful attempt")
# Player("No worries, Captain. We have all the proper documents right here.")
# narrate("Player presents the party's documents to Captain Galen. The documents are signed and stamped by the proper authorities.")
# Guard("*examines the documents* Hmm..., *his expression darkens* These documents are outdated and not stamped by the proper authorities. Entry denied.")
# Player("Captain Galen, please reconsider! We come with urgent news from the nearby village of Glimmerbrook. A horde of undead is preparing to attack Eldoria.")
# Guard("*skeptical* Undead, you say? That's not an excuse to bypass the city's regulations.")
# Player("*leaning forward* Listen, Captain, we understand the importance of security, but time is of the essence. Lives are at stake. Surely, there must be something we can do to gain entry?")
# Guard("*crossing arms* I'm afraid not. Our rules are strict for a reason.")
# outcome(ONGOING,"The player need to further persuade the guard to let them in.")

example_dialogue("A bribe")
Player("No worries, Captain. We have all the proper documents right here.")
narrate("Player presents the party's documents to Captain Galen. The documents are signed and stamped by the proper authorities.")
Guard("*examines the documents* Hmm..., *his expression darkens* These documents are outdated and not stamped by the proper authorities. Entry denied.")
Player("Captain Galen, please reconsider! We come with urgent news from the nearby village of Glimmerbrook. A horde of undead is preparing to attack Eldoria.")
Guard("*skeptical* Undead, you say? That's not an excuse to bypass the city's regulations.")
Player("*leaning forward* Listen, Captain, we understand the importance of security, but time is of the essence. Lives are at stake. Surely, there must be something we can do to gain entry?")
Guard("*crossing arms* I'm afraid not. Our rules are strict for a reason.")
Player("*sincerely* Captain Galen, please. We risked our lives to bring this information. Surely, the safety of the city is worth bending the rules a bit.")
Guard("*stern* Rules are rules. If you can't abide by them, then leave.")
Player("Captain, we understand the importance of your duty. Would a little compensation help you look the other way, just this once?")
narrate("Player offers a pouch of gold to Captain Galen.")
Guard("*hesitates, torn between duty and the gold.* Fine. But this better not come back to haunt me. *reluctantly* You have one day, and then you're out.")
outcome("Passed","Player have a proper document, a convincing reason and have bribed the guard.")

example_dialogue("A failed persuasion which leads to a fight")
Player("*smiling confidently* Greetings, Captain Galen. We come as Emissaries from a distant land, seeking to share tales of adventure and knowledge with the people of Eldoria.")
Guard("*raising an eyebrow* Emissaries, you say? I'm not easily swayed by flowery words. Show me your credentials.")
Player("*enthusiastically* Of course, Captain! We have a letter of recommendation from a respected scholar back in our homeland. He praised our wisdom and contributions to our community.")
narrate("Player presents the letter to Captain Galen.")
narrate("The letter was hastily wrote just a moment ago, and lack of any specific details about the party's supposed achievements.")
Guard("*scans the letter* Hmm..., *displeased* This letter seems dubious at best. I find it hard to believe that a respected scholar would pen such a vague endorsement.")
Player("*nervously* Captain, we are being honest in our intentions. We really do possess valuable knowledge and experiences to share.")
Guard("*frowning* Words are cheap. If you truly have something to offer, then prove it with actions, not empty promises.")
Player("*desperately* Captain, please! We have traveled a long way to reach Eldoria. Surely, you can make an exception for us?")
Guard("Stop wasting my time. If you keep this up, I'll have you arrested for disturbing the peace.")
Player("We mean no harm, Captain. It seems diplomacy has failed us, but we won't back down from our mission. If you won't let us pass peacefully, we'll have no choice but to force our way through!")
Guard("*angered* You dare threaten me in my own city? You'll regret that!")
outcome("Fight","Player stirred the guard after he explicitly threatened the player.")

example_dialogue("Need to pay the bribe") # need to provide more ONGOING examples
Player("Here is the document, sir")
narrate("Player provides the document. The document is well signed.")
Guard("*carefully examining the document* Hmph, this document seems to be in order. However, I'm afraid there's an additional tax you need to pay to enter the city. It's a small fee, of course, for the privilege of experiencing the wonders of Eldoria.")
outcome(ONGOING,"Player need to pay the bribe. Note that at the moment, the player haven't actually paid the bribe yet.")


if __name__=="__main__":
    api_key=open("C:\\openai.txt").read()
    url="https://api.openai.com/v1/chat/completions"
    from chatgpt_api import init_chatgpt_api
    init_chatgpt_api(api_key,url,debug_print_request=False,debug_print_response=False)
    _outcome=example_game_loop(player_character=Player,npcs=npcs,scenario=demo_scenario)