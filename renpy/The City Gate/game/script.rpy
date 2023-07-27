define Player= Character("Player", color="#c8ffc8", what_prefix="")
define NPC = Character("NPC", color="#ffc8c8", what_prefix="")


label start:

    python:
        import time
        def get_ai_response(query):
            return "This is a dummy response. {}".format(int(time.time()*3))






    call city_gate
    return





    
label example_bad_rollback_loop:
    while True:
        $ user_input= renpy.input("What do you want to say? ")
        $ renpy.fix_rollback()

        $ iNPC=0
        while iNPC<2:
            python:
                ai_response=renpy.roll_forward_info()
                if ai_response is None:
                    ai_response=get_ai_response(user_input)
                renpy.checkpoint(ai_response)
            $ iNPC+=1
            $ NPC(ai_response)
