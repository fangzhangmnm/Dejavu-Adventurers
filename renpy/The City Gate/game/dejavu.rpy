init -1 python:
    from dejavu import init_chatgpt_api,completion
    import dejavu

    dejavu.init_chatgpt_api(api_key=open("C:\\openai.txt").read(), proxy="https://api.openai.com/v1/chat/completions")
    
    dejavu.store={'key':'value'}

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