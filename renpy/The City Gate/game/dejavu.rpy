init offset=-99

default dejavu_store.scenario_data=None # don't put objects here. pure json. should be static
default dejavu_store.current={} # pointers to the objects in scenario_data we are currently writing to
default dejavu_store.state="disabled"
default dejavu_store.character_objects={} # stores the DejavuCharacter objects
default dejavu_store.diary_references={} # stores the diary list references. Will be cleared when new scenario starts
default dejavu_store.log_level=2
        

# DSL injection

define NARRATOR_NAME="SYSTEM"
define ONGOING_OUTCOME_NAME="ONGOING"
define PLAYER_QUIT_OUTCOME_NAME="PLAYER_QUIT"

init python: 
    def log_text(text):
        for line in text.split("\n"):
            renpy.log(line)
        renpy.log("")

    def log_object(obj):
        import json
        text=json.dumps(obj,indent=4,default=lambda o: '<not serializable>')
        for line in text.split("\n"):
            renpy.log(line)
        renpy.log("")

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

    def dejavu_scenario(name,*args,**kwargs):
        dejavu_store.on_new_scenario()
        dejavu_store.scenario_data={
            'name':name,
            'summary':"",
            'characters':{},
            'outcomes':{},
            'opening_dialogue':{
                'name':"Opening",
                'description':"",
                'content':[],
            },
            'example_dialogues':{},
            'player_character_name':"Player",
            'npc_names':[],
        }

    def dejavu_end_scenario(what="",*args,**kwargs):
        dejavu_store.set_state("disabled")

    def dejavu_summary(content,*args,**kwargs):
        dejavu_store.scenario_data['summary']=content


    def dejavu_character(name,is_player=False,*args,**kwargs):
        assert name!=NARRATOR_NAME
        dejavu_store.scenario_data['characters'].setdefault(name,{
            'name':name,
            'description':"",
            'personality':"",
            'diary_list':[],
        })
        dejavu_store.current['character']=('characters',name)
        if is_player:
            dejavu_store.scenario_data['player_character_name']=name
        else:
            dejavu_store.scenario_data['npc_names'].append(name)
        dejavu_store.character_objects[name]=dejavu_store.DejavuCharacter(name,is_player=is_player,*args,**kwargs)
        return dejavu_store.character_objects[name]

    def AICharacter(name,*args,**kwargs):
        return dejavu_character(name,is_player=False,*args,**kwargs)

    def PlayerCharacter(name,*args,**kwargs):
        dejavu_store.scenario_data['player_character_name']=name
        return dejavu_character(name,is_player=True,*args,**kwargs)

    dejavu_narrator=dejavu_store.DejavuCharacter(NARRATOR_NAME)

    def dejavu_description(content,*args,**kwargs):
        character=dejavu_store.get_object(dejavu_store.current['character'])
        character['description']=content

    def dejavu_personality(content,*args,**kwargs):   
        character=dejavu_store.get_object(dejavu_store.current['character'])
        character['personality']=content

    def dejavu_read_diary(diary_list:list):
        character=dejavu_store.get_object(dejavu_store.current['character'])
        character['diary_list'].extend(diary_list)

    def dejavu_write_diary(diary_list_reference:list):
        character=dejavu_store.get_object(dejavu_store.current['character'])
        dejavu_store.diary_references[character['name']]=diary_list_reference

    def dejavu_outcome(name,label=None,type='outcome',once=False,*args,**kwargs):
        dejavu_store.scenario_data['outcomes'].setdefault(name,{
            'name':name,
            'label':label or name,
            'condition':"",
            'type':type,
        })
        dejavu_store.current['outcome']=('outcomes',name)

    def dejavu_incident(name,label=None,once=True,*args,**kwargs):
        dejavu_outcome(name,label,type='incident',once=once)

    def dejavu_condition(content,*args,**kwargs):
        outcome=dejavu_store.get_object(dejavu_store.current['outcome'])
        outcome['condition']=content

    def dejavu_opening_dialogue(name='Opening',*args,**kwargs):
        dejavu_store.scenario_data['opening_dialogue']['name']=name
        dejavu_store.current['dialogue']=('opening_dialogue',)
        dejavu_store.set_state("opening_dialogue")

    def dejavu_example_dialogue(name,*args,**kwargs):
        dejavu_store.scenario_data['example_dialogues'].setdefault(name,{
            'name':name,
            'description':"",
            'content':[],
            'outcome_name':"",
            'outcome_comment':"",
        })
        dejavu_store.current['dialogue']=('example_dialogues',name)
        dejavu_store.set_state("example_dialogue")


# game loop

default dejavu_store.rollback=dejavu_store.RollBack() # initialize the rollback system at the new game

label dejavu_dialogue_loop:
    python:
        assert dejavu_store.state=='disabled', "You must call end_scenario() before calling dejavu_dialogue_loop."
        dejavu_store.history=list(dejavu_store.scenario_data['opening_dialogue']['content'])
        dejavu_store.removed_incidents=[]
        dejavu_store.set_state("playing")
        dejavu_store.outcome=ONGOING_OUTCOME_NAME
        dejavu_store.player_character_name=dejavu_store.scenario_data['player_character_name']
        dejavu_store.npc_names=dejavu_store.scenario_data['npc_names']
        if dejavu_store.log_level>1:
            renpy.log("Compiled scenario:")
            log_object(dejavu_store.scenario_data)
    while True:
        # player input
        python:
            dejavu_store.user_input=dejavu_store.rollback.get()
            if dejavu_store.user_input is None:
                renpy.suspend_rollback(True)
                dejavu_store.user_input = renpy.input("What do you say ? (enter to skip, 'quit' to quit)", length=1000) or "" # need to put in separate statement to make fix_rollback work
                dejavu_store.rollback.set(dejavu_store.user_input)
                renpy.suspend_rollback(False)
        if dejavu_store.user_input.lower() in ["quit","exit"]:
            $ dejavu_store.outcome=PLAYER_QUIT_OUTCOME_NAME
            call dejavu_dialogue_loop_finally_block from dejavu_dialogue_loop_label_1
            return
        if len(dejavu_store.user_input)>0:
            $ dejavu_store.Player=dejavu_store.character_objects[dejavu_store.player_character_name]
            $ dejavu_store.Player(dejavu_store.user_input,no_substitution=True)

        # npc dialogue
        $ dejavu_store.iNPC=0
        while dejavu_store.iNPC<len(dejavu_store.npc_names):
            python:
                dejavu_store.NPC=dejavu_store.character_objects[dejavu_store.npc_names[dejavu_store.iNPC]]
                dejavu_store.npc_name=dejavu_store.npc_names[dejavu_store.iNPC]
                dejavu_store.ai_reply=dejavu_store.rollback.get()
                if dejavu_store.ai_reply is None:
                    dejavu_store.ai_reply=dejavu_store.perform_roleplay_query(dejavu_store.npc_name,dejavu_store.scenario_data, dejavu_store.history)
                    dejavu_store.rollback.set(dejavu_store.ai_reply)
                dejavu_store.iNPC+=1
            $ dejavu_store.NPC(dejavu_store.ai_reply,no_substitution=True)

            # check outcome. 
            # unfortunately, we need to do this after each NPC dialogue, because AI might be distracted by the other NPC's dialogue
            python:
                dejavu_store.outcome_tuple=dejavu_store.rollback.get()
                if dejavu_store.outcome_tuple is None:
                    dejavu_store.outcome_tuple=dejavu_store.perform_check_outcome_query(dejavu_store.scenario_data,dejavu_store.history,removed_incidents=dejavu_store.removed_incidents)
                    dejavu_store.rollback.set(dejavu_store.outcome_tuple)
                dejavu_store.outcome_name,dejavu_store.outcome_type,dejavu_store.outcome_comment=dejavu_store.outcome_tuple
            
            if dejavu_store.outcome_type=="incident":
                $ dejavu_store.removed_incidents.append(dejavu_store.outcome_name)
                call expression dejavu_store.get_outcome_label(dejavu_store.outcome_name) from dejavu_dialogue_loop_label_2
            elif dejavu_store.outcome_type=="outcome":
                call dejavu_dialogue_loop_finally_block from dejavu_dialogue_loop_label_3
                jump expression dejavu_store.get_outcome_label(dejavu_store.outcome_name)

    $ assert False
    
label dejavu_dialogue_loop_finally_block:
    $ dejavu_store.set_state("disabled")

    python:
        for name,diary_references in dejavu_store.diary_references.items():
            diary_references.append(dejavu_store.perform_summary_query(name,dejavu_store.scenario_data,dejavu_store.history))

    return
