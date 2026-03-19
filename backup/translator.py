"""Translation module using Groq LLM for English to Indian languages."""

import re
import sys
import json
from typing import Dict, Optional
from abc import ABC, abstractmethod


class BaseTranslator(ABC):
    """Abstract base class for translators."""

    def __init__(self, target_language: str = "hi"):
        self.target_language = target_language

    @abstractmethod
    def translate(self, text: str) -> Dict[str, str]:
        """Translate bracketed text to target language. Returns dict with roman and devanagari outputs."""
        pass

    def validate_constraints(self, original: str, translated_roman: str) -> bool:
        """Verify that bracketed terms are preserved in Roman output."""
        original_terms = sorted(re.findall(r'\[([^\]]+)\]', original))
        translated_terms = sorted(re.findall(r'\[([^\]]+)\]', translated_roman))
        return original_terms == translated_terms

    def unguard_terms(self, text: str) -> str:
        """Remove square brackets, keeping the term text."""
        return re.sub(r'\[([^\]]+)\]', r'\1', text)

    def _fix_marathi_roman(self, text: str) -> str:
        """Replace common Hindi words with Marathi equivalents in Roman script."""
        replacements = [
            # Hindi -> Marathi
            (r'\bkarta hai\b', 'karte'),
            (r'\bkarti hai\b', 'karte'),
            (r'\bhai\b', 'ahe'),
            (r'\bhain\b', 'ahet'),
            (r'\bke\b', 'cha'),
            (r'\bko\b', 'la'),
            (r'\bpar\b', 'vpar'),
            (r'\bupar\b', 'vpar'),
            (r'\bke saath\b', 'saath'),
            (r'\bdo\b', 'don'),
            (r'\bek\b', 'ek'),
            (r'\bhar\b', 'prati'),
        ]
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text

    def _fix_marathi_devanagari(self, text: str) -> str:
        """Replace common Hindi words with Marathi equivalents in Devanagari."""
        replacements = [
            # Hindi -> Marathi Devanagari
            (r'करता है', 'करते'),
            (r'करती है', 'करते'),
            (r'हैं', 'आहे'),
            (r'है', 'आहे'),
            (r'के', 'च्या'),
            (r'को', 'ला'),
            (r'पर', 'वर'),
            (r'के साथ', 'साठ'),
            (r'द्वारा', 'द्वारे'),
            (r'एक', 'एक'),
        ]
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text)
        return text


class LLMTranslator(BaseTranslator):
    """
    LLM-based translator using Groq API.
    Translates only non-bracketed text while preserving bracketed terms.
    Returns both Roman script and Devanagari outputs.
    """

    def __init__(self, target_language: str = "hi",
                 api_key: Optional[str] = None,
                 model: str = "llama-3.1-8b-instant",
                 temperature: float = 0.3):
        super().__init__(target_language)
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.lang_names = {
            'hi': 'Hindi',
            'mr': 'Marathi',
        }
        self.lang_scripts = {
            'hi': 'Devanagari',
            'mr': 'Devanagari',
        }

    def _build_prompt(self, text: str) -> str:
        """Build elaborate prompt with few-shot examples."""
        lang = self.lang_names.get(self.target_language, 'Hindi')
        script = self.lang_scripts.get(self.target_language, 'Devanagari')
        
        # Language-specific few-shot examples
        if self.target_language == 'mr':
            examples = '''
Input: "The [for loop] iterates over the [array]."
Output: {{"roman": "for loop array cha vpar iterate karte", "devanagari": "फॉर लूप ऐरे च्या वर iterate करते"}}

Input: "This [class] has four [member variables]."
Output: {{"roman": "hi class char member variables ahe", "devanagari": "ही क्लास चार मेंबर व्हेरिएबल्स आहे"}}

Input: "The [function] returns a [boolean] value."
Output: {{"roman": "function ek boolean value return karte", "devanagari": "फंक्शन एक बूलियन व्हैल्यू return करते"}}

Input: "Each [object] has its own [instance variables]."
Output: {{"roman": "prati object la apala instance variables ahe", "devanagari": "प्रत्येक ऑब्जेक्ट ला आपला इन्स्टेंस व्हेरिएबल्स आहे"}}

Input: "The [while loop] continues until the [condition] becomes false."
Output: {{"roman": "while loop such tak chalte jab tak condition false nahi hot", "devanagari": "व्हाइल लूप तेवढा चालतो जोपर्यंत कंडीशन false नाही होत"}}

Input: "Call the [function] with two [arguments]."
Output: {{"roman": "function la don arguments saath call kara", "devanagari": "फंक्शन ला दोन आर्ग्युमेंट्स साठ call करा"}}

STRICT RULES FOR MARATHI:
- NEVER use "hai" - ALWAYS use "ahe" (singular) or "ahet" (plural)
- NEVER use "karta hai" - ALWAYS use "karte" (plural) or "karto" (singular)
- NEVER use "ke" - ALWAYS use "cha/chi/che"
- NEVER use "par" or "upar" - ALWAYS use "vpar"
- NEVER use "ko" - ALWAYS use "la"
- NEVER use "ke saath" - ALWAYS use "saath"
- NEVER use "do" - ALWAYS use "don"'''
        else:
            examples = '''
Input: "The [for loop] iterates over the [array]."
Output: {{"roman": "[for loop] [array] ke upar iterate karta hai", "devanagari": "[फॉर लूप] [ऐरे] के ऊपर इटरेट करता है"}}

Input: "This [class] has four [member variables]."
Output: {{"roman": "is [class] mein chaar [member variables] hai", "devanagari": "इस [क्लास] में चार [मेंबर व्हेरिएबल्स] हैं"}}

Input: "The [function] returns a [boolean] value."
Output: {{"roman": "[function] ek [boolean] value return karta hai", "devanagari": "[फंक्शन] एक [बूलियन] व्हैल्यू रिटर्न करता है"}}

Input: "Each [object] has its own [instance variables]."
Output: {{"roman": "har [object] ke apne [instance variables] hote hain", "devanagari": "हर [ऑब्जेक्ट] के अपने [इन्स्टेंस व्हेरिएबल्स] होते हैं"}}

Input: "Call the [function] with two [arguments]."
Output: {{"roman": "[function] ko do [arguments] ke saath call karo", "devanagari": "[फंक्शन] को दो [आर्ग्युमेंट्स] के साथ कॉल करो"}}'''
        
        system_prompt = f"""You are an expert technical translator from English to {lang}.

TASK: Translate the given English text to {lang} while following these rules CRITICAL:

{f"- You MUST translate to {lang} (Marathi), NOT Hindi! This is very important." if self.target_language == 'mr' else ""}

1. ABSOLUTE RULE - PRESERVE BRACKETS: Any text inside square brackets [like this] must appear WITH EXACTLY THE SAME BRACKETS in your output. DO NOT remove, modify, or add any brackets. The bracketed terms are technical terms that must stay in English.

2. TRANSLATE NON-BRACKETED TEXT: Translate only the English text that is NOT inside brackets to {lang}.

3. GRAMMATICAL COGNIZANCE: When translating text that surrounds bracketed terms:
   - Use proper {lang} sentence structure (typically SOV - Subject-Object-Verb)
   - Apply correct gender, case, and number agreement
   - Use appropriate postpositions instead of English prepositions
   - Add auxiliary verbs and particles as needed for natural {lang} grammar
{f"   - For MARATHI: Use 'cha/chi/che' for possession, 'ahe/ahet' for 'is/are', 'karte' for 'does', NOT Hindi forms!" if self.target_language == 'mr' else ""}

4. OUTPUT FORMAT: Return a JSON object with exactly these two fields:
   - "roman": Translation in Roman script (Latin alphabet). KEEP ALL [bracketed terms] EXACTLY as in input. Non-bracketed words should be in Roman {lang.lower()} transliteration.
   - "devanagari": Translation in {script} script. KEEP ALL [bracketed terms] EXACTLY as in input. ALL non-bracketed words must be in Devanagari script ONLY - no Roman words allowed!

IMPORTANT: 
- The brackets [] are delimiters - keep them exactly as they appear in the input!
- For Devanagari output: EVERY non-bracketed word must be in Devanagari script, not Roman!
- For Marathi: Use proper Marathi grammar and sentence structure (not Hindi)

EXAMPLES:
''' + examples + '''

Input: "The [while loop] continues until the [condition] becomes false."
Output: {{"roman": "[while loop] tab tak continue karta hai jab tak [condition] false nahi ho jati", "devanagari": "[वाइल लूप] तब तक जारी रहता है जब तक [कंडीशन] फॉल्स नहीं हो जाती"}}

Input: "Call the [function] with two [arguments]."
Output: {{"roman": "[function] ko do [arguments] ke saath call karo", "devanagari": "[फंक्शन] को दो [आर्ग्युमेंट्स] के साथ कॉल करो"}}

Input: "{text}"
Output:"""

        return system_prompt

    def translate(self, text: str) -> Dict[str, str]:
        """
        Translate bracketed English text to Hindi/Marathi.
        
        Args:
            text: English text with bracketed terms like [for loop]
            
        Returns:
            Dict with 'roman' and 'devanagari' keys containing translations
        """
        try:
            from groq import Groq
        except ImportError:
            print("Warning: Groq package not installed. Run: pip install groq", file=sys.stderr)
            return {"roman": text, "devanagari": text}

        if not self.api_key:
            print("Warning: No API key provided.", file=sys.stderr)
            return {"roman": text, "devanagari": text}

        try:
            client = Groq(api_key=self.api_key)
            
            prompt = self._build_prompt(text)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            
            try:
                result = json.loads(content)
                roman = result.get("roman", text).strip()
                devanagari = result.get("devanagari", text).strip()
                
                # Validate brackets BEFORE removing them
                if not self.validate_constraints(text, roman):
                    print("Warning: Bracketed terms may not be preserved correctly.", file=sys.stderr)
                
                # Remove brackets from final output
                roman = self.unguard_terms(roman)
                devanagari = self.unguard_terms(devanagari)
                
                # Post-process Marathi to fix common Hindi->Marathi issues
                if self.target_language == 'mr':
                    roman = self._fix_marathi_roman(roman)
                    devanagari = self._fix_marathi_devanagari(devanagari)
                
                return {"roman": roman, "devanagari": devanagari}
            except json.JSONDecodeError:
                print(f"Warning: Could not parse LLM response as JSON: {content}", file=sys.stderr)
                return {"roman": text, "devanagari": text}
                
        except Exception as e:
            print(f"Warning: LLM translation failed ({e}). Returning original.", file=sys.stderr)
            return {"roman": text, "devanagari": text}


def create_translator(target_language: str = "hi",
                      api_key: Optional[str] = None,
                      model: str = "llama-3.1-8b-instant") -> LLMTranslator:
    """Factory function to create LLM translator."""
    return LLMTranslator(
        target_language=target_language,
        api_key=api_key,
        model=model
    )
