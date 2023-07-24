define Galen = Character("Captain Galen")
define Player = Character("Player")

    
init python:
    from dejavu import init_chatgpt_api,completion
    api_key=open("C:\\openai.txt").read()
    proxy="https://api.openai.com/v1/chat/completions"
    init_chatgpt_api(api_key=api_key, proxy=proxy)



    


    class AICharacter:
        def __init__(name):
            self.name=name
        def __str__(self):
            return self.name

    

        
    

    







label start:
    define e = Character("Eileen")
    define Player=Character("Player")

    # $ round=1
    # $ user_input = ""
    # while True:
    #     if round==1:
    #         e "Hello there, my name is Eileen, who are you ?"
    #     else:
    #         e "You said [user_input], what do you mean ?"
    #     $user_input = renpy.input("What do you say ?", length=1000)
    #     Player "[user_input]" (interact=False)
    #     $round+=1

    
    python:
        messages=[
            {"role": "system", "content": "You are Eileen, a tennage student enrolled at Miskatonic Univeristy of Arkham. You are secretly in love with the user. You laugh very frequently and finish your sentences with 'Hihihi'"},
        ]

    $ai_reply="Hello there, my name is Eileen, I am so happy to see you ! Hihihi"

    while True:
        $ renpy.fix_rollback()
        e "[ai_reply]"
        $ messages.append({"role": "assistant", "content": ai_reply})
        $ user_input = renpy.input("What do you say ?", length=1000)
        Player "[user_input]" (interact=False)
        $ messages.append({"role": "user", "content": user_input})
        $ ai_reply=completion(messages)[-1]["content"]

label city_gate:

    scene city gate
    with fade

    narrator "The player approaches the city gate, the gate is closed shut. The guard is standing in front of the gate."

    show captain galen at right
    with dissolve

    Galen "Halt! State your business and provide your documentation."

    Player "No worries, Captain. We have all the proper documents right here."
    narrator "Player presents the party's documents to Captain Galen. The documents are signed and stamped by the proper authorities."
    Galen "*examines the documents* Hmm..., *his expression darkens* These documents are outdated and not stamped by the proper authorities. Entry denied."
    Player "Captain Galen, please reconsider! We come with urgent news from the nearby village of Glimmerbrook. A horde of undead is preparing to attack Eldoria."
    Galen "*skeptical* Undead, you say? That's not an excuse to bypass the city's regulations."
    Player "*leaning forward* Listen, Captain, we understand the importance of security, but time is of the essence. Lives are at stake. Surely, there must be something we can do to gain entry?"
    Galen "*crossing arms* I'm afraid not. Our rules are strict for a reason."
    Player "*sincerely* Captain Galen, please. We risked our lives to bring this information. Surely, the safety of the city is worth bending the rules a bit."
    Galen "*stern* Rules are rules. If you can't abide by them, then leave."
    Player "Captain, we understand the importance of your duty. Would a little compensation help you look the other way, just this once?"
    narrator "Player offers a pouch of gold to Captain Galen."
    Galen "*hesitates, torn between duty and the gold.* Fine. But this better not come back to haunt me. *reluctantly* You have one day, and then you're out."

    jump passed

label passed:
    narrator "The party enters the city."
    narrator "success ending"