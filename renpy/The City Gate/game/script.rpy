label start:
    jump city_gate



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

    
