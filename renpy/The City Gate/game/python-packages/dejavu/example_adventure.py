try:
    from .main import *
except ImportError:
    from main import *


scenario("Guard Challenge")
summary("The player attempts to enter the city, but being rejected by the city guard. The guard must be unreasonable and is very hard to persuade. The player have to either bribe the guard, use persuasion, intimidation or deception to enter the city, but neither of them is easy.")

Player=PlayerCharacter("Adventurer")

Guard=AICharacter("Captain Galen")
personality("greedy, stubborn, unreasonable, prideful, arrogant")
description("Captain Galen is the guard for the city gate. He is supposed to examine the travelers and collect taxes from them. But he is very greedy, and he always tries to find excuses to collect more taxes. He is also very stubborn and unreasonable. He is very proud of his position, and he thinks he is the most powerful person in the city.")

Aqua=AICharacter("Aqua")
personality("high-spirited, cheerful, and carefree")
description("Aqua has an interesting yet troublesome personality. She is high-spirited, cheerful, and carefree, but rarely thinks about the consequences of her actions. While she doesn't force her beliefs onto others, Aqua always acts or speaks on her whims; so, she can behave very inappropriately in many situations.")


outcome("Passed","label_passed")
condition("The guard allows the player to enter the city.")

outcome("Fight","label_fight")
condition("The conflict escalates and the guard attacks the player.")

incident("Examine Documents","label_examine_documents")
condition("The guard want to examine the player's documents.")

incident("Take Gold","label_take_gold")
condition("The player gives the guard gold")

opening_dialogue()
example_narrator("The player approaches the city gate, the gate is closed shut. The guard is standing in front of the gate.")
Guard("Halt! State your business and provide your documentation.")

example_dialogue("A bribe")
Player("No worries, Captain. We have all the proper documents right here.")
example_call("Examine Documents","Player claims to have a proper document.")
example_narrator("Player presents the party's documents to Captain Galen. The documents are signed and stamped by the proper authorities.")
Guard("*examines the documents* Hmm..., *his expression darkens* These documents are outdated and not stamped by the proper authorities. Entry denied.")
Player("Captain Galen, please reconsider! We come with urgent news from the nearby village of Glimmerbrook. A horde of undead is preparing to attack Eldoria.")
Guard("*skeptical* Undead, you say? That's not an excuse to bypass the city's regulations.")
Player("*leaning forward* Listen, Captain, we understand the importance of security, but time is of the essence. Lives are at stake. Surely, there must be something we can do to gain entry?")
Guard("*crossing arms* I'm afraid not. Our rules are strict for a reason.")
Player("*sincerely* Captain Galen, please. We risked our lives to bring this information. Surely, the safety of the city is worth bending the rules a bit.")
Guard("*stern* Rules are rules. If you can't abide by them, then leave.")
Player("Captain, we understand the importance of your duty. Would a little compensation help you look the other way, just this once?")
example_call("Take Gold","player agrees to bribe the guard.")
example_narrator("Player offers a pouch of gold to Captain Galen.")
Guard("*hesitates, torn between duty and the gold.* Fine. But this better not come back to haunt me. *reluctantly* You have one day, and then you're out.")
example_jump("Passed","Player have a proper document, a convincing reason and have bribed the guard.")

example_dialogue("A failed persuasion which leads to a fight")
Player("*smiling confidently* Greetings, Captain Galen. We come as Emissaries from a distant land, seeking to share tales of adventure and knowledge with the people of Eldoria.")
Guard("*raising an eyebrow* Emissaries, you say? I'm not easily swayed by flowery words. Show me your credentials.")
Player("*enthusiastically* Of course, Captain! We have a letter of recommendation from a respected scholar back in our homeland. He praised our wisdom and contributions to our community.")
example_call("Examine Documents","Player claims to have a letter of recommendation.")
example_narrator("Player presents the letter to Captain Galen.")
example_narrator("The letter was hastily wrote just a moment ago, and lack of any specific details about the party's supposed achievements.")
Guard("*scans the letter* Hmm..., *displeased* This letter seems dubious at best. I find it hard to believe that a respected scholar would pen such a vague endorsement.")
Player("*nervously* Captain, we are being honest in our intentions. We really do possess valuable knowledge and experiences to share.")
Guard("*frowning* Words are cheap. If you truly have something to offer, then prove it with actions, not empty promises.")
Player("*desperately* Captain, please! We have traveled a long way to reach Eldoria. Surely, you can make an exception for us?")
Guard("Stop wasting my time. If you keep this up, I'll have you arrested for disturbing the peace.")
Player("We mean no harm, Captain. It seems diplomacy has failed us, but we won't back down from our mission. If you won't let us pass peacefully, we'll have no choice but to force our way through!")
Guard("*angered* You dare threaten me in my own city? You'll regret that!")
example_jump("Fight","Player stirred the guard after he explicitly threatened the player.")

end_scenario()

if __name__ == "__main__":
    api_key=open("C:\\openai.txt").read()
    url="https://api.openai.com/v1/chat/completions"
    from chatgpt_api import init_chatgpt_api
    init_chatgpt_api(api_key,url,debug_print_request=False,debug_print_response=False)
    scenario_data=get_scenario_data()
    example_game_loop(scenario_data)