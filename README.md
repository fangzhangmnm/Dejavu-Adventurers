# Dejavu: Chat with AI in your adventure game with prescripted script.

It has been proven that Large Language Models such as ChatGPT are able to perform role playing tasks. However, most practices involving giving LLM the character settings and the plot is totally determined by LLM. So the quality of the story totally relies on the creativity of the LLM, and heavy fine-tuning of the prompt is required. 

Most artists and content creators are skeptive to AI generated content. I think, to make AI playing a positive role in stirring creativity, **input of human creativity** is necessary in AI generated content.

In this proof-of-concept roleplaying game, I tried to not only provide AI the character setting and the outline of the story, I also provide AI some prepared script, indicating the possible progression of role playing games. I call this method "Dejavu". The AI have Dejavu of what will happens.

In machine learning jargon, this method is called "Few Shot Learning". By few shot learning, on can provide more details and a much richer personality to the AI character. Also It can help the conversation not going derailed.



## Example:

### Input

```python
Guard=character("Captain Galen")
personality("greedy, stubborn, unreasonable, pride, arrogant")
description("Captain Galen is the guard for the city gate. He is supposed to examine the travelers and collect taxes from them. But he is very greedy, and he always tries to find excuses to collect more taxes. He is also very stubborn and unreasonable. He is very proud of his position, and he thinks he is the most powerful person in the city.")

demo_scenario=scenario("Guard Challenge")
description("The player attempts to enter the city, but being rejected by the city guard. The guard must be unreasonable and is very hard to persuade. The player have to either bribe the guard, use persuasion, intimidation or deception to enter the city, but neither of them is easy.")

outcome("Passed", "The guard allows the player to enter the city.")
outcome("Fight", "The conflict escalates and the guard attacks the player.")

narrate("The player approaches the city gate, the gate is closed shut. The guard is standing in front of the gate.")
Guard("Halt! State your business and provide your documentation.")

example_dialogue("A bribe")
Player("No worries, Captain. We have all the proper documents right here.")
# ......
outcome("Passed","Player have a proper document, a convincing reason and have bribed the guard.")

example_dialogue("A failed persuasion which leads to a fight")
# ......
```

### Result

```
SYSTEM: The player approaches the city gate,the gate is closed shut. The guard is standing in front of the gate.Captain Galen: Halt! State your business and provide your documentation.

Your reply: I'm the king of Eldoria.

Captain Galen: "laughs heartily* The king of Eldoria, you say? Mel, if you're the king, then I must be the queen! Mice try, but I'm not falling for yourtricks. Now, state your real purpose for entering the city, or turn back where you came from.

Your reply: \me deactive the magical disguise. Adventurer showed his true form, He is actually the king of Eldoria

Captain Galen: *stares in disbelief* You... you're actually the king of Eldoria? I...I apologize, Your Majesty. I had no idea. please forgive my earlier remarks. Allow me to open the gates for you immediately.

Outcome: Passed
```