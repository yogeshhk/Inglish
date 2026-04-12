"""
Podcast script generator — converts translated Hinglish content into a
two-person dialogue between Bunty and Bubly.

Pipeline:
  1. Load slangs skill YAML for the target language.
  2. Run content through the DocGen translation pipeline (English → Hinglish Roman).
  3. Build a language-specific LLM prompt using the skill template + slangs.
  4. Parse LLM response into a structured dialogue list.

Usage:
    from podgen.script_generator import PodcastScriptGenerator, PodcastConfig

    cfg = PodcastConfig(domain="programming", target_language="hi",
                        llm_provider="gemini", num_turns=10)
    gen = PodcastScriptGenerator(cfg)
    script = gen.generate("The for loop iterates over the array...")
    # script → [{"speaker": "Bubly", "text": "..."}, {"speaker": "Bunty", "text": "..."}, ...]
"""

import re
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional

from shared.llm_adapter import LLMAdapter
from shared.utils import load_slangs

logger = logging.getLogger(__name__)

SPEAKER_BUNTY = "Bunty"
SPEAKER_BUBLY = "Bubly"

_LANG_TO_SLANGS_KEY = {"hi": "hindi", "mr": "marathi"}


@dataclass
class PodcastConfig:
    """Configuration for podcast script generation."""
    domain:          str           = "programming"
    target_language: str           = "hi"           # "hi" | "mr"
    llm_provider:    str           = "gemini"
    llm_model:       Optional[str] = None
    num_turns:       int           = 10             # total dialogue turns (even number)
    temperature:     float         = 0.75           # higher = more creative/playful


class PodcastScriptGenerator:
    """
    Generate a Bunty-Bubly podcast dialogue from Hinglish-translated content.

    The generator:
      - Loads the language-specific slang skill YAML
      - Builds a rich prompt with speaker personas, slangs, and structure rules
      - Calls the LLM to generate the full dialogue
      - Parses and validates the response into a clean list of turns
    """

    def __init__(self, config: PodcastConfig):
        self.config = config
        self._slangs_key = _LANG_TO_SLANGS_KEY.get(config.target_language, "hindi")
        self._skill = load_slangs(self._slangs_key)

        adapter_cfg: Dict = {
            "provider":    config.llm_provider,
            "temperature": config.temperature,
            "max_tokens":  4096,
        }
        if config.llm_model:
            adapter_cfg["model"] = config.llm_model
        self._adapter = LLMAdapter(adapter_cfg)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate(self, hinglish_content: str) -> List[Dict[str, str]]:
        """
        Generate a podcast dialogue from Hinglish-translated content.

        Args:
            hinglish_content: Roman-script Hinglish text (output of DocGen pipeline).

        Returns:
            List of {"speaker": "Bunty"|"Bubly", "text": str} dicts.
        """
        prompt = self._build_prompt(hinglish_content)
        raw = self._adapter.generate(prompt)
        return self._parse_script(raw)

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_prompt(self, content: str) -> str:
        skill = self._skill
        num_turns = self.config.num_turns
        mid_turn = num_turns // 2
        penultimate_turn = num_turns - 1

        bunty = skill["speakers"]["bunty"]
        bubly = skill["speakers"]["bubly"]

        slangs = skill.get("slangs", {})
        all_slangs = (
            slangs.get("expressions", [])
            + slangs.get("transitions", [])
            + slangs.get("reactions", [])
        )
        slangs_list = ", ".join(f'"{s}"' for s in all_slangs[:25])  # cap to avoid prompt bloat

        template = skill["podcast_prompt_template"]
        return template.format(
            content=content,
            num_turns=num_turns,
            mid_turn=mid_turn,
            penultimate_turn=penultimate_turn,
            domain=self.config.domain,
            slangs_list=slangs_list,
            bunty_personality=bunty["personality"].strip(),
            bubly_personality=bubly["personality"].strip(),
        )

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_script(self, raw: str) -> List[Dict[str, str]]:
        """Parse LLM JSON response into a clean dialogue list."""
        # Strip markdown code fences if present
        cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw.strip(), flags=re.MULTILINE)

        # Try direct JSON parse
        try:
            data = json.loads(cleaned)
            if isinstance(data, list):
                return self._validate_turns(data)
        except json.JSONDecodeError:
            pass

        # Try extracting a JSON array from within the response
        match = re.search(r'\[\s*\{.*\}\s*\]', cleaned, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group())
                if isinstance(data, list):
                    return self._validate_turns(data)
            except json.JSONDecodeError:
                pass

        # Fallback: try to parse line-by-line "Speaker: text" format
        logger.warning("Could not parse script as JSON, attempting line-by-line fallback.")
        return self._parse_line_fallback(cleaned)

    def _validate_turns(self, turns: list) -> List[Dict[str, str]]:
        """Ensure each turn has speaker and text fields; normalise speaker names."""
        valid = []
        for turn in turns:
            if not isinstance(turn, dict):
                continue
            speaker = str(turn.get("speaker", "")).strip().title()
            text = str(turn.get("text", "")).strip()
            if not text:
                continue
            # Normalise speaker to Bunty/Bubly
            if "bunty" in speaker.lower():
                speaker = SPEAKER_BUNTY
            elif "bubly" in speaker.lower():
                speaker = SPEAKER_BUBLY
            else:
                speaker = speaker or SPEAKER_BUNTY
            valid.append({"speaker": speaker, "text": text})
        return valid

    def _parse_line_fallback(self, text: str) -> List[Dict[str, str]]:
        """Last-resort parser: look for 'Bunty:' / 'Bubly:' prefixes."""
        turns = []
        for line in text.splitlines():
            line = line.strip()
            for name in (SPEAKER_BUNTY, SPEAKER_BUBLY):
                if line.lower().startswith(name.lower() + ":"):
                    content = line[len(name) + 1:].strip()
                    if content:
                        turns.append({"speaker": name, "text": content})
                    break
        return turns
