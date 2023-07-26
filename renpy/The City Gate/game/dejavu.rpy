init offset=-100

default dejavu_store.scenario_data=None
default dejavu_store.current={}
default dejavu_store.state="disabled"
default dejavu_store.character_objects={}
default dejavu_narrator=dejavu_character(NARRATOR_NAME)


init python hide:
    import dejavu as api
    dejavu_store.api=api

    dejavu_store.api.init_chatgpt_api(api_key=open("C:\\openai.txt").read(), proxy="https://api.openai.com/v1/chat/completions")



    def get_object(path):
        p=dejavu_store.scenario_data
        for key in path:
            p=p[key]
        return p
    dejavu_store.get_object=get_object

    def set_state(state:'Literal["disabled", "opening_dialogue","example_dialogue","playing"]'):
        assert state in ["disabled", "opening_dialogue","example_dialogue","playing"]
        dejavu_store.state=state
    dejavu_store.set_state=set_state

    def write_dialogue(character_name,content,destination=None):
        destination=destination or dejavu_store.get_object(dejavu_store.current['dialogue'])['content']
        if character_name==NARRATOR_NAME:
            destination.append({
                'type':'narrate',
                'content':content,
            })
        else:
            destination.append({
                'type':'dialogue',
                'character':character_name,
                'content':content,
            })
    dejavu_store.write_dialogue=write_dialogue

    class DejavuCharacter:
        def __init__(self,name,*args,**kwargs):
            self.name=name
            self.renpy_character=Character(name,*args,**kwargs)
            dejavu_store.character_objects[name]=self
        def __call__(self,what,*args,**kwargs):
            if dejavu_store.state=="opening_dialogue":
                dejavu_store.write_dialogue(self.name,what)
                self.renpy_character(what,*args,**kwargs)
            elif dejavu_store.state=="example_dialogue":
                dejavu_store.write_dialogue(self.name,what)
            elif dejavu_store.state=="playing":
                dejavu_store.write_dialogue(self.name,what,destination=dejavu_store.history)
                self.renpy_character(what,*args,**kwargs)
    dejavu_store.DejavuCharacter=DejavuCharacter


init python:
    NARRATOR_NAME="SYSTEM"
    ONGOING_OUTCOME_NAME="ONGOING"
    PLAYER_QUIT_OUTCOME_NAME="PLAYER_QUIT"

    def log_object(obj):
        import json
        text=json.dumps(obj,indent=4,default=lambda o: '<not serializable>')
        for line in text.split("\n"):
            renpy.log(line)

    def dejavu_character(name,is_player=False,*args,**kwargs):
        if name!=NARRATOR_NAME:
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
        return dejavu_store.DejavuCharacter(name,*args,**kwargs)

    

    def dejavu_call(outcome_name,comment="",history=None,*args,**kwargs):
        history=history or dejavu_store.get_object(dejavu_store.current['dialogue'])['content']
        history.append({
            'type':'call',
            'outcome_name':outcome_name,
            'comment':comment,
        })

    def dejavu_jump(outcome_name,comment="",*args,**kwargs):
        dialogue=dejavu_store.get_object(dejavu_store.current['dialogue'])
        dialogue['outcome_name']=outcome_name
        dialogue['outcome_comment']=comment

    def scenario(name,*args,**kwargs):
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

    def end_scenario(what="",*args,**kwargs):
        dejavu_store.set_state("disabled")

    def summary(content,*args,**kwargs):
        dejavu_store.scenario_data['summary']=content

    def AICharacter(name,*args,**kwargs):
        return dejavu_character(name,is_player=False,*args,**kwargs)

    def PlayerCharacter(name,*args,**kwargs):
        dejavu_store.scenario_data['player_character_name']=name
        return dejavu_character(name,is_player=True,*args,**kwargs)

    def description(content,*args,**kwargs):
        character=dejavu_store.get_object(dejavu_store.current['character'])
        character['description']=content

    def personality(content,*args,**kwargs):   
        character=dejavu_store.get_object(dejavu_store.current['character'])
        character['personality']=content

    def outcome(name,label=None,type='outcome',once=False,*args,**kwargs):
        dejavu_store.scenario_data['outcomes'].setdefault(name,{
            'name':name,
            'label':label or name,
            'condition':"",
            'type':type,
        })
        dejavu_store.current['outcome']=('outcomes',name)

    def incident(name,label=None,once=True,*args,**kwargs):
        outcome(name,label,type='incident',once=once)

    def condition(content,*args,**kwargs):
        outcome=dejavu_store.get_object(dejavu_store.current['outcome'])
        outcome['condition']=content

    def opening_dialogue(name='Opening',*args,**kwargs):
        dejavu_store.scenario_data['opening_dialogue']={
            'name':name,
            'description':"",
            'content':[],
        }
        dejavu_store.current['dialogue']=('opening_dialogue',)
        dejavu_store.set_state("opening_dialogue")

    def example_dialogue(name,*args,**kwargs):
        dejavu_store.scenario_data['example_dialogues'].setdefault(name,{
            'name':name,
            'description':"",
            'content':[],
            'outcome_name':"",
            'outcome_comment':"",
        })
        dejavu_store.current['dialogue']=('example_dialogues',name)
        dejavu_store.set_state("example_dialogue")

label dejavu_dialogue_loop:
    python:
        dejavu_store.history=list(dejavu_store.scenario_data['opening_dialogue']['content'])
        dejavu_store.removed_incidents=[]
        dejavu_store.set_state("playing")
        dejavu_store.outcome=ONGOING_OUTCOME_NAME
        dejavu_store.player_character_name=dejavu_store.scenario_data['player_character_name']
        dejavu_store.npc_names=dejavu_store.scenario_data['npc_names']
        renpy.log("Compiled scenario:")
        log_object(dejavu_store.scenario_data)
    while True:
        # player input
        $ dejavu_store.user_input = renpy.input("What do you say ?", length=1000) # need to put in separate statement to make fix_rollback work
        $ renpy.fix_rollback()
        if dejavu_store.user_input.lower() in ["quit","exit"]:
            $ dejavu_store.outcome=PLAYER_QUIT_OUTCOME_NAME
            call dejavu_dialogue_loop_finally_block from dejavu_dialogue_loop_label_1
            return
        if len(dejavu_store.user_input)>0:
            $ dejavu_store.Player=dejavu_store.character_objects[dejavu_store.player_character_name]
            $ dejavu_store.Player(dejavu_store.user_input,interact=False)
        # npc dialogue
        $ dejavu_store.iNPC=0
        while dejavu_store.iNPC<len(dejavu_store.npc_names):
            python:
                dejavu_store.NPC=dejavu_store.character_objects[dejavu_store.npc_names[dejavu_store.iNPC]]
                dejavu_store.npc_name=dejavu_store.npc_names[dejavu_store.iNPC]
                dejavu_store.iNPC+=1
                dejavu_store.ai_reply=renpy.roll_forward_info()
                if dejavu_store.ai_reply is None:
                    dejavu_store.ai_reply=dejavu_store.api.perform_roleplay_query(dejavu_store.npc_name,dejavu_store.scenario_data,dejavu_store.history)
                renpy.checkpoint(data=dejavu_store.ai_reply,hard=False)
            $ dejavu_store.NPC(dejavu_store.ai_reply)

    $ assert False
        
label dejavu_dialogue_loop_finally_block:
    dejavu_store.set_state("disabled")
    return


# def ai_conversation_loop(history):
#     try:
#         dejavu_store.history=history
#         dejavu_store.removed_incidents=[]
#         dejavu_store.set_state("playing")
#         dejavu_store.outcome=ONGOING_OUTCOME_NAME
#         player_character_name=dejavu_store.scenario_data['player_character_name']
#         npc_names=dejavu_store.scenario_data['npc_names']
#         while True:
#             # player dialogue
#             player_input=input("Your reply: ")
#             if len(player_input.strip())>0:
#                 if player_input.lower() in ["quit","exit"]:
#                     dejavu_store.outcome=PLAYER_QUIT_OUTCOME_NAME
#                     break
#                 elif "\me " in player_input:
#                     dialogue,action=player_input.split("\me ")
#                     if len(dialogue.strip())>0:
#                         say(player_character_name,dialogue)
#                     if len(action.strip())>0:
#                         say(NARRATOR_NAME,player_character_name+" "+action)
#                 elif player_input.startswith("\gm "):
#                     say(NARRATOR_NAME,player_input[4:])
#                 else:
#                     say(player_character_name,player_input)
#             # npc dialogue
#             dejavu_store.iNPC=0
#             while dejavu_store.iNPC<len(npc_names):
#                 npc_name=npc_names[dejavu_store.iNPC]
#                 dejavu_store.iNPC+=1
#                 npc_input=perform_roleplay_query(npc_name,dejavu_store.scenario_data,dejavu_store.history)
#                 say(npc_name,npc_input)

#             # check outcome
#             outcome_name,outcome_type,outcome_comment=perform_check_outcome_query(dejavu_store.scenario_data,dejavu_store.history,removed_incidents=dejavu_store.removed_incidents)
#             print("\033[90m"+outcome_comment+"\033[0m")
#             if outcome_type=="incident":
#                 dejavu_store.removed_incidents.append(outcome_name)
#                 print("\033[91m"+"Incident: "+outcome_name+"\033[0m")
#                 gm_input=input("GM: ")
#                 say(NARRATOR_NAME,gm_input)
#             elif outcome_type=="outcome":
#                 print("\033[91m"+"Outcome: "+outcome_name+"\033[0m")
#                 dejavu_store.outcome=outcome_name
#                 break
#             else: #"ongoing"
#                 continue
#     except KeyboardInterrupt:
#         dejavu_store.outcome=PLAYER_QUIT_OUTCOME_NAME
#     finally:
#         dejavu_store.set_state("disabled")
#     dejavu_store.npc_memory=[]
#     for npc_name in npc_names:
#         summary=perform_summary_query(npc_name,dejavu_store.scenario_data,dejavu_store.history)
#         dejavu_store.npc_memory.append({"character_name":npc_name,"dialogue_summary":summary})
#         print("\033[90m"+npc_name+"'s summary: "+summary+"\033[0m")

#     $ outcome=dejavu.ONGOING_OUTCOME_NAME
#     $ next_NPC_index=0
#     $ outcome_type="ongoing"
#     $ skip_next_player_input=False

#     while True:
#         if not skip_next_player_input:
#             $ user_input = renpy.input("What do you say ?", length=1000)
#             $ renpy.fix_rollback()
#             Player "[user_input]" (interact=False)
#         python:
#             if not skip_next_player_input:
#                 history.append({"type": "dialogue", "character": player_character_name, "content": user_input})
#             npc_name=npc_names[next_NPC_index]
#             npc=dejavu.get_character_payload(npc_name)
#             cached_response=renpy.roll_forward_info()
#             renpy.log("retreived roll forward info: "+str(cached_response))
#             if cached_response is None:
#                 renpy.log("Current History:")
#                 log_object(history)
#                 renpy.log("Sending roleplay query")
#                 ai_reply=dejavu.perform_roleplay_query(npc_name,scenario,history)
#                 renpy.log("Performed roleplay query: "+ai_reply)
#                 history.append({"type": "dialogue", "character": npc_name, "content": ai_reply})
#                 renpy.log("Sending check outcome query")
#                 outcome_name,outcome_type,outcome_comment=dejavu.perform_check_outcome_query(scenario,history,removed_incidents=removed_incidents)
#                 renpy.log("Performed check outcome query: "+outcome_comment)
#                 cached_response=(ai_reply,outcome_name,outcome_type,outcome_comment)
#             renpy.checkpoint(data=cached_response,hard=False)
#         $ ai_reply,outcome_name,outcome_type,outcome_comment=cached_response
#         $ history=list(history) # not sure if it is necessary for renpy to detect the change

#         npc "[ai_reply]"

#         $ skip_next_player_input=False
#         if outcome_type=="incident":
#             $ removed_incidents.append(outcome_name)
#             call expression dejavu.get_outcome_label(outcome_name)
#             $ skip_next_player_input=True
#         elif outcome_type=="outcome":
#             jump expression dejavu.get_outcome_label(outcome_name)
#         else: #ongoing
#             $ next_NPC_index=(next_NPC_index+1)%len(npc_names)
#     $ assert False










# init -1 python:
#     from dejavu import init_chatgpt_api,completion
#     import dejavu

#     dejavu.init_chatgpt_api(api_key=open("C:\\openai.txt").read(), proxy="https://api.openai.com/v1/chat/completions")
    
#     # def history_narrator(content,slience=False,**kwargs):
#     #     history.append({"type": "narrate", "content": content})
#     #     if not slience:
#     #         narrator(content,**kwargs)

#     # def log_object(obj):
#     #     import json
#     #     text=json.dumps(obj,indent=4,default=lambda o: '<not serializable>').replace("\n","<br>")
#     #     for line in text.split("<br>"):
#     #         renpy.log(line)



#     def say(who,what,*args,**kwargs):
#         if dejavu.write_to_history:
#             dejavu.history


#         if dejavu.write_to_renpy:
#             renpy.say(who,what,*args,**kwargs)

#     def AICharacter(name, **kwargs):
#         return Character(name, what_do_you_say=AIWhatDoYouSay(), **kwargs)

    


            

# label ai_dialogue_loop:
#     python:
#         player_character_name=dejavu.get_player_character_name()
#         scenario=dejavu.get_scenario_data()
#         npc_names=dejavu.get_npc_names()
#         history=scenario['opening_dialogue']['content'].copy()
#         removed_incidents=[]
#         Player=dejavu.get_character_payload(player_character_name)
#         renpy.log("Compiled scenario:")
#         log_object(scenario)

#     $ outcome=dejavu.ONGOING_OUTCOME_NAME
#     $ next_NPC_index=0
#     $ outcome_type="ongoing"
#     $ skip_next_player_input=False

#     while True:
#         if not skip_next_player_input:
#             $ user_input = renpy.input("What do you say ?", length=1000)
#             $ renpy.fix_rollback()
#             Player "[user_input]" (interact=False)
#         python:
#             if not skip_next_player_input:
#                 history.append({"type": "dialogue", "character": player_character_name, "content": user_input})
#             npc_name=npc_names[next_NPC_index]
#             npc=dejavu.get_character_payload(npc_name)
#             cached_response=renpy.roll_forward_info()
#             renpy.log("retreived roll forward info: "+str(cached_response))
#             if cached_response is None:
#                 renpy.log("Current History:")
#                 log_object(history)
#                 renpy.log("Sending roleplay query")
#                 ai_reply=dejavu.perform_roleplay_query(npc_name,scenario,history)
#                 renpy.log("Performed roleplay query: "+ai_reply)
#                 history.append({"type": "dialogue", "character": npc_name, "content": ai_reply})
#                 renpy.log("Sending check outcome query")
#                 outcome_name,outcome_type,outcome_comment=dejavu.perform_check_outcome_query(scenario,history,removed_incidents=removed_incidents)
#                 renpy.log("Performed check outcome query: "+outcome_comment)
#                 cached_response=(ai_reply,outcome_name,outcome_type,outcome_comment)
#             renpy.checkpoint(data=cached_response,hard=False)
#         $ ai_reply,outcome_name,outcome_type,outcome_comment=cached_response
#         $ history=list(history) # not sure if it is necessary for renpy to detect the change

#         npc "[ai_reply]"

#         $ skip_next_player_input=False
#         if outcome_type=="incident":
#             $ removed_incidents.append(outcome_name)
#             call expression dejavu.get_outcome_label(outcome_name)
#             $ skip_next_player_input=True
#         elif outcome_type=="outcome":
#             jump expression dejavu.get_outcome_label(outcome_name)
#         else: #ongoing
#             $ next_NPC_index=(next_NPC_index+1)%len(npc_names)
#     $ assert False



# label ai_dialogue_loop:
#     python:
#         player_character_name=dejavu.get_player_character_name()
#         scenario=dejavu.get_scenario_data()
#         npc_names=dejavu.get_npc_names()
#         history=scenario['opening_dialogue']['content'].copy()
#         removed_incidents=[]
#         Player=dejavu.get_character_payload(player_character_name)
#         renpy.log("Compiled scenario:")
#         log_object(scenario)

#     $ outcome=dejavu.ONGOING_OUTCOME_NAME
#     $ next_NPC_index=0
#     $ outcome_type="ongoing"
#     $ skip_next_player_input=False

#     while True:
#         if not skip_next_player_input:
#             $ user_input = renpy.input("What do you say ?", length=1000)
#             $ renpy.fix_rollback()
#             Player "[user_input]" (interact=False)
#         python:
#             if not skip_next_player_input:
#                 history.append({"type": "dialogue", "character": player_character_name, "content": user_input})
#             npc_name=npc_names[next_NPC_index]
#             npc=dejavu.get_character_payload(npc_name)
#             cached_response=renpy.roll_forward_info()
#             renpy.log("retreived roll forward info: "+str(cached_response))
#             if cached_response is None:
#                 renpy.log("Current History:")
#                 log_object(history)
#                 renpy.log("Sending roleplay query")
#                 ai_reply=dejavu.perform_roleplay_query(npc_name,scenario,history)
#                 renpy.log("Performed roleplay query: "+ai_reply)
#                 history.append({"type": "dialogue", "character": npc_name, "content": ai_reply})
#                 renpy.log("Sending check outcome query")
#                 outcome_name,outcome_type,outcome_comment=dejavu.perform_check_outcome_query(scenario,history,removed_incidents=removed_incidents)
#                 renpy.log("Performed check outcome query: "+outcome_comment)
#                 cached_response=(ai_reply,outcome_name,outcome_type,outcome_comment)
#             renpy.checkpoint(data=cached_response,hard=False)
#         $ ai_reply,outcome_name,outcome_type,outcome_comment=cached_response
#         $ history=list(history) # not sure if it is necessary for renpy to detect the change

#         npc "[ai_reply]"

#         $ skip_next_player_input=False
#         if outcome_type=="incident":
#             $ removed_incidents.append(outcome_name)
#             call expression dejavu.get_outcome_label(outcome_name)
#             $ skip_next_player_input=True
#         elif outcome_type=="outcome":
#             jump expression dejavu.get_outcome_label(outcome_name)
#         else: #ongoing
#             $ next_NPC_index=(next_NPC_index+1)%len(npc_names)


#     $ assert False

    
#     # while True:
#     #     $ user_input = renpy.input("What do you say ?", length=1000)
#     #     $ renpy.fix_rollback()
#     #     Player "[user_input]" (interact=False)
#     #     $ messages.append({"role": "user", "content": user_input})
#     #     python:
#     #         ai_reply=renpy.roll_forward_info() or completion(messages)[-1]["content"]
#     #         renpy.checkpoint(data=ai_reply,hard=False)
#     #     e "[ai_reply]"
#     #     $ messages.append({"role": "assistant", "content": ai_reply})



