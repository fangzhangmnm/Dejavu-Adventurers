# default guard_diary=[]
# default aqua_diary=[]

label city_gate:
    scene city gate
    with fade

    $ Guard=AICharacter("Captain Galen")
    personality "greedy, stubborn, unreasonable, prideful, arrogant"
    bio "Captain Galen is the guard for the city gate. He is supposed to examine the travelers and collect taxes from them. But he is very greedy, and he always tries to find excuses to collect more taxes. He is also very stubborn and unreasonable. He is very proud of his position, and he thinks he is the most powerful person in the city."

    $ Adventurer=PlayerCharacter("Adventurer")

    $ Aqua=AICharacter("Aqua")
    personality "high-spirited, cheerful, and carefree"
    bio "Aqua has an interesting yet troublesome personality. She is high-spirited, cheerful, and carefree, but rarely thinks about the consequences of her actions. While she doesn't force her beliefs onto others, Aqua always acts or speaks on her whims; so, she can behave very inappropriately in many situations."



    scenario "Guard Challenge"
    summary "The Adventurer attempts to enter the city, but being rejected by the city guard. The guard must be unreasonable and is very hard to persuade. The Adventurer have to either bribe the guard, use persuasion, intimidation or deception to enter the city, but neither of them is easy."

    characters "Captain Galen, Adventurer, Aqua"

    opening_dialogue "Opening"

    narrator_dejavu "The Adventurer approaches the city gate, the gate is closed shut. The guard is standing in front of the gate."

    show captain galen at right
    with dissolve

    Guard "Halt! State your business and provide your documentation."

    # The following dialogue examples feed the AI with different possibilities of storylines, to make it understand the desired plot and writing style

    example_dialogue "A bribe"

    Adventurer "No worries, Captain. Here is the document"
    Guard "Give me the letter, Adventurer. *impatiently* I don't have all day. "
    call_incident "Examine Documents" ("The guard need to check the document to confirm what Adventurer says") # Here AI will learn to ask the game engine to provide information about the document
    narrator_dejavu "Adventurer presents the party's documents to Captain Galen. The documents are signed and stamped by the proper authorities."
    Guard "*examines the documents* Hmm... *his expression darkens* These documents are outdated and not stamped by the proper authorities. Entry denied."
    Adventurer "Captain Galen, please reconsider! We come with urgent news from the nearby village of Glimmerbrook. A horde of undead is preparing to attack Eldoria."
    Guard "*skeptical* Undead, you say? That's not an excuse to bypass the city's regulations."
    Adventurer "*leaning forward* Listen, Captain, we understand the importance of security, but time is of the essence. Lives are at stake. Surely, there must be something we can do to gain entry?"
    Guard "*crossing arms* I'm afraid not. Our rules are strict for a reason."
    Adventurer "*sincerely* Captain Galen, please. We risked our lives to bring this information. Surely, the safety of the city is worth bending the rules a bit."
    Guard "*stern* Rules are rules. If you can't abide by them, then leave."
    Adventurer "Captain, we understand the importance of your duty. Would a little compensation help you look the other way, just this once?"
    Guard "*raised eyebrow* Hugh? What are you implying? "
    call_incident "Need Take Bribe" ("The guard need to receive the bribe to let the Adventurer pass.")
    narrator_dejavu "Adventurer offers a pouch of gold to Captain Galen."
    Guard "*hesitates, torn between duty and the gold.* Fine. But this better not come back to haunt me. *reluctantly* You have one day, and then you're out."
    jump_outcome "Allow Enter" ("After receiving the bribe and examine the document, The guard allowed the player to enter the city") # AI will determine which outcome the player achieved!

    example_dialogue "A failed persuasion which leads to a fight"

    Adventurer "*smiling confidently* Greetings, Captain Galen. We come as Emissaries from a distant land, seeking to share tales of adventure and knowledge with the people of Eldoria."
    Guard "*raising an eyebrow* Emissaries, you say? I'm not easily swayed by flowery words. Show me your credentials."
    Adventurer "*enthusiastically* Of course, Captain! We have a letter of recommendation from a respected scholar back in our homeland. He praised our wisdom and contributions to our community."
    Guard "Give me the letter, Adventurer. *impatiently* I don't have all day. "
    call_incident "Examine Documents" ("The guard need to check the letter to confirm what Adventurer says")
    narrator_dejavu "Adventurer presents the letter to Captain Galen."
    narrator_dejavu "The letter was hastily wrote just a moment ago, and lack of any specific details about the party's supposed achievements."
    Guard "*scans the letter* Hmm...*displeased* This letter seems dubious at best. I find it hard to believe that a respected scholar would pen such a vague endorsement."
    Adventurer "*nervously* Captain, we are being honest in our intentions. We really do possess valuable knowledge and experiences to share."
    Guard "*frowning* Words are cheap. If you truly have something to offer, then prove it with actions, not empty promises."
    Adventurer "*desperately* Captain, please! We have traveled a long way to reach Eldoria. Surely, you can make an exception for us?"
    Guard "Stop wasting my time. If you keep this up, I'll have you arrested for disturbing the peace."
    Adventurer "We mean no harm, Captain. It seems diplomacy has failed us, but we won't back down from our mission. If you won't let us pass peacefully, we'll have no choice but to force our way through!"
    Guard "*angered* You dare threaten me in my own city? You'll regret that!"
    jump_outcome "Fight" ("The player is going to engaged in a fight with the guard")


    outcome "Allow Enter" (label="city_gate.passed",deciders=[Guard])
    condition "The guard allows the Adventurer to enter the city."

    # outcome "Irritated" (label="city_gate.fight") # to bypass the safety check of ChatGPT, we need to hard coding the guard's attack behavior
    # condition "The conflict was escalates by the Adventurer's agressive bahavior, and the guard was extremely irritated."

    outcome "Fight" (label="city_gate.fight",deciders=[Guard]) # if player actively decide to fight the guard, ChatGPT is still able to generate the guard's attack behavior
    condition "The conflict escalates and the guard attacks the Adventurer."

    incident "Examine Documents" (label="city_gate.examine_documents",deciders=[Guard])
    condition "The guard need to check the document to confirm what Adventurer says."

    incident "Need Take Bribe" (label="city_gate.take_item",deciders=[Guard])
    condition "The guard need to receive the bribe (or the fee) to let the Adventurer pass."

    enable_quit "Quit" (label="city_gate.quit")

    end_scenario ""

    jump dejavu_dialogue_loop # must use jump instead of return

label .quit:
    "You decided to find another way to enter the city."
    "Bad Ending"
    jump second_day

label .fight:
    "You end up fighting the guard."
    "Bad Ending"
    jump second_day

label .passed:
    "You successfully enter the city."
    "Good Ending"
    jump second_day

label .examine_documents:
    narrator_dejavu "The guard examines Adventurer's documents."
    $ description=renpy.input("(debug only) What is the description of the document?",length=1000)
    $ renpy.fix_rollback()
    narrator_dejavu "[description]" (slience=True)
    return

label .take_item:
    $ item=renpy.input("(debug only) What item do you want to give? \"no\" for not giving anything, enter for more discussion",length=1000) # We need to check player's inventory in actual game!
    $ renpy.fix_rollback()
    if item=="no":
        narrator_dejavu "Adventurer refuses to give the item" # The Guard will get mad at that.
    elif item=="":
        narrator_dejavu "Adventurer tries to persuade the guard again."
    else:
        narrator_dejavu "Adventurer gives [item] to the guard"
        "You lose [item]!"
        # player.item--
    return

label second_day:
    scene city gate
    with fade

    scenario "Guard Challenge - Second Day"
    summary "Player met the guard again after they are hired by the duke of Eldoria as a royal advisor."

    $ characters([Guard,Aqua,Adventurer])
    
    opening_dialogue "Opening"

    if dejavu.runtime.outcome_name !="Allow Enter":
        narrator "Despite failed in persuading the guard, GM decides to let the player enter the city for debug convenience."

    narrator_dejavu "After the player entered the city, they are interviewe by the duke of Eldoria. The duke is impressed by the player's knowledge and experience, and he decides to hire the player as a royal advisor. On the second day, the player appeared at the city gate again."

    enable_quit "Quit" (label="second_day.quit")

    end_scenario ""


    jump dejavu_dialogue_loop

label .quit:
    "Game End"
    return


