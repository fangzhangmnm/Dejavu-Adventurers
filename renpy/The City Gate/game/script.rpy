define Galen = Character("Captain Galen")
define Player = Character("Player")

$ gui.text_size = 24
    
init python:
    from dejavu import init_chatgpt_api,completion
    import dejavu

    api_key=open("C:\\openai.txt").read()
    proxy="https://api.openai.com/v1/chat/completions"
    init_chatgpt_api(api_key=api_key, proxy=proxy)
    config.log="debug_log.txt"

    def history_narrator(content,slience=False,**kwargs):
        history.append({"type": "narrate", "content": content})
        if not slience:
            narrator(content,**kwargs)

    def log_object(obj):
        import json
        text=json.dumps(obj,indent=4,default=lambda o: '<not serializable>').replace("\n","<br>")
        for line in text.split("<br>"):
            renpy.log(line)



label ai_dialogue_loop:
    python:
        player_character_name=dejavu.get_player_character_name()
        scenario=dejavu.get_scenario_data()
        npc_names=dejavu.get_npc_names()
        history=scenario['opening_dialogue']['content'].copy()
        removed_incidents=[]
        Player=dejavu.get_character_payload(player_character_name)
        renpy.log("Compiled scenario:")
        log_object(scenario)

    $ outcome=dejavu.ONGOING_OUTCOME_NAME
    $ next_NPC_index=0
    $ outcome_type="ongoing"
    $ skip_next_player_input=False

    while True:
        if not skip_next_player_input:
            $ user_input = renpy.input("What do you say ?", length=1000)
            $ renpy.fix_rollback()
            Player "[user_input]" (interact=False)
        python:
            if not skip_next_player_input:
                history.append({"type": "dialogue", "character": player_character_name, "content": user_input})
            npc_name=npc_names[next_NPC_index]
            npc=dejavu.get_character_payload(npc_name)
            cached_response=renpy.roll_forward_info()
            renpy.log("retreived roll forward info: "+str(cached_response))
            if cached_response is None:
                renpy.log("Current History:")
                log_object(history)
                renpy.log("Sending roleplay query")
                ai_reply=dejavu.perform_roleplay_query(npc_name,scenario,history)
                renpy.log("Performed roleplay query: "+ai_reply)
                history.append({"type": "dialogue", "character": npc_name, "content": ai_reply})
                renpy.log("Sending check outcome query")
                outcome_name,outcome_type,outcome_comment=dejavu.perform_check_outcome_query(scenario,history,removed_incidents=removed_incidents)
                renpy.log("Performed check outcome query: "+outcome_comment)
                cached_response=(ai_reply,outcome_name,outcome_type,outcome_comment)
            renpy.checkpoint(data=cached_response,hard=False)
        $ ai_reply,outcome_name,outcome_type,outcome_comment=cached_response
        $ history=list(history) # not sure if it is necessary for renpy to detect the change

        npc "[ai_reply]"

        $ skip_next_player_input=False
        if outcome_type=="incident":
            $ removed_incidents.append(outcome_name)
            call expression dejavu.get_outcome_label(outcome_name)
            $ skip_next_player_input=True
        elif outcome_type=="outcome":
            jump expression dejavu.get_outcome_label(outcome_name)
        else: #ongoing
            $ next_NPC_index=(next_NPC_index+1)%len(npc_names)


    $ assert False

    
    # while True:
    #     $ user_input = renpy.input("What do you say ?", length=1000)
    #     $ renpy.fix_rollback()
    #     Player "[user_input]" (interact=False)
    #     $ messages.append({"role": "user", "content": user_input})
    #     python:
    #         ai_reply=renpy.roll_forward_info() or completion(messages)[-1]["content"]
    #         renpy.checkpoint(data=ai_reply,hard=False)
    #     e "[ai_reply]"
    #     $ messages.append({"role": "assistant", "content": ai_reply})




label city_gate:
    scene city gate
    with fade

    define Guard = Character("Captain Galen")
    define Player = Character("Player")
    narrator "The player approaches the city gate, the gate is closed shut. The guard is standing in front of the gate."

    show captain galen at right
    with dissolve

    Guard "Halt! State your business and provide your documentation."

    dejavu.scenario "Guard Challenge"
    dejavu.summary "The player attempts to enter the city, but being rejected by the city guard. The guard must be unreasonable and is very hard to persuade. The player have to either bribe the guard, use persuasion, intimidation or deception to enter the city, but neither of them is easy."
    
    $Guard=dejavu.character("Captain Galen",payload=Guard)
    dejavu.personality "greedy, stubborn, unreasonable, prideful, arrogant"
    dejavu.description "Captain Galen is the guard for the city gate. He is supposed to examine the travelers and collect taxes from them. But he is very greedy, and he always tries to find excuses to collect more taxes. He is also very stubborn and unreasonable. He is very proud of his position, and he thinks he is the most powerful person in the city."

    $Player=dejavu.character("Adventurer",is_player=True,payload=Player)
    
    dejavu.outcome "Passed" (label="city_gate.passed")
    dejavu.condition "The guard allows the player to enter the city."

    dejavu.outcome "Fight" (label="city_gate.fight")
    dejavu.condition "The conflict escalates and the guard attacks the player."

    dejavu.incident "Examine Documents" (label="city_gate.examine_documents")
    dejavu.condition "The guard want to examine the player's documents."

    dejavu.incident "Take Item" (label="city_gate.take_item",once=False)
    dejavu.condition "The player gives the guard some items."

    dejavu.opening_dialogue ""
    dejavu.narrator "The player approaches the city gate, the gate is closed shut. The guard is standing in front of the gate."
    Guard "Halt! State your business and provide your documentation."

    # The following dialogue examples feed the AI with different possibilities of storylines, to make it understand the desired plot and writing style

    dejavu.example_dialogue "A bribe"
    Player "No worries, Captain. Here is the document"
    Guard "Give me the document. *impatiently* I don't have all day."
    dejavu.call "Examine Documents" ("Player claims to have a proper document.") # Here AI will learn to ask the game engine to provide information about the document
    dejavu.narrator "Player presents the party's documents to Captain Galen. The documents are signed and stamped by the proper authorities."
    Guard "*examines the documents* Hmm... *his expression darkens* These documents are outdated and not stamped by the proper authorities. Entry denied."
    Player "Captain Galen, please reconsider! We come with urgent news from the nearby village of Glimmerbrook. A horde of undead is preparing to attack Eldoria."
    Guard "*skeptical* Undead, you say? That's not an excuse to bypass the city's regulations."
    Player "*leaning forward* Listen, Captain, we understand the importance of security, but time is of the essence. Lives are at stake. Surely, there must be something we can do to gain entry?"
    Guard "*crossing arms* I'm afraid not. Our rules are strict for a reason."
    Player "*sincerely* Captain Galen, please. We risked our lives to bring this information. Surely, the safety of the city is worth bending the rules a bit."
    Guard "*stern* Rules are rules. If you can't abide by them, then leave."
    Player "Captain, we understand the importance of your duty. Would a little compensation help you look the other way, just this once?"
    Guard "*raised eyebrow* Hugh? What are you implying?"
    dejavu.call "Take Item" ("player agrees to bribe the guard.")
    dejavu.narrator "Player offers a pouch of gold to Captain Galen."
    Guard "*hesitates, torn between duty and the gold.* Fine. But this better not come back to haunt me. *reluctantly* You have one day, and then you're out."
    dejavu.jump "Passed" ("Player have a proper document, a convincing reason and have bribed the guard.") # AI will determine which outcome the player achieved!

    dejavu.example_dialogue "A failed persuasion which leads to a fight"
    Player "*smiling confidently* Greetings, Captain Galen. We come as Emissaries from a distant land, seeking to share tales of adventure and knowledge with the people of Eldoria."
    Guard "*raising an eyebrow* Emissaries, you say? I'm not easily swayed by flowery words. Show me your credentials."
    Player "*enthusiastically* Of course, Captain! We have a letter of recommendation from a respected scholar back in our homeland. He praised our wisdom and contributions to our community."
    Guard "Give me the letter. *impatiently* I don't have all day."
    dejavu.call "Examine Documents" ("Player claims to have a letter of recommendation.")
    dejavu.narrator "Player presents the letter to Captain Galen."
    dejavu.narrator "The letter was hastily wrote just a moment ago, and lack of any specific details about the party's supposed achievements."
    Guard "*scans the letter* Hmm...*displeased* This letter seems dubious at best. I find it hard to believe that a respected scholar would pen such a vague endorsement."
    Player "*nervously* Captain, we are being honest in our intentions. We really do possess valuable knowledge and experiences to share."
    Guard "*frowning* Words are cheap. If you truly have something to offer, then prove it with actions, not empty promises."
    Player "*desperately* Captain, please! We have traveled a long way to reach Eldoria. Surely, you can make an exception for us?"
    Guard "Stop wasting my time. If you keep this up, I'll have you arrested for disturbing the peace."
    Player "We mean no harm, Captain. It seems diplomacy has failed us, but we won't back down from our mission. If you won't let us pass peacefully, we'll have no choice but to force our way through!"
    Guard "*angered* You dare threaten me in my own city? You'll regret that!"
    dejavu.jump "Fight" ("Player stirred the guard after he explicitly threatened the player.")

    call ai_dialogue_loop from city_gate_1

    return 

label .fight:
    "You end up fighting the guard."
    "Bad Ending"
    return

label .passed:
    "You successfully enter the city."
    "Good Ending"
    return

label .examine_documents:
    history_narrator "The guard examines Adventurer's documents."
    $description=renpy.input("(debug only) What is the description of the document?",length=1000)
    history_narrator "[description]" (slience=True)
    return

label .take_item:
    $item=renpy.input("(debug only) What item do you want to give? \"no\" for not giving anything",length=1000) # We need to check player's inventory in actual game!
    if item=="no":
        history_narrator "Adventurer refuses to give the item" # The Guard will get mad at that.
    else:
        history_narrator "Adventurer gives [item] to the guard"
        "You lose [item]!"
        # player.item--
    return

    

label start:
    jump city_gate

    # define e = Character("Eileen")
    # define Player=Character("Player")

    
    # python:
    #     messages=[
    #         {"role": "system", "content": "You are Eileen, a tennage student enrolled at Miskatonic Univeristy of Arkham. You are secretly in love with the user. You laugh very frequently and finish your sentences with 'Hihihi'"},
    #         {"role": "assistant", "content": "Hello there, my name is Eileen, I am so happy to see you ! Hihihi"}
    #     ]

    # e "Hello there, my name is Eileen, I am so happy to see you ! Hihihi"

    # while True:
    #     $ user_input = renpy.input("What do you say ?", length=1000)
    #     $ renpy.fix_rollback()
    #     Player "[user_input]" (interact=False)
    #     $ messages.append({"role": "user", "content": user_input})
    #     python:
    #         ai_reply=renpy.roll_forward_info() or completion(messages)[-1]["content"]
    #         renpy.checkpoint(data=ai_reply,hard=False)
    #     e "[ai_reply]"
    #     $ messages.append({"role": "assistant", "content": ai_reply})

    # return

# label city_gate_old:

#     scene city gate
#     with fade

#     narrator "The player approaches the city gate, the gate is closed shut. The guard is standing in front of the gate."

#     show captain galen at right
#     with dissolve

#     Galen "Halt! State your business and provide your documentation."

#     Player "No worries, Captain. We have all the proper documents right here."
#     narrator "Player presents the party's documents to Captain Galen. The documents are signed and stamped by the proper authorities."
#     Galen "*examines the documents* Hmm..., *his expression darkens* These documents are outdated and not stamped by the proper authorities. Entry denied."
#     Player "Captain Galen, please reconsider! We come with urgent news from the nearby village of Glimmerbrook. A horde of undead is preparing to attack Eldoria."
#     Galen "*skeptical* Undead, you say? That's not an excuse to bypass the city's regulations."
#     Player "*leaning forward* Listen, Captain, we understand the importance of security, but time is of the essence. Lives are at stake. Surely, there must be something we can do to gain entry?"
#     Galen "*crossing arms* I'm afraid not. Our rules are strict for a reason."
#     Player "*sincerely* Captain Galen, please. We risked our lives to bring this information. Surely, the safety of the city is worth bending the rules a bit."
#     Galen "*stern* Rules are rules. If you can't abide by them, then leave."
#     Player "Captain, we understand the importance of your duty. Would a little compensation help you look the other way, just this once?"
#     narrator "Player offers a pouch of gold to Captain Galen."
#     Galen "*hesitates, torn between duty and the gold.* Fine. But this better not come back to haunt me. *reluctantly* You have one day, and then you're out."

#     jump passed
# label passed:
#     narrator "The party enters the city."
#     narrator "success ending"
#     return