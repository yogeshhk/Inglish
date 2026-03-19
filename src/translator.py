"""
Translation module — translates bracketed English text to Indian languages.

Uses LLMAdapter so any supported LLM provider can be used transparently.
The translator receives text with [bracketed technical terms] and must keep
those brackets (and their content) unchanged in its output.
"""

import re
import json
import logging
from typing import Dict, Optional
from abc import ABC, abstractmethod

from llm_adapter import LLMAdapter

logger = logging.getLogger(__name__)


class BaseTranslator(ABC):
    """Abstract base for all translator implementations."""

    def __init__(self, target_language: str = "hi"):
        self.target_language = target_language

    @abstractmethod
    def translate(self, text: str) -> Dict[str, str]:
        """
        Translate bracketed English text.

        Args:
            text: English text with [bracketed] technical terms.

        Returns:
            {"roman": <Roman script>, "devanagari": <Devanagari script>}
        """

    def validate_constraints(self, original: str, translated: str) -> bool:
        """Check that every [bracketed term] in original appears in translated."""
        return sorted(re.findall(r'\[([^\]]+)\]', original)) == \
               sorted(re.findall(r'\[([^\]]+)\]', translated))

    def unguard_terms(self, text: str) -> str:
        """Strip square brackets while keeping the term text."""
        return re.sub(r'\[([^\]]+)\]', r'\1', text)


class LLMTranslator(BaseTranslator):
    """
    LLM-based translator.

    Translates only non-bracketed text while preserving [bracketed terms].
    Returns both Roman (Hinglish) and Devanagari outputs.

    Provider-agnostic: uses LLMAdapter so provider is configured externally.
    """

    # Human-readable names for prompt construction
    _LANG_NAMES   = {"hi": "Hindi",   "mr": "Marathi"}
    _LANG_SCRIPTS = {"hi": "Devanagari", "mr": "Devanagari"}

    def __init__(
        self,
        target_language: str = "hi",
        llm_provider: str = "gemini",
        llm_model: Optional[str] = None,
        temperature: float = 0.3,
    ):
        super().__init__(target_language)
        adapter_config: Dict = {
            "provider":    llm_provider,
            "temperature": temperature,
            "max_tokens":  1024,
        }
        if llm_model:
            adapter_config["model"] = llm_model
        self._adapter = LLMAdapter(adapter_config)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def translate(self, text: str) -> Dict[str, str]:
        """
        Translate bracketed English text to the configured target language.

        Raises the underlying exception so callers can see exactly what went wrong.
        Wrap in try/except at the pipeline level if you want a graceful fallback.
        """
        prompt = self._build_prompt(text)
        raw = self._adapter.generate(prompt)
        return self._parse_response(raw, fallback=text)

    # ------------------------------------------------------------------
    # Prompt construction
    # ------------------------------------------------------------------

    def _build_prompt(self, text: str) -> str:
        lang   = self._LANG_NAMES.get(self.target_language, "Hindi")
        script = self._LANG_SCRIPTS.get(self.target_language, "Devanagari")
        examples = self._few_shot_examples()

        marathi_rule = (
            "\n- CRITICAL FOR MARATHI: Use 'ahe/ahet' (not 'hai/hain'), "
            "'karte' (not 'karta hai'), 'cha/chi/che' (not 'ke'), "
            "'la' (not 'ko'), 'vpar' (not 'par/upar')."
            if self.target_language == "mr" else ""
        )

        return f"""You are an expert technical translator from English to {lang}.

TASK: Translate the input English sentence to {lang}.

RULES (follow all strictly):
1. Any text inside [square brackets] MUST appear UNCHANGED (with brackets) in your output.
   Do NOT translate, remove, or modify bracketed content.
2. Translate ONLY the non-bracketed English words to {lang}.
3. Use natural {lang} grammar (SOV word order, correct postpositions, gender agreement).
4. Output a JSON object with exactly two keys:
   - "roman": Roman-script {lang} translation. Keep ALL [brackets] as-is.
   - "devanagari": {script}-script translation. Keep ALL [brackets] as-is.
     Every non-bracketed word MUST be in {script} script — including verbs like iterate, compile, return etc.
     Do NOT leave any Roman/Latin words outside of brackets in the devanagari field.{marathi_rule}

EXAMPLES:
{examples}

Input: "{text}"
Output:"""

    def _few_shot_examples(self) -> str:
        if self.target_language == "mr":
            return '''\
Input: "The [for loop] iterates over the [array]."
Output: {"roman": "[for loop] [array] cha vpar iterate karte", "devanagari": "[फॉर लूप] [ऐरे] च्या वर इटरेट करते"}

Input: "This [class] has four [member variables]."
Output: {"roman": "hi [class] char [member variables] ahe", "devanagari": "ही [क्लास] चार [मेंबर व्हेरिएबल्स] आहे"}

Input: "The [function] returns a [boolean] value."
Output: {"roman": "[function] ek [boolean] value return karte", "devanagari": "[फंक्शन] एक [बूलियन] व्हैल्यू रिटर्न करते"}

Input: "The [while loop] continues until the [condition] is false."
Output: {"roman": "[while loop] tab tak chalta rahta jab tak [condition] false nahi hoti", "devanagari": "[व्हाइल लूप] तब तक चलता रहता जब तक [कंडीशन] फॉल्स नहीं होती"}'''
        else:  # Hindi default
            return '''\
Input: "The [for loop] iterates over the [array]."
Output: {"roman": "[for loop] [array] ke upar iterate karta hai", "devanagari": "[फॉर लूप] [ऐरे] के ऊपर इटरेट करता है"}

Input: "This [class] has four [member variables]."
Output: {"roman": "is [class] mein chaar [member variables] hain", "devanagari": "इस [क्लास] में चार [मेंबर व्हेरिएबल्स] हैं"}

Input: "Each [object] has its own [instance variables]."
Output: {"roman": "har [object] ke apne [instance variables] hote hain", "devanagari": "हर [ऑब्जेक्ट] के अपने [इन्स्टेंस व्हेरिएबल्स] होते हैं"}

Input: "The [function] returns a [boolean] value."
Output: {"roman": "[function] ek [boolean] value return karta hai", "devanagari": "[फंक्शन] एक [बूलियन] वैल्यू रिटर्न करता है"}

Input: "The [while loop] continues until the [condition] is false."
Output: {"roman": "[while loop] tab tak chalta rahta hai jab tak [condition] false nahi hoti", "devanagari": "[व्हाइल लूप] तब तक चलता रहता है जब तक [कंडीशन] फॉल्स नहीं होती"}

Input: "Call the [function] with two [arguments]."
Output: {"roman": "[function] ko do [arguments] ke saath call karo", "devanagari": "[फंक्शन] को दो [आर्ग्युमेंट्स] के साथ कॉल करो"}'''

    # ------------------------------------------------------------------
    # Response parsing
    # ------------------------------------------------------------------

    def _parse_response(self, raw: str, fallback: str) -> Dict[str, str]:
        """Parse LLM JSON response; return fallback if parsing fails."""
        # Strip markdown fences if present
        cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw.strip())
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Try extracting a JSON object from the string
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                try:
                    data = json.loads(match.group())
                except json.JSONDecodeError:
                    logger.warning("Could not parse LLM response as JSON: %s", raw[:200])
                    plain = self.unguard_terms(fallback)
                    return {"roman": plain, "devanagari": plain}
            else:
                plain = self.unguard_terms(fallback)
                return {"roman": plain, "devanagari": plain}

        roman      = str(data.get("roman",      fallback)).strip()
        devanagari = str(data.get("devanagari", fallback)).strip()

        # Warn if constraints are broken, but still return what we got
        if not self.validate_constraints(fallback, roman):
            logger.warning("Bracketed terms may not be fully preserved in Roman output.")

        # Strip brackets for final output
        return {
            "roman":      self.unguard_terms(roman),
            "devanagari": self.unguard_terms(devanagari),
        }
