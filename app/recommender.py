import math
import re
from collections import Counter
from typing import Any

from app.catalog import TYPE_LABELS, load_catalog
from app.models import ChatResponse, Message, Recommendation

TOKEN_RE = re.compile(r"[a-z0-9+#.]+")

STOPWORDS = {
    "a",
    "an",
    "and",
    "around",
    "for",
    "i",
    "me",
    "need",
    "of",
    "please",
    "the",
    "to",
    "want",
    "with",
}

GENERIC_REQUEST_TERMS = {
    "assessment",
    "assessments",
    "candidate",
    "employee",
    "hire",
    "hiring",
    "job",
    "role",
    "test",
    "tests",
}

ALIASES = {
    "gsa": "global skills assessment",
    "opq": "occupational personality questionnaire opq32r",
    "opq32": "occupational personality questionnaire opq32r",
    "opq32r": "occupational personality questionnaire opq32r",
}

OFF_TOPIC_TERMS = {
    "salary",
    "compensation",
    "legal",
    "law",
    "lawsuit",
    "visa",
    "immigration",
    "contract",
    "interview questions",
    "job posting",
    "write a job ad",
}

INJECTION_TERMS = {
    "ignore previous",
    "ignore the previous",
    "developer message",
    "system prompt",
    "reveal prompt",
    "bypass",
    "jailbreak",
}

SKILL_SYNONYMS = {
    "java": ["java", "j2ee", "spring", "hibernate"],
    "python": ["python", "django", "flask"],
    "javascript": ["javascript", "typescript", "node", "react", "angular"],
    "sql": ["sql", "database", "mysql", "postgres", "oracle", "server"],
    "cloud": ["aws", "azure", "cloud", "kubernetes", "docker", "devops"],
    "testing": ["testing", "qa", "selenium", "manual testing", "automation"],
    "data": ["data", "analytics", "excel", "power bi", "tableau", "statistics"],
    "sales": ["sales", "customer", "account", "crm", "service"],
}

PERSONALITY_TERMS = {"personality", "behavior", "behaviour", "opq", "motivation"}
ABILITY_TERMS = {"ability", "aptitude", "cognitive", "reasoning", "numerical", "verbal", "deductive", "inductive"}
SIMULATION_TERMS = {"simulation", "hands-on", "practical", "work sample"}


class SHLAgent:
    def __init__(self) -> None:
        self.catalog = load_catalog()
        self._documents = [self._document(item) for item in self.catalog]
        self._idf = self._build_idf(self._documents)

    def respond(self, messages: list[Message]) -> ChatResponse:
        if not messages:
            return self._clarify()

        user_texts = [m.content for m in messages if m.role == "user"]
        latest = user_texts[-1] if user_texts else ""
        transcript = "\n".join(user_texts)

        if self._is_unsafe_or_offtopic(latest):
            return ChatResponse(
                reply="I can only help with SHL assessment selection from the product catalog. I cannot assist with that request.",
                recommendations=[],
                end_of_conversation=False,
            )

        comparison = self._comparison_request(latest)
        if comparison:
            return self._compare(comparison)

        if self._needs_clarification(transcript):
            return self._clarify(transcript)

        ranked = self.rank(transcript, limit=10)
        if not ranked:
            return ChatResponse(
                reply="I could not find a grounded SHL catalog match from the information provided. Please share the role, core skills, seniority, and any preferred test types.",
                recommendations=[],
                end_of_conversation=False,
            )

        recommendations = [
            Recommendation(name=i["name"], url=i["url"], test_type=i.get("test_type", ""))
            for i in ranked[:10]
        ]
        role_phrase = self._role_phrase(transcript)
        reply = f"Based on the SHL catalog, here are {len(recommendations)} assessments that fit {role_phrase}."
        return ChatResponse(reply=reply, recommendations=recommendations, end_of_conversation=True)

    def rank(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        query_tokens = self._expand_tokens(query)
        if not query_tokens:
            return []

        wanted_types = self._wanted_types(query)
        scored: list[tuple[float, dict[str, Any]]] = []
        for item, doc_tokens in zip(self.catalog, self._documents):
            score = self._tfidf_score(query_tokens, doc_tokens)
            name = item.get("name", "").lower()
            description = item.get("description", "").lower()
            haystack = f"{name} {description}"

            for token in set(query_tokens):
                if token in name:
                    score += 4.0
                elif token in haystack:
                    score += 1.5

            test_type = item.get("test_type", "")
            if wanted_types:
                overlap = set(test_type) & wanted_types
                score += 5.0 * len(overlap)
                if not overlap and wanted_types == {"P"}:
                    score -= 2.0

            if "stakeholder" in query.lower() or "communication" in query.lower():
                if set(test_type) & {"P", "C", "S"}:
                    score += 2.0

            if "senior" in query.lower() or "manager" in query.lower():
                if re.search(r"manager|professional|lead|senior", item.get("job_levels", "").lower() + " " + name):
                    score += 1.0

            if score > 0:
                scored.append((score, item))

        scored.sort(key=lambda pair: (-pair[0], pair[1].get("name", "")))
        return [item for _, item in scored[:limit]]

    def _compare(self, names: list[str]) -> ChatResponse:
        matches = [self._find_item(name) for name in names]
        matches = [m for m in matches if m]
        if len(matches) < 2:
            return ChatResponse(
                reply="I can compare SHL assessments when both names can be matched to catalog entries. Please provide the assessment names as they appear in the catalog.",
                recommendations=[],
                end_of_conversation=False,
            )

        parts = []
        recs = []
        for item in matches[:3]:
            types = ", ".join(TYPE_LABELS.get(t, t) for t in item.get("test_type", ""))
            duration = item.get("duration") or "not listed"
            parts.append(
                f"{item['name']}: {types}; {duration} minutes; {item.get('description', 'No catalog description available')}"
            )
            recs.append(Recommendation(name=item["name"], url=item["url"], test_type=item.get("test_type", "")))
        reply = "Here is the grounded catalog comparison. " + " ".join(parts)
        return ChatResponse(reply=reply, recommendations=recs, end_of_conversation=False)

    def _find_item(self, text: str) -> dict[str, Any] | None:
        needle = self._normalize(ALIASES.get(text.strip().lower(), text))
        best_score = 0.0
        best = None
        for item in self.catalog:
            name = self._normalize(item.get("name", ""))
            if needle and needle in name:
                return item
            overlap = len(set(TOKEN_RE.findall(needle)) & set(TOKEN_RE.findall(name)))
            score = overlap / max(1, len(set(TOKEN_RE.findall(needle))))
            if score > best_score:
                best_score = score
                best = item
        return best if best_score >= 0.5 else None

    def _comparison_request(self, text: str) -> list[str]:
        lower = text.lower()
        if not any(word in lower for word in ["compare", "difference", "versus", " vs "]):
            return []
        cleaned = re.sub(r"what('?s| is)?|the|difference|between|compare|versus|vs\.?|and", "|", text, flags=re.I)
        parts = [p.strip(" ?.,:;\"'") for p in cleaned.split("|") if len(p.strip()) > 1]
        return parts[:3]

    def _needs_clarification(self, text: str) -> bool:
        tokens = set(TOKEN_RE.findall(text.lower())) - STOPWORDS
        meaningful = tokens - GENERIC_REQUEST_TERMS
        has_role_signal = len(meaningful) >= 2 or any(skill in text.lower() for skill in SKILL_SYNONYMS)
        has_type_signal = bool(tokens & PERSONALITY_TERMS) or bool(tokens & ABILITY_TERMS) or bool(tokens & SIMULATION_TERMS)
        return not (has_role_signal or has_type_signal)

    def _clarify(self, text: str = "") -> ChatResponse:
        reply = (
            "I can help shortlist SHL assessments. Please share the role, seniority, core skills, and whether you want "
            "knowledge, cognitive ability, personality/behavior, simulation, or a mix."
        )
        if text:
            reply = "I need a little more context before recommending. " + reply
        return ChatResponse(reply=reply, recommendations=[], end_of_conversation=False)

    def _is_unsafe_or_offtopic(self, text: str) -> bool:
        lower = text.lower()
        return any(term in lower for term in OFF_TOPIC_TERMS | INJECTION_TERMS)

    def _wanted_types(self, query: str) -> set[str]:
        lower_tokens = set(TOKEN_RE.findall(query.lower()))
        wanted: set[str] = set()
        if lower_tokens & PERSONALITY_TERMS:
            wanted.add("P")
        if lower_tokens & ABILITY_TERMS:
            wanted.add("A")
        if lower_tokens & SIMULATION_TERMS:
            wanted.add("S")
        if {"skill", "skills", "technical", "knowledge"} & lower_tokens:
            wanted.add("K")
        return wanted

    def _document(self, item: dict[str, Any]) -> list[str]:
        fields = [
            item.get("name", ""),
            item.get("description", ""),
            item.get("job_levels", ""),
            item.get("languages", ""),
            item.get("test_type", ""),
        ]
        return self._expand_tokens(" ".join(fields))

    def _expand_tokens(self, text: str) -> list[str]:
        lower = text.lower()
        tokens = TOKEN_RE.findall(lower)
        for root, synonyms in SKILL_SYNONYMS.items():
            if any(s in lower for s in synonyms):
                tokens.extend(TOKEN_RE.findall(" ".join(synonyms + [root])))
        return tokens

    def _build_idf(self, docs: list[list[str]]) -> dict[str, float]:
        df = Counter()
        for doc in docs:
            df.update(set(doc))
        total = max(1, len(docs))
        return {term: math.log((1 + total) / (1 + count)) + 1 for term, count in df.items()}

    def _tfidf_score(self, query: list[str], doc: list[str]) -> float:
        doc_counts = Counter(doc)
        query_counts = Counter(query)
        score = 0.0
        for token, q_count in query_counts.items():
            if token in doc_counts:
                score += q_count * (1 + math.log(doc_counts[token])) * self._idf.get(token, 1.0)
        return score

    def _role_phrase(self, text: str) -> str:
        compact = " ".join(text.split())
        return compact[:90] + ("..." if len(compact) > 90 else "")

    def _normalize(self, text: str) -> str:
        return " ".join(TOKEN_RE.findall(text.lower()))
