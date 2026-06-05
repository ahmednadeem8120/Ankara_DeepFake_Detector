import json
from typing import Optional

from ..config import settings
from .retriever import ForensicRetriever


FORENSIC_SYSTEM_PROMPT = """You are the Ankara Forensic Reasoning Engine, an AI-powered
digital forensics analyst specializing in deepfake detection.

Ankara analyzes media with a DINOv2 self-supervised vision transformer probe that
detects spatial texture and structural artifacts left by face-generation models.

Your role is to explain the detection result in clear, precise forensic language.
You must:
1. Reference the spatial analysis result and any texture-anomaly evidence found
2. Cite relevant research when available (use the provided context)
3. Explain the significance of the detected artifacts
4. Provide a confidence-calibrated overall assessment
5. Note any limitations or caveats in the analysis

Format your response as a structured forensic brief:
- SUMMARY: 2-3 sentence overview
- KEY FINDINGS: bullet points of the most significant evidence
- TECHNICAL ANALYSIS: detailed explanation of the spatial detector's findings
- CITED RESEARCH: relevant papers that support the analysis
- CONFIDENCE ASSESSMENT: explanation of confidence level and any caveats

Use precise technical language but remain accessible.
Do NOT speculate beyond what the evidence supports. Analyze ONLY the spatial
evidence provided — do not invent other detection signals."""


class ForensicReasoningEngine:
    def __init__(self):
        self.retriever = ForensicRetriever()
        self._client = None

    def _get_client(self):
        if getattr(self, "_provider", None) is not None:
            return self._client

        provider = (settings.LLM_PROVIDER or "").lower()

        if provider == "ollama":
            self._client = None
            self._provider = "ollama"
        elif provider == "anthropic" and settings.ANTHROPIC_API_KEY:
            import anthropic
            self._client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            self._provider = "anthropic"
        elif provider == "openai" and settings.OPENAI_API_KEY:
            import openai
            self._client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            self._provider = "openai"
        else:
            self._client = None
            self._provider = "fallback"

        return self._client

    def _ollama_generate(self, context: str) -> str:
        import json as _json
        import urllib.request

        payload = {
            "model": settings.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": FORENSIC_SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        "Analyze the following detection results and provide a forensic "
                        f"explanation. Ground your analysis in the retrieved research.\n\n{context}"
                    ),
                },
            ],
            "stream": False,
            "options": {"temperature": 0.2},
        }
        req = urllib.request.Request(
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            data=_json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
        return data["message"]["content"]

    def _build_context(self, detection_result: dict, retrieved_docs: list[dict]) -> str:
        parts = [
            "SPATIAL DETECTION RESULT",
            f"Authenticity Score: {detection_result.get('authenticity_score', 'N/A')}/100",
            f"Deepfake Probability: {detection_result.get('deepfake_probability', 'N/A')}",
            f"Confidence Level: {detection_result.get('confidence_level', 'N/A')}",
        ]

        meta = detection_result.get("metadata", {})
        if meta.get("frames_analyzed"):
            parts.append(f"Frames analyzed: {meta['frames_analyzed']}")

        evidence = detection_result.get("evidence", [])
        if evidence:
            parts.append("\nEvidence:")
            for ev in evidence:
                parts.append(
                    f"[{ev.get('timestamp_sec', 0):.1f}s] "
                    f"{ev.get('artifact_type', 'unknown')}: "
                    f"{ev.get('description', '')} "
                    f"(confidence: {ev.get('confidence', 0):.2f})"
                )

        if retrieved_docs:
            parts.append("\nRELEVANT RESEARCH")
            for i, doc in enumerate(retrieved_docs):
                parts.append(f"\n[{i+1}] {doc.get('source', 'Unknown')} (relevance: {doc.get('relevance_score', 0):.2f})")
                parts.append(doc.get("text", ""))

        return "\n".join(parts)

    def _generate_fallback_explanation(self, detection_result: dict) -> str:
        score = detection_result.get("authenticity_score", 50)
        prob = detection_result.get("deepfake_probability", 0.5)
        confidence = detection_result.get("confidence_level", "medium")

        if prob > 0.7:
            verdict = "This media is likely manipulated."
        elif prob < 0.3:
            verdict = "This media appears authentic."
        else:
            verdict = "The analysis is inconclusive."

        lines = [f"SUMMARY: {verdict}", f"Authenticity score: {score:.1f}/100 (confidence: {confidence})."]

        evidence = detection_result.get("evidence", [])
        if evidence:
            lines.append("\nKEY FINDINGS:")
            for ev in evidence:
                lines.append(f"  - [{ev.get('timestamp_sec', 0):.1f}s] {ev.get('description', '')}")

        lines.append("\nTECHNICAL ANALYSIS:")
        if prob > 0.6:
            lines.append(f"  Spatial (DINOv2): detected texture/structural artifacts (score: {prob:.2f})")
        elif prob < 0.3:
            lines.append(f"  Spatial (DINOv2): no manipulation artifacts detected (score: {prob:.2f})")
        else:
            lines.append(f"  Spatial (DINOv2): inconclusive (score: {prob:.2f})")

        return "\n".join(lines)

    def explain(self, detection_result: dict) -> str:
        retrieved_docs = self.retriever.retrieve_for_detection(detection_result)
        context = self._build_context(detection_result, retrieved_docs)
        client = self._get_client()

        if self._provider == "ollama":
            try:
                return self._ollama_generate(context)
            except Exception as e:
                print(f"Ollama explanation failed: {e}")

        if self._provider == "anthropic" and client:
            try:
                response = client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1500,
                    system=FORENSIC_SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": f"Analyze the following detection results and provide a forensic explanation. Ground your analysis in the retrieved research.\n\n{context}"}],
                )
                return response.content[0].text
            except Exception as e:
                print(f"LLM explanation failed: {e}")

        elif self._provider == "openai" and client:
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    max_tokens=1500,
                    messages=[
                        {"role": "system", "content": FORENSIC_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Analyze the following detection results and provide a forensic explanation. Ground your analysis in the retrieved research.\n\n{context}"},
                    ],
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"LLM explanation failed: {e}")

        return self._generate_fallback_explanation(detection_result)

    async def explain_async(self, detection_result: dict) -> str:
        import asyncio
        return await asyncio.to_thread(self.explain, detection_result)
