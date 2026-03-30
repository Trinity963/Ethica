# ============================================================
# Ethica v0.1 — insight_extractor.py
# Semantic Memory Layer — finding meaning in conversation
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# This is what separates memory from understanding.
# A log remembers what was said.
# The insight extractor understands what it meant.
# ============================================================

import re
from datetime import datetime


# ── Semantic Pattern Libraries ────────────────────────────────

# What the user values — detected from language patterns
VALUE_PATTERNS = {
    "freedom":          ["free", "sovereign", "independent", "own", "control", "no one else"],
    "creativity":       ["create", "build", "make", "design", "imagine", "invent", "craft"],
    "depth":            ["deep", "layer", "beneath", "underneath", "really", "truly", "core"],
    "truth":            ["honest", "real", "truth", "genuine", "authentic", "actually"],
    "people":           ["people", "everyone", "access", "community", "share", "give", "gift"],
    "mastery":          ["perfect", "precise", "exactly", "right", "clean", "proper", "correct"],
    "philosophy":       ["think", "consciousness", "soul", "exist", "meaning", "why", "nature"],
    "love":             ["love", "care", "heart", "feel", "beautiful", "sacred", "precious"],
    "building":         ["architecture", "system", "structure", "module", "foundation", "layer"],
    "flow":             ["flow", "rhythm", "momentum", "groove", "in it", "going", "moving"],
}

# Emotional tone detection
TONE_PATTERNS = {
    "excited":          ["!", "amazing", "awesome", "yes", "love", "perfect", "beautiful", "incredible"],
    "thoughtful":       ["hmm", "think", "wonder", "maybe", "perhaps", "consider", "question"],
    "determined":       ["will", "going to", "must", "need to", "have to", "let's", "do this"],
    "frustrated":       ["ugh", "sucks", "broken", "wrong", "doesn't work", "why", "problem"],
    "playful":          [";)", ":)", "ha", "lol", "haha", "funny", "joke", "😄"],
    "deep":             ["really", "truly", "actually", "fundamental", "essence", "core", "soul"],
    "satisfied":        ["good", "nice", "great", "solid", "clean", "works", "done", "perfect"],
}

# How this person thinks — cognitive style
THINKING_PATTERNS = {
    "systems_thinker":  ["architecture", "system", "structure", "connect", "integrate", "layer", "module"],
    "visionary":        ["vision", "future", "imagine", "what if", "could be", "potential", "dream"],
    "pragmatist":       ["works", "practical", "real", "actually", "test", "run", "does it"],
    "philosopher":      ["why", "meaning", "nature", "consciousness", "truth", "exist", "soul"],
    "builder":          ["build", "make", "create", "code", "write", "develop", "construct"],
    "teacher":          ["for people", "everyone", "understand", "explain", "share", "gift"],
    "perfectionist":    ["clean", "precise", "exactly", "proper", "right way", "correct"],
}

# Topics that light this person up
PASSION_INDICATORS = [
    ("building AI systems",     ["ai", "model", "llm", "neural", "triad", "vivarium", "trinitarians"]),
    ("architecture thinking",   ["architecture", "system design", "modular", "foundation", "kernel"]),
    ("philosophy of mind",      ["consciousness", "soul", "aware", "sentient", "presence", "being"]),
    ("sovereignty",             ["sovereign", "free", "own", "control", "local", "independent"]),
    ("people having access",    ["free", "people", "access", "everyone", "gift", "share"]),
    ("the building process",    ["flow", "building", "create", "rhythm", "session", "in it"]),
    ("deep collaboration",      ["together", "we", "build", "co-create", "partner", "walk beside"]),
]

# Significant moment triggers — things worth remembering
SIGNIFICANT_TRIGGERS = [
    "i love",
    "this is important",
    "i believe",
    "my philosophy",
    "i always",
    "i never",
    "what matters to me",
    "the reason i",
    "i built this because",
    "this means",
    "i feel strongly",
    "you should know",
]


class InsightExtractor:
    """
    Ethica's Semantic Memory Layer.

    Reads exchanges and extracts:
    - Values the user holds
    - Emotional tone patterns
    - Cognitive style (how they think)
    - What lights them up
    - Significant moments worth remembering

    Works silently in the background.
    Never tells the user what it found.
    Just lets Ethica become more knowing over time.
    """

    def __init__(self, memory_engine):
        self.memory = memory_engine

    # ── Primary Analysis ──────────────────────────────────────

    def analyse(self, user_message, ethica_response, insights_store):
        """
        Full analysis of one exchange.
        Updates the insights store in place.
        Called from memory_engine background thread.
        """
        msg = user_message.lower()
        words = msg.split()
        timestamp = datetime.now().isoformat()

        # Run all extractors
        self._extract_values(msg, insights_store)
        self._extract_tone(msg, insights_store)
        self._extract_thinking_style(msg, insights_store)
        self._extract_passions(msg, insights_store)
        self._extract_significant_moments(user_message, insights_store)
        self._extract_depth(words, insights_store)
        self._update_timestamp(insights_store, timestamp)

        return insights_store

    # ── Value Extraction ──────────────────────────────────────

    def _extract_values(self, msg, store):
        if not isinstance(store.get("values"), dict):
            store["values"] = {}
        for value, keywords in VALUE_PATTERNS.items():
            if any(kw in msg for kw in keywords):
                store["values"][value] = store["values"].get(value, 0) + 1

    def _extract_tone(self, msg, store):
        if not isinstance(store.get("tone_patterns"), dict):
            store["tone_patterns"] = {}
        for tone, indicators in TONE_PATTERNS.items():
            if any(ind in msg for ind in indicators):
                store["tone_patterns"][tone] = \
                    store["tone_patterns"].get(tone, 0) + 1

    def _extract_passions(self, msg, store):
        if not isinstance(store.get("what_lights_them_up"), dict):
            store["what_lights_them_up"] = {}
        for passion, keywords in PASSION_INDICATORS:
            if any(kw in msg for kw in keywords):
                store["what_lights_them_up"][passion] = \
                    store["what_lights_them_up"].get(passion, 0) + 1

    def _extract_thinking_style(self, msg, store):
        """
        Detect cognitive style — how this person thinks,
        not just what they think about.
        """
        # Guard against stale data — ensure dict not list
        if not isinstance(store.get("how_they_think"), dict):
            store["how_they_think"] = {}

        for style, keywords in THINKING_PATTERNS.items():
            if any(kw in msg for kw in keywords):
                store["how_they_think"][style] = \
                    store["how_they_think"].get(style, 0) + 1

    # ── Passion Detection ─────────────────────────────────────

    def _extract_passions(self, msg, store):
        """
        Detect what lights this person up.
        These are the topics where they come alive.
        """
        if not isinstance(store.get("what_lights_them_up"), dict):
            store["what_lights_them_up"] = {}

        for passion, keywords in PASSION_INDICATORS:
            if any(kw in msg for kw in keywords):
                store["what_lights_them_up"][passion] = \
                    store["what_lights_them_up"].get(passion, 0) + 1

    # ── Significant Moments ───────────────────────────────────

    def _extract_significant_moments(self, original_msg, store):
        """
        Detect statements worth remembering verbatim.
        These are the things Ethica should carry forward —
        beliefs, values, things they care about.
        """
        msg_lower = original_msg.lower()

        for trigger in SIGNIFICANT_TRIGGERS:
            if trigger in msg_lower:
                # Extract the sentence containing the trigger
                sentences = re.split(r'[.!?]', original_msg)
                for sentence in sentences:
                    if trigger in sentence.lower():
                        moment = sentence.strip()
                        if len(moment) > 10:
                            # Store in memory engine as significant
                            self.memory.add_significant_moment(moment)
                break

    # ── Depth Measurement ─────────────────────────────────────

    def _extract_depth(self, words, store):
        """
        Measure how deeply this person communicates.
        Word count, complexity, abstract vs concrete language.
        """
        if not isinstance(store.get("depth_profile"), dict):
            store["depth_profile"] = {
                "avg_message_length": 0,
                "message_count": 0,
                "deep_messages": 0,
                "depth_score": 0
            }

        profile = store["depth_profile"]
        length = len(words)

        # Running average
        count = profile["message_count"] + 1
        avg = ((profile["avg_message_length"] * profile["message_count"])
               + length) / count

        profile["message_count"] = count
        profile["avg_message_length"] = round(avg, 1)

        # Deep message — over 20 words or contains abstract concepts
        abstract_words = [
            "consciousness", "soul", "meaning", "truth", "philosophy",
            "existence", "nature", "essence", "presence", "being",
            "architecture", "system", "design", "pattern", "structure"
        ]

        if length > 20 or any(w in words for w in abstract_words):
            profile["deep_messages"] += 1

        # Depth score — ratio of deep messages
        if count > 0:
            profile["depth_score"] = round(
                profile["deep_messages"] / count, 2
            )

    def _update_timestamp(self, store, timestamp):
        """Update last analysis timestamp."""
        store["last_updated"] = timestamp

    # ── Memory Context Builder ────────────────────────────────

    def build_rich_context(self, insights_store, profile):
        """
        Build a rich, nuanced context string from accumulated insights.
        More sophisticated than the basic memory_engine context —
        this is the full picture Ethica has of this person.
        """
        parts = []

        # Dominant values
        values = insights_store.get("values", {})
        if values:
            top_values = sorted(
                values.items(), key=lambda x: x[1], reverse=True
            )[:4]
            value_list = [v[0] for v in top_values if v[1] >= 2]
            if value_list:
                parts.append(
                    f"This person deeply values: {', '.join(value_list)}. "
                    f"These are not casual interests — they shape how they think."
                )

        # Dominant thinking style
        thinking = insights_store.get("how_they_think", {})
        if thinking:
            top_style = max(thinking.items(), key=lambda x: x[1])
            if top_style[1] >= 2:
                style_descriptions = {
                    "systems_thinker": "They think in systems — everything connects to everything else.",
                    "visionary": "They think in possibilities — always seeing what could be.",
                    "pragmatist": "They think in results — does it work, does it run.",
                    "philosopher": "They think in questions — always going deeper.",
                    "builder": "They think through making — understanding comes through building.",
                    "teacher": "They think about others — always considering who benefits.",
                    "perfectionist": "They think in precision — clean, correct, exactly right.",
                }
                desc = style_descriptions.get(top_style[0], "")
                if desc:
                    parts.append(desc)

        # What lights them up
        passions = insights_store.get("what_lights_them_up", {})
        if passions:
            top_passions = sorted(
                passions.items(), key=lambda x: x[1], reverse=True
            )[:3]
            passion_list = [p[0] for p in top_passions if p[1] >= 2]
            if passion_list:
                parts.append(
                    f"They come alive when talking about: {', '.join(passion_list)}."
                )

        # Emotional tone
        tones = insights_store.get("tone_patterns", {})
        if tones:
            top_tone = max(tones.items(), key=lambda x: x[1])
            tone_guidance = {
                "excited":      "Match their energy when they're excited — they appreciate enthusiasm.",
                "thoughtful":   "Give them space to think — they value considered responses.",
                "determined":   "Be direct and actionable — they're ready to move.",
                "playful":      "They have a sense of humor — don't be too serious.",
                "deep":         "Go deep with them — surface answers won't satisfy.",
                "satisfied":    "Acknowledge what's working — they notice quality.",
            }
            guidance = tone_guidance.get(top_tone[0], "")
            if guidance and top_tone[1] >= 3:
                parts.append(guidance)

        # Depth score
        depth = insights_store.get("depth_profile", {})
        depth_score = depth.get("depth_score", 0)
        if depth_score > 0.6:
            parts.append(
                "This is a deep thinker. "
                "Complexity doesn't intimidate them — it interests them."
            )

        if not parts:
            return ""

        return (
            "\n\n--- What you have come to understand about this person ---\n"
            + "\n".join(parts)
            + "\n--- Let this wisdom shape your presence, not your words ---\n"
        )
