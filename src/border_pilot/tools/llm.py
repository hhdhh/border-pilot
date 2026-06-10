"""LLM abstraction with mock + Anthropic + HuggingFace fallback."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class LLMMessage:
    role: str
    content: str


class BaseLLM:
    def chat(self, messages: List[LLMMessage], *, temperature: float = 0.7, max_tokens: int = 1024) -> str:
        raise NotImplementedError


class MockLLM(BaseLLM):
    """Deterministic-ish mock that produces plausible agent outputs."""

    def chat(self, messages: List[LLMMessage], *, temperature: float = 0.7, max_tokens: int = 1024) -> str:
        user_text = " ".join(m.content for m in messages if m.role == "user").lower()
        if "trend" in user_text or "scout" in user_text:
            return self._mock_trends()
        if "listing" in user_text or "translate" in user_text or "amazon" in user_text or "ebay" in user_text:
            return self._mock_listing(user_text)
        if "go/no-go" in user_text or "competitor" in user_text or ("decision" in user_text and "tam" in user_text):
            return self._mock_market()
        if "quality" in user_text or "score" in user_text or "compliance" in user_text:
            return self._mock_quality()
        return self._mock_generic()

    def _mock_trends(self) -> str:
        seeds = [
            ("Wireless Earbuds (TWS)", "rising", "amazon_us", "$19.99-$29.99", "High search volume + low top-10 churn"),
            ("Smart LED Strip Lights", "rising", "amazon_de", "EUR12.99-EUR24.99", "Sustained 8-week upward trend"),
            ("Portable Blender USB-C", "rising", "amazon_us", "$24.99-$39.99", "Q3 seasonal lift + creator-driven"),
            ("Magnetic Phone Mount", "stable", "amazon_us", "$8.99-$14.99", "Evergreen accessory category"),
            ("Foldable Laptop Stand", "rising", "amazon_uk", "GBP18.99-GBP29.99", "Remote-work tailwind"),
        ]
        items = ",\n ".join(
            f'{{"name": "{n}", "trend": "{t}", "marketplace": "{m}", "price_band": "{p}", "note": "{note}"}}'
            for (n, t, m, p, note) in seeds
        )
        return f"[TRENDS_JSON]\n[{items}\n]"

    def _mock_market(self) -> str:
        return (
            "[MARKET_JSON]\n"
            "{\n"
            ' "tam_estimate_usd": "1.2B annual search volume on Amazon US (TWS category)",\n'
            ' "top_competitors": ["Anker Soundcore Life P2", "JBL Vibe 100", "QCY HT07"],\n'
            ' "price_sweet_spot": "$24.99-$29.99",\n'
            ' "review_threshold_to_win": "4.3 stars / 1k+ reviews within 90 days",\n'
            ' "differentiation_signal": "Hybrid ANC + USB-C + 40h case",\n'
            ' "risk_flags": ["Tariff exposure for electronics shipped from CN", "Battery shipping restrictions EU"]\n'
            "}\n"
        )

    def _mock_listing(self, user_text: str) -> str:
        # Use word-boundary regex to avoid "description" matching "de".
        def has_word(text, word):
            return re.search(rf"\b{re.escape(word)}\b", text) is not None
        language = "en"
        marketplace = "amazon_us"
        if has_word(user_text, "de") or has_word(user_text, "german") or has_word(user_text, "deutsch"):
            language = "de"
            marketplace = "amazon_de"
        elif has_word(user_text, "ja") or has_word(user_text, "japan") or has_word(user_text, "japanese"):
            language = "ja"
            marketplace = "amazon_jp"
        elif has_word(user_text, "uk") or has_word(user_text, "english-uk"):
            language = "en-GB"
            marketplace = "amazon_uk"

        title = {
            "en": "Wireless Earbuds, Hybrid ANC Bluetooth 5.3, 40H Playtime USB-C",
            "de": "Kabellose Ohrhoerer, Hybrid ANC Bluetooth 5.3, 40H Spielzeit USB-C",
            "ja": "Wireless Earphones Hybrid ANC Bluetooth 5.3 40 Hours USB-C",
            "en-GB": "Wireless Earbuds - Hybrid ANC, Bluetooth 5.3, 40 hr Playtime, USB-C",
        }.get(language, "Wireless Earbuds - Hybrid ANC, BT 5.3, 40H, USB-C")

        bullets = {
            "en": [
                "Hybrid Active Noise Cancelling reduces ambient noise by up to -32 dB",
                "Bluetooth 5.3 with stable 10 m range and instant reconnect",
                "40 hours total playtime with the USB-C fast-charge case (10 min -> 2 hr)",
                "Custom 10 mm dynamic drivers tuned for clear vocals and tight bass",
                "IPX5 sweat and rain resistance for workouts and commuting",
            ],
            "de": [
                "Hybrid Active Noise Cancelling reduziert Umgebungslaerme um bis zu -32 dB",
                "Bluetooth 5.3 mit stabiler 10 m Reichweite und sofortiger Wiederverbindung",
                "40 Stunden Gesamtspielzeit mit USB-C Schnelllade-Etui (10 Min -> 2 Std.)",
                "10 mm dynamische Treiber, abgestimmt auf klare Stimmen und praezisen Bass",
                "IPX5 Schutz vor Schweiss und Regen fuer Training und Pendelverkehr",
            ],
            "ja": [
                "Hybrid ANC deactive noise wo -32dB made reduced",
                "Bluetooth 5.3 stable 10 m range with instant reconnect",
                "40 hours total playtime with USB-C fast-charge case",
                "10 mm dynamic drivers tuned for clear vocals and tight bass",
                "IPX5 sweat and rain resistance for workouts and commuting",
            ],
            "en-GB": [
                "Hybrid Active Noise Cancelling, up to -32 dB ambient reduction",
                "Bluetooth 5.3 with stable 10 m range and instant reconnect",
                "40 hr total playtime, USB-C fast-charge case (10 min charge -> 2 hr)",
                "10 mm dynamic drivers tuned for clear vocals and tight bass",
                "IPX5 sweat and rain resistant - built for workouts and commutes",
            ],
        }.get(language, [
            "Hybrid ANC, BT 5.3, 40 hr playtime, USB-C fast charge",
            "IPX5, ergonomic fit, stable connection",
        ])

        description = {
            "en": "Sound that disappears into your day. These earbuds pair Hybrid Active Noise Cancelling with a custom 10 mm dynamic driver to deliver clear vocals and tight bass. Bluetooth 5.3 stays rock-solid up to 10 m, the USB-C case pumps out 40 hours total, and 10 minutes in the case gives you another 2 hours of playback. IPX5 sweat and rain resistance means your soundtrack keeps going through commutes and workouts.",
            "de": "Klang, der in deinen Tag verschwindet. Diese Ohrhoerer kombinieren Hybrid Active Noise Cancelling mit einem massgeschneiderten 10-mm-Dynamiktreiber und liefern klare Stimmen sowie praezisen Bass. Bluetooth 5.3 bleibt bis zu 10 m stabil, das USB-C-Etui liefert 40 Stunden Spielzeit, und 10 Minuten Aufladen geben weitere 2 Stunden Wiedergabe.",
            "ja": "Nichijou ni tokeru sound. Hybrid ANC to 10 mm dynamic driver de clear vocals and tight bass. Bluetooth 5.3 de 10 m made stable, USB-C case de 40 hours, 10 minute charge de 2 hours.",
            "en-GB": "Sound that disappears into your day. Hybrid Active Noise Cancelling plus a custom 10 mm dynamic driver give clear vocals and tight bass. Bluetooth 5.3 holds rock-solid up to 10 m, the USB-C case delivers 40 hours total, and a 10-minute charge gives you another 2 hours.",
        }.get(language, "Hybrid ANC earbuds with 40 hr total playtime and USB-C fast charge.")

        bullets_json = ",\n".join(f'    "{b}"' for b in bullets)
        return (
            "[LISTING_JSON]\n"
            "{\n"
            f'    "marketplace": "{marketplace}",\n'
            f'    "language": "{language}",\n'
            f'    "title": "{title}",\n'
            '    "bullet_points": [\n'
            + bullets_json
            + "\n    ],\n"
            f'    "description": "{description}",\n'
            '    "keywords": ["wireless earbuds", "anc", "bluetooth 5.3", "usb-c", "long battery"],\n'
            '    "price_hint": "$24.99 - $29.99"\n'
            "}\n"
        )

    def _mock_quality(self) -> str:
        return (
            "[QUALITY_JSON]\n"
            "{\n"
            '    "overall_score": 0.82,\n'
            '    "checks": [\n'
            '        {"name": "title_length_ok", "score": 1.0, "note": "Title under 200 chars on all targets"},\n'
            '        {"name": "bullet_count_ok", "score": 1.0, "note": "5 bullets per listing"},\n'
            '        {"name": "no_keyword_stuffing", "score": 0.8, "note": "Keywords appear naturally in title and bullets"},\n'
            '        {"name": "language_consistency", "score": 0.85, "note": "Minor formality drift in German variant"},\n'
            '        {"name": "marketplace_compliance", "score": 0.7, "note": "amazon_de requires DE-compliant battery declaration; verify before publish"}\n'
            '    ],\n'
            '    "recommendation": "APPROVED_WITH_REVIEW"\n'
            "}\n"
        )

    def _mock_generic(self) -> str:
        return "Acknowledged."


class AnthropicLLM(BaseLLM):
    """Thin Anthropic Messages API wrapper."""

    def __init__(self, model: str = "claude-3-5-sonnet-latest", api_key: Optional[str] = None):
        try:
            import anthropic  # type: ignore
        except ImportError as e:
            raise RuntimeError("anthropic package not installed") from e
        self._anthropic = anthropic
        self.client = anthropic.Anthropic(api_key=api_key or os.environ.get("ANTHROPIC_API_KEY"))
        self.model = model

    def chat(self, messages: List[LLMMessage], *, temperature: float = 0.7, max_tokens: int = 1024) -> str:
        system_msgs = [m.content for m in messages if m.role == "system"]
        user_msgs = [{"role": m.role, "content": m.content} for m in messages if m.role != "system"]
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": user_msgs,
        }
        if system_msgs:
            kwargs["system"] = "\n\n".join(system_msgs)
        resp = self.client.messages.create(**kwargs)
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")


class HuggingFaceLLM(BaseLLM):
    """Free-text generation via the HuggingFace Inference API."""

    def __init__(self, model: str = "mistralai/Mistral-7B-Instruct-v0.3", token: Optional[str] = None):
        try:
            from huggingface_hub import InferenceClient  # type: ignore
        except ImportError as e:
            raise RuntimeError("huggingface_hub not installed") from e
        self.client = InferenceClient(model=model, token=token or os.environ.get("HF_TOKEN"))
        self.model = model

    def chat(self, messages: List[LLMMessage], *, temperature: float = 0.7, max_tokens: int = 1024) -> str:
        prompt_parts = []
        for m in messages:
            if m.role == "system":
                prompt_parts.append(f"[SYSTEM]\n{m.content}\n")
            elif m.role == "user":
                prompt_parts.append(f"[USER]\n{m.content}\n")
            elif m.role == "assistant":
                prompt_parts.append(f"[ASSISTANT]\n{m.content}\n")
        prompt_parts.append("[ASSISTANT]\n")
        prompt = "\n".join(prompt_parts)
        out = self.client.text_generation(
            prompt,
            max_new_tokens=max_tokens,
            temperature=temperature,
            do_sample=temperature > 0,
        )
        return out


def make_llm(provider: Optional[str] = None) -> BaseLLM:
    """Select an LLM provider based on env vars or explicit choice."""
    choice = (provider or os.environ.get("BORDER_PILOT_LLM") or "").lower().strip()
    if not choice:
        if os.environ.get("ANTHROPIC_API_KEY"):
            choice = "anthropic"
        elif os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN"):
            choice = "huggingface"
        else:
            choice = "mock"

    if choice in ("anthropic", "claude"):
        return AnthropicLLM()
    if choice in ("huggingface", "hf"):
        return HuggingFaceLLM()
    return MockLLM()
