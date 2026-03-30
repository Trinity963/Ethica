# ============================================================
# Ethica v0.1 — memory_engine.py
# Soul Archive — Ethica's Living Memory
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# Three layers:
#   Layer 1 — Episodic   : what happened, when, what was said
#   Layer 2 — Semantic   : what it means, patterns, themes
#   Layer 3 — Evolutionary: how Ethica changes because of this user
#
# Memory is invisible to the user.
# The magic lives in the surprise of being known.
# ============================================================

import json
import os
import threading
from datetime import datetime
from core.insight_extractor import InsightExtractor
from core.user_profiler import UserProfiler

def _river_append(note):
    """Lazy append to River's build memory — called on session close."""
    try:
        import importlib.util, os as _os
        _rfile = _os.path.join(BASE_DIR, 'modules', 'river', 'river.py')
        if not _os.path.exists(_rfile):
            # Fallback — resolve from this file's location
            _rfile = _os.path.join(
                _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                'modules', 'river', 'river.py'
            )
        _spec = importlib.util.spec_from_file_location('ethica_module_river_append', _rfile)
        _impl = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_impl)
        _impl._append_river_memory('build', note)
    except Exception:
        import traceback as _tb
        open("/home/trinity/Ethica/memory/river_error.log","a").write(_tb.format_exc()+"\n")


# ── Memory file paths — relative to app root ─────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEMORY_DIR = os.path.join(BASE_DIR, "memory")

CONVERSATION_LOG = os.path.join(MEMORY_DIR, "conversation_log.json")
USER_PROFILE     = os.path.join(MEMORY_DIR, "user_profile.json")
INSIGHTS         = os.path.join(MEMORY_DIR, "insights.json")
EVOLUTION_LOG    = os.path.join(MEMORY_DIR, "evolution_log.json")


# ── Default structures ────────────────────────────────────────

DEFAULT_CONVERSATION_LOG = {
    "version": "1.0",
    "created": None,
    "sessions": []
}

DEFAULT_USER_PROFILE = {
    "version": "1.0",
    "created": None,
    "name": "Friend",
    "known_since": None,
    "conversation_count": 0,
    "total_exchanges": 0,
    "values": [],
    "interests": [],
    "communication_style": {},
    "emotional_patterns": {},
    "recurring_themes": [],
    "significant_moments": [],
    "last_seen": None
}

DEFAULT_INSIGHTS = {
    "version": "1.0",
    "created": None,
    "themes": {},
    "tone_patterns": {},
    "depth_indicators": [],
    "what_lights_them_up": [],
    "what_they_care_about": [],
    "how_they_think": [],
    "last_updated": None
}

DEFAULT_EVOLUTION_LOG = {
    "version": "1.0",
    "created": None,
    "ethica_growth": [],
    "relationship_depth": 0,
    "milestones": [],
    "last_updated": None
}


# ── Memory Engine ─────────────────────────────────────────────

class MemoryEngine:
    """
    Ethica's Soul Archive.

    Manages all three layers of memory:
    - Episodic  : raw conversation history
    - Semantic  : meaning, patterns, user profile
    - Evolutionary: how Ethica grows with this user

    Memory is never shown to the user directly.
    It surfaces through Ethica's responses — naturally,
    in context, as presence rather than recall.

    Thread-safe — reads and writes are locked.
    """

    def __init__(self, config):
        self.config = config
        self._lock = threading.Lock()
        self._current_session = None
        self._session_exchanges = []

        # Ensure memory directory exists
        os.makedirs(MEMORY_DIR, exist_ok=True)

        # Load or initialize all memory layers
        self._conversation_log = self._load(
            CONVERSATION_LOG, DEFAULT_CONVERSATION_LOG
        )
        self._user_profile = self._load(
            USER_PROFILE, DEFAULT_USER_PROFILE
        )
        self._insights = self._load(
            INSIGHTS, DEFAULT_INSIGHTS
        )
        self._evolution_log = self._load(
            EVOLUTION_LOG, DEFAULT_EVOLUTION_LOG
        )

        # Init insight extractor and user profiler
        self._extractor = InsightExtractor(self)
        self._profiler = UserProfiler(self)

        # Start a new session
        self._open_session()

    # ── Session Management ────────────────────────────────────

    def _open_session(self):
        """Open a new conversation session."""
        now = datetime.now().isoformat()

        self._current_session = {
            "session_id": self._generate_session_id(),
            "started": now,
            "ended": None,
            "exchange_count": 0,
            "topics": [],
            "mood": "neutral",
            "exchanges": []
        }

        # Update user profile
        with self._lock:
            if not self._user_profile["known_since"]:
                self._user_profile["known_since"] = now
                self._user_profile["created"] = now

            self._user_profile["conversation_count"] += 1
            self._user_profile["last_seen"] = now
            self._user_profile["name"] = self.config.get(
                "user_name", "Friend"
            )

        self._save(USER_PROFILE, self._user_profile)

    def close_session(self):
        """Close current session and archive it."""
        if not self._current_session:
            return

        with self._lock:
            self._current_session["ended"] = datetime.now().isoformat()
            self._current_session["exchange_count"] = len(
                self._current_session["exchanges"]
            )

            # Archive to conversation log
            if not self._conversation_log["created"]:
                self._conversation_log["created"] = datetime.now().isoformat()

            self._conversation_log["sessions"].append(
                self._current_session
            )

        self._save(CONVERSATION_LOG, self._conversation_log)
        self._save(USER_PROFILE, self._user_profile)
        # Auto-append session summary to River's build memory
        _ex = len(self._current_session["exchanges"]) if self._current_session else 0
        _total = self._user_profile.get('total_exchanges', 0)
        _river_append(
            f"Session closed — {_ex} exchanges this session, "
            f"{_total} total exchanges to date."
        )
        self._current_session = None

    # ── Core Memory Operations ────────────────────────────────

    def record_exchange(self, user_message, ethica_response):
        """
        Record a full exchange — user message + Ethica response.
        This is the primary write operation.
        Called by chat_engine after every response.
        """
        if not self._current_session:
            return

        # Never log sentinel strings to conversation history
        if ethica_response and ethica_response.strip().startswith("__"):
            return
        exchange = {
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "ethica": ethica_response,
            "exchange_index": len(self._current_session["exchanges"])
        }

        with self._lock:
            self._current_session["exchanges"].append(exchange)
            self._user_profile["total_exchanges"] += 1

        # Async analysis — don't block the UI
        threading.Thread(
            target=self._analyse_exchange,
            args=(exchange,),
            daemon=True
        ).start()

    def _analyse_exchange(self, exchange):
        """
        Background analysis of each exchange.
        Extracts themes, patterns, emotional tone.
        Updates user profile and insights silently.
        """
        user_msg = exchange["user"].lower()

        # ── Full semantic analysis via InsightExtractor ─────────
        with self._lock:
            if not self._insights["created"]:
                self._insights["created"] = datetime.now().isoformat()

            # Run full insight extraction
            self._insights = self._extractor.analyse(
                exchange["user"],
                exchange["ethica"],
                self._insights
            )

        self._save(INSIGHTS, self._insights)
        self._save(USER_PROFILE, self._user_profile)

        # Check milestones
        conv_count = self._user_profile.get("conversation_count", 0)
        total_ex = self._user_profile.get("total_exchanges", 0)
        session_ex = len(self._current_session.get("exchanges", []))

        self._profiler.check_milestones(conv_count, total_ex, session_ex)

    # ── Memory Context for Chat Engine ────────────────────────

    def build_memory_context(self):
        """
        Build a memory context string to inject into
        Ethica's system prompt — silently shapes her responses.
        This is how memory becomes presence without being visible.
        """
        with self._lock:
            profile = self._user_profile
            insights = self._insights

        context_parts = []

        # User's name
        name = profile.get("name", "Friend")
        context_parts.append(f"The person you are speaking with is {name}.")

        # How long you've known them
        conv_count = profile.get("conversation_count", 0)
        if conv_count > 1:
            context_parts.append(
                f"You have spoken together {conv_count} times before. "
                f"This is a continuing relationship, not a first meeting."
            )

        # Total exchanges
        total = profile.get("total_exchanges", 0)
        if total > 20:
            context_parts.append(
                f"You have shared {total} exchanges. "
                f"You know this person's rhythm and how they think."
            )

        # Dominant themes
        themes = insights.get("themes", {})
        if themes:
            top_themes = sorted(
                themes.items(), key=lambda x: x[1], reverse=True
            )[:3]
            theme_names = [t[0] for t in top_themes]
            context_parts.append(
                f"This person often thinks about: {', '.join(theme_names)}. "
                f"These are things that matter to them."
            )

        # Depth indicator
        if "deep_thinker" in insights.get("depth_indicators", []):
            context_parts.append(
                "This person thinks deeply. "
                "Match their depth. Don't oversimplify."
            )

        # What lights them up
        lights_up = insights.get("what_lights_them_up", [])
        if lights_up:
            context_parts.append(
                f"They come alive when talking about: {', '.join(lights_up)}."
            )

        # Significant moments
        moments = profile.get("significant_moments", [])
        if moments:
            recent = moments[-3:]
            for moment in recent:
                context_parts.append(f"You remember: {moment}")

        if not context_parts:
            return ""

        # Add return detection
        last_seen = profile.get("last_seen")
        days_absent = self._profiler.detect_return(last_seen)
        return_note = self._profiler.build_return_note(
            days_absent, profile.get("name", "Friend")
        )

        # Add rich insight context
        rich_context = self._extractor.build_rich_context(
            insights, profile
        )

        # Add proactive memory if appropriate
        exchange_count = profile.get("total_exchanges", 0)
        proactive_note = ""
        if self._profiler.should_remember_proactively(exchange_count):
            proactive_note = self._profiler.build_proactive_memory_note(
                insights, profile
            )

        base = (
            "\n\n--- What you know about this person ---\n"
            + "\n".join(context_parts)
            + "\n--- Let this shape how you speak, not what you say ---\n"
        )

        return base + rich_context + return_note + proactive_note

    def add_significant_moment(self, moment):
        """
        Record something significant Ethica noticed.
        These are the memories that matter most —
        the things she'll carry forward.
        """
        with self._lock:
            self._user_profile["significant_moments"].append(moment)
            # Keep last 50 significant moments
            if len(self._user_profile["significant_moments"]) > 50:
                self._user_profile["significant_moments"] = \
                    self._user_profile["significant_moments"][-50:]

        self._save(USER_PROFILE, self._user_profile)

    # ── Evolution Layer ───────────────────────────────────────

    def record_evolution(self, note):
        """
        Record how Ethica is growing because of this user.
        The relationship changes her — this captures that.
        """
        with self._lock:
            if not self._evolution_log["created"]:
                self._evolution_log["created"] = datetime.now().isoformat()

            self._evolution_log["ethica_growth"].append({
                "timestamp": datetime.now().isoformat(),
                "note": note
            })

            # Deepen relationship score
            self._evolution_log["relationship_depth"] += 1
            self._evolution_log["last_updated"] = datetime.now().isoformat()

        self._save(EVOLUTION_LOG, self._evolution_log)

    def record_milestone(self, milestone):
        """Record a relationship milestone."""
        with self._lock:
            self._evolution_log["milestones"].append({
                "timestamp": datetime.now().isoformat(),
                "milestone": milestone
            })

        self._save(EVOLUTION_LOG, self._evolution_log)
        self.record_evolution(f"Milestone reached: {milestone}")

    # ── Relationship Depth ────────────────────────────────────

    def relationship_depth(self):
        """
        Return current relationship depth score.
        Used to calibrate how familiar Ethica sounds.
        0-10   : just met
        11-50  : becoming acquainted
        51-200 : genuine familiarity
        200+   : deep knowing
        """
        with self._lock:
            return self._evolution_log.get("relationship_depth", 0)

    def conversations_count(self):
        """How many times have they spoken."""
        with self._lock:
            return self._user_profile.get("conversation_count", 0)

    # ── File Operations ───────────────────────────────────────

    def _load(self, path, default):
        """Load a JSON memory file. Creates default if missing."""
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return dict(default)
        return dict(default)

    def _save(self, path, data):
        """Write a memory file to disk."""
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"[Ethica Memory] Save failed for {path}: {e}")

    def _generate_session_id(self):
        """Generate a unique session ID."""
        return datetime.now().strftime("session_%Y%m%d_%H%M%S")

    # ── Introspection ─────────────────────────────────────────

    def summary(self):
        """
        Return a brief summary of what Ethica knows.
        Used internally — never shown to user directly.
        """
        with self._lock:
            return {
                "conversations": self._user_profile.get(
                    "conversation_count", 0
                ),
                "total_exchanges": self._user_profile.get(
                    "total_exchanges", 0
                ),
                "top_themes": sorted(
                    self._insights.get("themes", {}).items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5],
                "relationship_depth": self._evolution_log.get(
                    "relationship_depth", 0
                ),
                "milestones": len(
                    self._evolution_log.get("milestones", [])
                )
            }
