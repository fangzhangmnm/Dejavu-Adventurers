define Player= Character("Player", color="#c8ffc8", what_prefix="")
define NPC1 = Character("NPC1", color="#ffc8c8", what_prefix="")
define NPC2 = Character("NPC2", color="#ffc8c8", what_prefix="")
label start:
    while True:
        $ player_input= renpy.input("What do you want to do?")
        $ renpy.fix_rollback()
        Player "[player_input]" (interact=False)

        $ response=renpy.roll_forward_info()
        if response is None:
            $ response=str(renpy.random.randint(1, 10))
        $ renpy.checkpoint(response,hard=False)
        $ renpy.fix_rollback()
        NPC1 "[response]"
        

        



    "Start Testing"
    call city_gate
    "Successfully returned!"
    $ log_object(dejavu_store.scenario_data)
    return





    
