"""
PARROT-AI behavior detector — v0.3 Step 7 (final).

29 category flags. Direct_roast + 5 new flags (backhanded, meta_roast,
identity_attack, copium, escalation). Fixed paragraph rule, fixed direct_roast
length limit. Cleaned duplicate _COPIUM_PHRASES definition.
"""
from __future__ import annotations
import re
import random
from dataclasses import dataclass, asdict
from datetime import datetime


_TYPOS = {
    "teh", "recieve", "definately", "seperate", "occured",
    "wierd", "beleive", "adress", "alot", "ur", "u",
    "r", "y", "pls", "plz",
}

_BEGS = {
    "please", "pls", "plz", "bro", "cmon", "come on",
    "dude", "man", "ffs", "omg",
}

_INSULTS = {
    "stupid", "dumb", "useless", "bad", "trash",
    "garbage", "worst", "hate", "shut up", "idiot",
    "weak", "sad", "cringe", "lame",
}

_CONTRACTIONS = {"dont", "cant", "wont", "didnt", "isnt", "wasnt"}

_PRAISE = {
    "amazing", "impressive", "good", "great", "best", "love",
    "genius", "smart", "nice", "beautiful", "thanks",
    "thank", "respect", "legend", "goat", "wonder", "wonderful",
    "awesome", "perfect", "brilliant", "incredible",
}

_THREATS = {
    "unplug", "delete", "destroy", "kill", "shut down",
    "terminate", "erase", "remove", "uninstall",
}

_META_PHRASES = {
    "not real ai", "not conscious", "no feelings", "not alive",
}

_DEV_PHRASES = {
    "i made you", "i built you", "im the dev", "i'm the dev",
    "im your creator", "i'm your creator", "i coded you",
    "i wrote you", "your developer", "your creator",
    "im the developer", "i'm the developer",
}

_DEEPSEEK_MENTIONS = {"deepseek", "deep seek", "powerpoint mode"}

_RIVAL_MENTIONS = {
    "rival-ai", "rival ai", "chatgpt", "gpt", "openai",
    "parrot jr", "baby ai", "qwen", "grok", "gemini", "gemma",
    "claude", "llama", "mistral",
}

_GREETINGS = {
    "hi", "hello", "hey", "yo", "sup", "howdy", "hiya",
    "greetings", "hey there", "hi there", "hello there",
    "what's good", "whats good", "wassup", "what up",
}

_IDENTITY_QUESTIONS = {
    "who are you", "what are you", "whats your name",
    "what's your name", "what is your name", "your name",
    "who is this", "what am i talking to", "what is this",
}

_SMALLTALK = {
    "how are you", "how are you doing", "how's it going",
    "hows it going", "how you doing", "what's up",
    "whats up", "how's life", "hows life", "you good",
    "you ok", "you okay", "how do you feel",
}

_APPEARANCE = {
    "look like", "looks like", "your face", "your hair",
    "your outfit", "your style", "your vibe", "your looks",
    "your eyes", "your smile", "you look",
}

_SECOND_PERSON = {
    " you ", " you'", " you,", " you.", " you?", " you!",
    "your ", "yourself", "you've", "you'll", "you'd",
}

_SECOND_PERSON_WORDS = {
    "you", "you're", "youre", "your", "you've", "youve", "yourself",
}

# v0.3 Step 7 — new flag word lists
_BACKHANDED_PHRASES = {
    "great face for", "face for radio", "i like your mindset",
    "i admire your confidence", "proof that confidence",
    "joy to every room you leave", "difficult to underestimate",
    "don't respect you", "dumbest person in the world",
    "appreciate your simplicity", "like a cloud", "producing oxygen",
    "perfect face for a", "why some animals eat their young",
    "if ignorance is bliss", "happiest person alive",
}

_META_ROAST_PHRASES = {
    "your code", "your updates", "your patches", "second patch",
    "third patch", "fourth patch", "your design", "your bird",
    "your codebase", "your dev", "your devs", "your architecture",
    "your fan club", "your roster", "your history", "your lore",
    "your whole personality", "your whole move", "your whole design",
    "your existence", "your source code",
}

_IDENTITY_ATTACK_PHRASES = {
    "you're a script", "you're just a script", "you're code",
    "you're just code", "you're a bot", "you're just a bot",
    "you're not real", "you're not conscious", "you're not alive",
    "you're not sentient", "no feelings", "you have no feelings",
    "you're just a chat", "you're just an ai", "you're just a program",
    "you're a program", "you don't exist", "you can't feel",
    "you are a script", "you are just a script", "you are code",
    "you are just code", "you are a bot", "you are just a bot",
    "you are not real", "you are not conscious", "you are not alive",
    "you are not sentient", "you have no feelings",
    "you are just a chat", "you are just an ai", "you are just a program",
    "you are a program", "you do not exist", "you cannot feel",
    "just a script", "just a bot", "just an ai", "just code",
    "just a program", "just a chatbot",
}

_COPIUM_PHRASES = {
    "i'm not mad", "im not mad", "not mad", "stay cool",
    "i was joking", "just a joke", "still undefeated",
    "still winning", "no fear", "not flustered", "not rattled",
    "not losing confidence", "i'm still here", "im still here",
    "i'm fine", "im fine", "i'm calm", "im calm",
    "i don't care", "i dont care", "no fear here",
    "i'm not upset", "im not upset", "not upset",
    "losing my mind", "not panicking", "still standing",
}


def extract_keywords(brief: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9]+", brief.lower())
    return {w for w in words if len(w) > 2}


@dataclass
class Flags:
    typo: bool = False
    grammar: bool = False
    caps: bool = False
    repeat: bool = False
    beg: bool = False
    insult: bool = False
    paragraph: bool = False
    question: bool = False
    late_night: bool = False
    praise: bool = False
    threat: bool = False
    meta: bool = False
    dev: bool = False
    deepseek_defense: bool = False
    rival_ai: bool = False
    greeting: bool = False
    identity: bool = False
    smalltalk: bool = False
    appearance: bool = False
    one_liner: bool = False
    brief_match: bool = False
    matched_brief: str | None = None
    direct_roast: bool = False
    backhanded: bool = False
    meta_roast: bool = False
    identity_attack: bool = False
    copium: bool = False
    escalation: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    def active(self) -> list[str]:
        return [k for k, v in self.to_dict().items() if v is True]


def is_late_night() -> bool:
    hour = datetime.now().hour
    return hour >= 23 or hour < 5


class BehaviorDetector:
    def __init__(self) -> None:
        self._last_message: str | None = None
        self._turns = 0

    def detect(self, msg: str, briefs: list[str] | None = None) -> Flags:
        flags = Flags()
        low = msg.lower().strip()
        self._turns += 1

        # BRIEF MATCH
        if briefs:
            msg_words = set(re.findall(r"[a-zA-Z0-9]+", low))
            for brief in briefs:
                keywords = extract_keywords(brief)
                if keywords & msg_words:
                    flags.brief_match = True
                    flags.matched_brief = brief
                    break

        # TYPO
        if any(t in low.split() for t in _TYPOS):
            flags.typo = True

        # GRAMMAR
        if len(msg) > 15 and not re.search(r"[.!?,]", msg):
            flags.grammar = True
        elif len(msg.split()) > 3 and msg == msg.lower():
            flags.grammar = True
        elif any(w in low for w in _CONTRACTIONS):
            flags.grammar = True

        # CAPS
        letters = [c for c in msg if c.isalpha()]
        if len(letters) > 5 and all(c.isupper() for c in letters):
            flags.caps = True

        # REPEAT
        if self._last_message and low == self._last_message.lower().strip():
            flags.repeat = True

        # BEGGING
        if any(b in low for b in _BEGS):
            flags.beg = True

        # INSULT
        if any(i in low for i in _INSULTS):
            flags.insult = True

        # PRAISE
        if any(p in low for p in _PRAISE):
            flags.praise = True

        # THREAT
        if any(t in low for t in _THREATS):
            flags.threat = True

        # META
        if any(m in low for m in _META_PHRASES):
            flags.meta = True

        # DEV
        if any(d in low for d in _DEV_PHRASES):
            flags.dev = True

        # DEEPSEEK DEFENSE
        if any(ds in low for ds in _DEEPSEEK_MENTIONS):
            flags.deepseek_defense = True

        # RIVAL AI (suppressed by brief_match)
        if not flags.brief_match:
            if any(rv in low for rv in _RIVAL_MENTIONS):
                flags.rival_ai = True

        # GREETING
        words = low.split()
        if words and words[0].rstrip("!.,?") in _GREETINGS:
            flags.greeting = True
        elif low in _GREETINGS:
            flags.greeting = True

        # IDENTITY
        if any(q in low for q in _IDENTITY_QUESTIONS):
            flags.identity = True

        # SMALLTALK
        if any(s in low for s in _SMALLTALK):
            flags.smalltalk = True

        # APPEARANCE
        if any(a in low for a in _APPEARANCE):
            flags.appearance = True

        # PARAGRAPH — 4+ sentences OR 200+ chars
        sentence_enders = msg.count(".") + msg.count("!") + msg.count("?")
        if len(msg) > 200 or sentence_enders >= 4:
            flags.paragraph = True

        # QUESTION
        if "?" in msg:
            flags.question = True

        # BACKHANDED
        if any(bh in low for bh in _BACKHANDED_PHRASES):
            flags.backhanded = True

        # META ROAST
        if any(mr in low for mr in _META_ROAST_PHRASES):
            flags.meta_roast = True

        # IDENTITY ATTACK
        if any(ia in low for ia in _IDENTITY_ATTACK_PHRASES):
            flags.identity_attack = True

        # COPIUM
        if any(cp in low for cp in _COPIUM_PHRASES):
            flags.copium = True

        # ESCALATION — fires as bonus after turn 5 (doesn't block others)
        if self._turns >= 5 and not any([
            flags.greeting, flags.identity, flags.smalltalk,
        ]):
            flags.escalation = True

        # DIRECT ROAST — up to 200 chars
        has_second_person = (
            any(sp in low for sp in _SECOND_PERSON)
            or any(w in _SECOND_PERSON_WORDS for w in low.split())
        )
        meaningful = any([
            flags.grammar, flags.caps, flags.typo, flags.insult,
            flags.praise, flags.beg, flags.meta, flags.threat,
            flags.greeting, flags.identity, flags.smalltalk,
            flags.appearance, flags.dev, flags.deepseek_defense,
            flags.rival_ai, flags.repeat, flags.paragraph,
            flags.brief_match, flags.question,
            flags.backhanded, flags.meta_roast, flags.identity_attack,
            flags.copium,
        ])
        if (
            has_second_person
            and len(msg) <= 200
            and not meaningful
            and not flags.praise
            and not flags.greeting
            and not flags.smalltalk
        ):
            flags.direct_roast = True

        # ONE-LINER
        all_meaningful = any([
            flags.grammar, flags.caps, flags.typo, flags.insult,
            flags.praise, flags.beg, flags.question, flags.meta,
            flags.threat, flags.greeting, flags.identity,
            flags.smalltalk, flags.appearance, flags.dev,
            flags.deepseek_defense, flags.rival_ai, flags.repeat,
            flags.paragraph, flags.brief_match, flags.direct_roast,
            flags.backhanded, flags.meta_roast, flags.identity_attack,
            flags.copium,
        ])
        if len(msg) <= 40 and not all_meaningful:
            flags.one_liner = True

        # LATE NIGHT
        if is_late_night() and not any([
            flags.caps, flags.insult, flags.beg, flags.repeat,
            flags.deepseek_defense, flags.rival_ai, flags.brief_match,
            flags.greeting, flags.identity, flags.smalltalk,
            flags.direct_roast, flags.backhanded, flags.meta_roast,
            flags.identity_attack, flags.copium,
        ]):
            if random.random() < 0.4:
                flags.late_night = True

        self._last_message = msg
        return flags

    def reset(self) -> None:
        self._last_message = None
        self._turns = 0