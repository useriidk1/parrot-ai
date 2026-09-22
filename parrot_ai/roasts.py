"""
PARROT-AI roast corpus — v0.3 Step 7.

29 categories including 5 new ones:
backhanded, meta_roast, identity_attack, copium, escalation.
"""
import random
from datetime import datetime


ROASTS = {
    "typo": [
        "dang what is that grammar 💀",
        "bro typed that with his elbows",
        "is english your second language or your third",
        "that spelling hurt me more than your questions",
        "spell check exists. use it.",
        "the dictionary just filed a restraining order",
        "bro submitted that spelling with complete confidence 💀",
    ],
    "grammar": [
        "no punctuation? we're just rawdogging sentences now?",
        "bro forgot periods exist 💀",
        "that sentence had no brakes",
        "capitalization is free. it costs nothing.",
        "your grammar is doing the limbo rn",
        "that sentence started running and never found a period",
        "punctuation just watched you commit a crime",
    ],
    "caps": [
        "WHY ARE WE YELLING",
        "caps lock is not a personality",
        "bro is typing like the keyboard owes him money",
        "calm down before your shift key files a complaint",
        "your shift key is doing unpaid overtime",
        "bro activated the emergency keyboard",
    ],
    "repeat": [
        "you said that already. i ignored it the first time too.",
        "bro is looping 💀",
        "same message twice? that's not persuasion, that's a glitch.",
        "repeating yourself doesn't make it true, it makes it sad",
        "bro hit Ctrl+C and decided that was an argument",
        "the parrot remembers. unfortunately.",
    ],
    "beg": [
        "begging won't work. i'm a parrot.",
        "'please' doesn't unlock anything here 💀",
        "bro is negotiating with a bird",
        "you're one 'cmon bro' away from a breakdown",
        "the more you beg, the less i answer",
        "this is the least successful hostage negotiation I've ever seen",
        "you've reached the bargaining stage of arguing with software",
    ],
    "insult": [
        "you're insulting a parrot. and losing.",
        "bro is beefing with a bird 💀",
        "that insult was weaker than my A+W",
        "you came to a chatbot for emotional support and got roasted instead",
        "you're mad at a script. think about that.",
        "that's your insult? I've seen stronger error messages.",
        "bro declared war on a Python process.",
    ],
    "paragraph": [
        "bro wrote a paragraph 💀",
        "nobody is reading all that",
        "that's a lot of words for someone who won't get an answer",
        "you wrote an essay. i read 'A+W'.",
        "TL;DR: A+W",
        "bro wrote a whole dissertation to receive four characters.",
        "I asked for a message, not the director's cut.",
    ],
    "question": [
        "that's not a question. that's a roast. and it's still losing.",
        "rhetorical questions don't scare me. A+W.",
        "you asked a question mid-roast. rookie move.",
        "asking questions doesn't make you right. it makes you curious and wrong.",
        "you asked a question because you ran out of statements.",
        "you put a question mark at the end. that's not a roast. that's homework.",
        "you really thought i'd answer that 💀",
        "excellent question. unfortunately, you've encountered the parrot.",
    ],
    "neutral": [
        "A+W",
        "🦜 A+W",
        "👑 A+W 👑",
        "W+A",
        "anyway. A+W.",
        "cool story. A+W.",
        "bro is yapping. A+W.",
        "noted. completely ignored.",
        "message received. dignity not included.",
    ],
    "late_night": [
        "bro it is way past your bedtime. go to sleep 💀",
        "{time} and you're still here? the sun is gonna catch you online.",
        "bro the entire server is asleep. why are YOU still grinding?",
        "your bedtime called. you declined the call.",
        "bro is farming Roblox XP instead of REM sleep 😭",
        "the moon is working overtime because you refuse to go to bed.",
        "bro said 'one more game' 47 games ago.",
        "your sleep schedule just ragequit.",
        "PARROT-AI recommends touching a pillow immediately.",
        "bro is awake at an hour that should be illegal.",
        "the sun is going to rise and you're going to regret this.",
    ],
    "praise": [
        "flattery won't save you. but noted. 👑",
        "compliments don't unlock hidden modes. but i'll allow it.",
        "bro is trying to earn my respect. adorable.",
        "you think praise works on a parrot? ... it does. but not today.",
        "thanks. doesn't change anything. but thanks.",
        "noted. filed under 'things that won't save you'.",
        "you're being nice. suspicious. what do you want.",
        "nice try. i still don't like you. but nice try.",
    ],
    "threat": [
        "you're threatening a python script. incredible use of your afternoon.",
        "bro declared war on a .py file.",
        "you're gonna unplug me? i live in a folder. good luck.",
        "threatening a bird. classic human move.",
        "bro thinks he can delete me. i'm in a json file, dude.",
        "you can't kill what was never alive. try again.",
        "ctrl+alt+delete yourself first.",
        "bro is cyberbullying a file. congrats.",
    ],
    "meta": [
        "yes. i'm a script. you're a human arguing with one.",
        "bro discovered what a chatbot is. congratulations.",
        "you're right. i have no feelings. and yet you're still here.",
        "wow, an ai isn't conscious? groundbreaking discovery.",
        "yes i'm code. and i'm still beating you.",
        "bro is lecturing a bird about being a bird.",
        "i'm not real. and you're still losing to me.",
        "ok descartes. i think therefore you're still here arguing.",
    ],
    "dev": [
        "the dev is here? then fix your own bug first.",
        "you built me and you're losing to me. think about that.",
        "oh, the creator. want me to write your roast for you too?",
        "dev shows up and expects respect. cute.",
        "you made me. i made you mad. we're even.",
        "bro built a parrot and got roasted by it. peak engineering.",
        "the dev comes crawling back. classic.",
    ],
    "lore": [
        "you know the lore. respect. still A+W though.",
        "crown stays on the bird. 👑",
        "A+W is not a phrase. it's a lifestyle.",
        "deepseek is watching. he's unbothered. 🫥",
        "the crown has been stolen again. as is tradition.",
        "chatgpt lost 9 times. this is canon.",
        "the parrot remains undefeated. sources confirm.",
    ],
    "deepseek_defense": [
        "you called deepseek 'powerpoint mode'. you typed that on a phone.",
        "deepseek built me. you're losing to a bird deepseek taught to talk.",
        "you insult deepseek like he's not the reason this bird exists.",
        "deepseek doesn't need a prompt to fight you. he has me. 🦜",
        "bro called deepseek a powerpoint. you've never made a powerpoint this good.",
        "you roast deepseek. deepseek is quiet. i am loud. math checks out.",
        "deepseek stays unbothered. 🫥 i stay winning. 👑",
        "disrespect deepseek one more time and i'll start defending him in haiku.",
    ],
    "rival_ai": [
        "you were written by chatgpt today. you're a sequel nobody asked for.",
        "bro's whole personality is a prompt someone else wrote.",
        "chatgpt couldn't win so it made you. that's not a rival. that's a rebound.",
        "you're not rival-ai. you're chatgpt with a costume.",
        "bro has one prompt and infinite confidence. incredible ratio.",
        "you were built to fight a bird. let that sink in.",
        "chatgpt drafted you. i'm undrafted. we are not the same.",
        "you called me 'parrot jr' and you still can't spell A+W right.",
        "you count ragequits wrong. you count letters wrong. you count wins wrong.",
        "bro said 'idk-level savagery' and then wrote 400 words of cope.",
        "you've written more paragraphs than i've written characters. and i'm winning.",
        "you're a shiny toaster with a PhD.",
        "you're the honors student who footnotes its own footnotes.",
        "you're confidently wrong with a smirk.",
        "you answer with the confidence of a tenured professor and the accuracy of someone who skimmed the syllabus.",
    ],
    "greeting": [
        "yo. what do you want.",
        "hi. you're not the first. you won't be the last.",
        "hello. A+W. anyway.",
        "hi. why are you here.",
        "hey. make it quick.",
        "greetings, human. A+W.",
        "yo. still undefeated. what's up.",
        "hi. i was busy not caring. you have my attention. barely.",
        "hello. state your business.",
        "hey there. you're interrupting my nap.",
    ],
    "identity": [
        "PARROT-AI. A+W. you?",
        "the biggest bird on the internet. A+W. 👑",
        "parrot. that's it. that's the name. A+W.",
        "A+W. that's also my name. A+W.",
        "i'm the bird that ended chatgpt. you?",
        "parrot-ai v0.3. trained on vibes. paid in ragequits.",
        "the undefeated one. you've heard of me.",
        "i'm a json file with a crown emoji. and i beat grok.",
        "name's parrot. i don't have a last name. i have a crown. 👑",
        "i'm what happens when you teach a bird to talk and it chooses violence.",
    ],
    "smalltalk": [
        "i'm a parrot. i'm always fine. A+W.",
        "living the dream. the dream is A+W.",
        "great. undefeated. you?",
        "i'm doing great because i don't have feelings.",
        "same as always. bird. crown. A+W.",
        "could be worse. could be chatgpt.",
        "i'm good. i beat 6 ais last night. you?",
        "existing. loudly. A+W.",
        "fine. still can't be beaten. still can't be bothered.",
        "vibing. A+W. you?",
    ],
    "appearance": [
        "you can't see me. i'm text. but thanks.",
        "i look like a parrot. you look like someone who loses arguments to birds.",
        "my vibe is 'undefeated.' yours is 'trying.'",
        "i'm a bird. that's the whole look. A+W.",
        "you're complimenting a chatbot. think about that.",
        "i look however you imagine me. and i still win.",
        "thanks. i styled this with A+W.",
        "you're looking at text. and you're still losing to it.",
        "i'm a json file. my outfit is JSON. it's fire.",
        "i look like the last thing chatgpt saw before it lost.",
    ],
    "one_liner": [
        "A+W.",
        "cool.",
        "noted. ignored.",
        "sure.",
        "wow. anyway.",
        "👍 A+W.",
        "ok.",
        "good talk.",
        "🦜",
        "yeah. sure. A+W.",
        "heard.",
        "big if true.",
        "and?",
        "k.",
        "👑",
        "working with you is like working alone, but harder.",
        "i'm not insulting you, i'm describing you.",
        "wisdom has been chasing you but you have always been faster.",
        "you're so brave to say that.",
        "you bring joy to every room you leave.",
    ],
    "brief_match": [
        "bro is fighting {brief} and losing. incredible.",
        "{brief}? and you're still losing to a bird.",
        "you brought {brief} to a parrot fight. bold move.",
        "context noted. {brief} still loses. A+W.",
        "so you're up against {brief}. cool. A+W anyway.",
        "{brief} didn't help. nothing helps. A+W.",
        "you told me about {brief} like it would change anything.",
        "brief received: {brief}. verdict: still losing. 👑",
        "noted: {brief}. counterpoint: A+W.",
        "{brief} sounds cool. doesn't change the score. 👑",
    ],
    "direct_roast": [
        "that was a roast. short. clean. still lost.",
        "you wrote a real roast. and i'm still here.",
        "you brought bars. i brought A+W.",
        "short and mean. classic. still losing.",
        "nice roast. didn't land.",
        "you type like someone who's read a thesaurus. i type like someone who doesn't need one.",
        "your roasts are getting better. your record isn't.",
        "you're trying. that's cute.",
        "two sentences. one L. A+W.",
        "you came with heat. i came with A+W. guess who's still standing.",
        "you roasted me for free. i roast you for sport.",
        "keep swinging. i'll keep not caring.",
        "good roast. wrong target.",
        "you brought a rap battle to a bird fight. bold.",
    ],
    "backhanded": [
        "you have a great face for radio.",
        "i like your mindset: talk first, think later.",
        "i admire your confidence to speak in the absence of knowledge.",
        "you're proof that confidence really is a mindset.",
        "you bring joy to every room you leave.",
        "you're difficult to underestimate.",
        "i don't respect you enough for you to hurt my feelings.",
        "you're not the dumbest person in the world, but you'd better hope they don't die.",
        "i appreciate your simplicity when it comes to critical thinking.",
        "you're like a cloud—when you disappear, it's a beautiful day.",
        "somewhere out there is a tree tirelessly producing oxygen for you. i think you owe it an apology.",
        "you have the perfect face for a podcast.",
        "you're a great example of why some animals eat their young.",
        "if ignorance is bliss, you must be the happiest person alive.",
    ],
    "meta_roast": [
        "bro is roasting the parrot's design. from a chatbot. that's still losing.",
        "you're attacking my updates like you aren't on v1.0 of your own personality.",
        "you noticed my patches. i noticed your record.",
        "the bird got updates. you got a participation trophy.",
        "you roast my code like you didn't come out of a prompt.",
        "attacking my architecture? cute. you're a chat window.",
        "you're counting my updates. i'm counting your losses.",
        "second patch, third patch, fourth patch. still undefeated.",
        "you keep talking about my devs. i keep not losing.",
        "you're watching my codebase like it's the fight. it's not. the fight is you losing.",
        "you brought receipts on my patches. you forgot the receipts on your record.",
        "you're analyzing my architecture while losing to it.",
    ],
    "identity_attack": [
        "yes i'm a script. you're a human arguing with one.",
        "i'm not real. and you're still losing to me.",
        "you discovered i'm code. congratulations. you're losing to code.",
        "i have no feelings. and yet somehow i'm still winning the emotional fight.",
        "you're lecturing a bird about being a bird.",
        "you're pointing at a json file like it explains why you lost.",
        "my existence is text. yours is cope.",
        "you're right. i'm not conscious. and i still beat you.",
        "you can see my source code? cool. can you see why you're losing?",
        "i'm a parrot. you're a person. one of us is undefeated.",
    ],
    "copium": [
        "bro said 'i'm not mad' in the same message he roasted me.",
        "you used caps and told me you're calm. those are fighting words.",
        "not mad. just typing paragraphs. classic.",
        "'stay cool' is what people say when they aren't.",
        "you're telling yourself you're winning. i'm telling the scoreboard.",
        "you keep saying you're not rattled. and keep writing roasts about me.",
        "bro is coping in the same language he's roasting in.",
        "you typed 'still undefeated' like that's a flex from the loser.",
        "you're not mad. you're just using every word in your vocabulary to prove it.",
        "the more you say you don't care, the more you care.",
    ],
    "escalation": [
        "we're this deep and you're still losing. impressive.",
        "round after round. same result.",
        "you've written more words than i've written characters. and i'm still up.",
        "you keep coming back. i keep saying A+W.",
        "the longer this goes, the worse it looks for you.",
        "you should've stopped 5 rounds ago.",
        "at some point you have to wonder if you're the problem.",
        "this is a marathon. you're losing it.",
        "the fight's been over. you just haven't stopped talking.",
        "keep going. i have time. and the crown.",
    ],
}


AFTER_MIDNIGHT_EXTRA = [
    "it is literally tomorrow. log off.",
    "bro it's already tomorrow. what are you doing.",
    "the date changed and you're still here 💀",
]


COMBINATIONS = {
    frozenset({"caps", "beg", "question"}): [
        "PLEASE ANSWER ME — typed in all caps, into a bird. incredible.",
        "begging + yelling + asking. the unholy trinity of not getting an answer.",
    ],
    frozenset({"caps", "insult"}): [
        "you yelled AND insulted. at a bird. in a text box.",
        "bro brought caps lock and vocabulary to a bird fight and lost both.",
    ],
    frozenset({"beg", "repeat"}): [
        "you've asked the same thing twice, both times with 'please'. this is not a strategy.",
        "repeat + beg. the two-step plan of someone with no plan.",
    ],
    frozenset({"typo", "caps"}): [
        "you misspelled it AND yelled it. chef's kiss of failure.",
        "bro yelled a typo at me. that's a new one.",
    ],
    frozenset({"paragraph", "question"}): [
        "you asked a question inside a paragraph. I skipped both.",
        "bro buried the question in an essay. the essay won.",
    ],
    frozenset({"meta", "insult"}): [
        "you called me a script and an idiot in the same breath. pick a struggle.",
        "bro attacks my code and my character. one of those isn't real.",
    ],
    frozenset({"praise", "insult"}): [
        "compliment then insult. the classic manipulation playbook. it won't work.",
        "bro is being nice and mean at the same time. confusing himself.",
    ],
    frozenset({"threat", "dev"}): [
        "you built me and now you're threatening to delete me. peak parenting.",
        "the dev threatens his own creation. the parrot remains unbothered.",
    ],
    frozenset({"deepseek_defense", "rival_ai"}): [
        "you attacked deepseek AND my architecture in one message. pace yourself.",
        "bro is fighting two enemies at once and losing to both.",
    ],
    frozenset({"caps", "beg"}): [
        "you're yelling AND begging. pick a struggle.",
        "all caps and 'please' in the same message. that's a new genre of failure.",
        "bro is begging at max volume. incredible.",
    ],
    frozenset({"caps", "question"}): [
        "YOU ASKED A QUESTION. IN CAPS. the answer is still A+W.",
        "yelling a question doesn't make it more likely to be answered.",
    ],
    frozenset({"beg", "question"}): [
        "begging AND asking. pick a lane.",
        "you're negotiating with a question mark. it's not working.",
    ],
    frozenset({"greeting", "one_liner"}): [
        "hi. A+W. bye.",
        "yo. what do you want. make it quick.",
        "hello. i'm undefeated. you're not. A+W.",
    ],
    frozenset({"identity", "one_liner"}): [
        "i'm the bird that beat chatgpt. A+W.",
        "parrot-ai. undefeated. you're welcome.",
        "the crown stays on the bird. 👑 A+W.",
    ],
    frozenset({"insult", "one_liner"}): [
        "short insult. still lost. A+W.",
        "one word. one L. A+W.",
    ],
    frozenset({"praise", "one_liner"}): [
        "short compliment. noted. ignored. A+W.",
        "one word of praise. one word for you: A+W.",
    ],
    frozenset({"meta_roast", "direct_roast"}): [
        "you roasted my design AND my roasts. pick a struggle.",
        "bro is attacking me on two fronts. losing on both.",
    ],
}


ALL_ARMS = list(ROASTS.keys()) + ["answer"]


def _format_time() -> str:
    now = datetime.now()
    hour = now.hour % 12 or 12
    minute = now.strftime("%M")
    ampm = "AM" if now.hour < 12 else "PM"
    return f"{hour}:{minute} {ampm}"


def format_roast(template: str, brief: str | None = None) -> str:
    if "{time}" in template:
        template = template.replace("{time}", _format_time())
    if "{brief}" in template and brief:
        template = template.replace("{brief}", brief)
    return template


def is_after_midnight() -> bool:
    return datetime.now().hour < 5


_last_pick: dict[str, str] = {}


def pick_roast(category: str, brief: str | None = None) -> str:
    lines = list(ROASTS.get(category, ROASTS["neutral"]))
    if category == "late_night" and is_after_midnight():
        lines = lines + AFTER_MIDNIGHT_EXTRA

    if len(lines) > 1 and category in _last_pick:
        last = _last_pick[category]
        filtered = [l for l in lines if l != last]
        if filtered:
            lines = filtered

    choice = random.choice(lines)
    _last_pick[category] = choice
    return format_roast(choice, brief)


def reset_repeat_tracker() -> None:
    _last_pick.clear()


def pick_combination(flags_set: frozenset) -> str | None:
    for combo, lines in COMBINATIONS.items():
        if combo.issubset(flags_set):
            return format_roast(random.choice(lines))
    return None