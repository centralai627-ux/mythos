"""
Mythos Self-Reflection System
=============================
Evaluasi dan perbaikan diri untuk meningkatkan kualitas response.
"""
from __future__ import annotations
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Reflection:
    timestamp: float
    user_message: str
    response: str
    scores: Dict[str, float]
    overall_score: float
    issues: List[str]
    suggestions: List[str]


class SelfReflector:
    """Sistem self-reflection untuk evaluasi kualitas response."""

    def __init__(self):
        self.history: List[Reflection] = []
        self.max_history = 100

    def evaluate_response(
        self,
        user_message: str,
        response: str,
        tool_calls: Optional[List[Dict]] = None
    ) -> Reflection:
        """Evaluate kualitas response."""
        import time

        scores = {
            'relevance': self._score_relevance(user_message, response),
            'completeness': self._score_completeness(response),
            'conciseness': self._score_conciseness(response),
            'tool_usage': self._score_tool_usage(user_message, tool_calls),
            'hallucination': self._detect_hallucination(response),
        }

        # Invert hallucination score (lower is better)
        scores['hallucination'] = 1.0 - scores['hallucination']

        overall = sum(scores.values()) / len(scores)

        issues = self._identify_issues(scores, response)
        suggestions = self._generate_suggestions(scores, issues)

        reflection = Reflection(
            timestamp=time.time(),
            user_message=user_message[:200],
            response=response[:200],
            scores=scores,
            overall_score=overall,
            issues=issues,
            suggestions=suggestions
        )

        self.history.append(reflection)
        if len(self.history) > self.max_history:
            self.history.pop(0)

        return reflection

    def _score_relevance(self, user_msg: str, response: str) -> float:
        """Score: Apakah response menjawab pertanyaan user?"""
        user_words = set(user_msg.lower().split())
        response_words = set(response.lower().split())

        if not user_words:
            return 0.5

        overlap = len(user_words & response_words)
        return min(1.0, overlap / len(user_words) * 2)

    def _score_completeness(self, response: str) -> float:
        """Score: Apakah response lengkap?"""
        score = min(1.0, len(response) / 500)

        if re.search(r'\n\n|\n-|\n\*|\n\d', response):
            score += 0.2

        return min(1.0, score)

    def _score_conciseness(self, response: str) -> float:
        """Score: Apakah response tidak terlalu panjang?"""
        ideal = 500
        diff = abs(len(response) - ideal)
        return max(0, 1 - diff / 2000)

    def _score_tool_usage(self, user_msg: str, tool_calls: Optional[List[Dict]]) -> float:
        """Score: Apakah tools digunakan dengan tepat?"""
        if not tool_calls:
            needs_tools = bool(re.search(
                r'file|command|search|run|list|read|write|create|execute',
                user_msg, re.I
            ))
            return 0.3 if needs_tools else 1.0
        return 0.8

    def _detect_hallucination(self, response: str) -> float:
        """Detect potensi hallucination."""
        indicators = [
            r'I think maybe',
            r"I'm not sure but",
            r'According to my knowledge',
            r'I believe',
            r'It seems like',
            r'Perhaps',
            r'Maybe',
            r"I'm guessing"
        ]

        score = 0
        for pattern in indicators:
            if re.search(pattern, response, re.I):
                score += 0.2

        return min(1.0, score)

    def _identify_issues(self, scores: Dict[str, float], response: str) -> List[str]:
        """Identifikasi masalah dalam response."""
        issues = []

        if scores['relevance'] < 0.3:
            issues.append('Response kurang relevan dengan pertanyaan')

        if scores['completeness'] < 0.3:
            issues.append('Response terlalu pendek atau tidak lengkap')

        if scores['conciseness'] < 0.3:
            issues.append('Response terlalu panjang')

        if scores['tool_usage'] < 0.5:
            issues.append('Tools tidak digunakan dengan tepat')

        if scores['hallucination'] < 0.5:
            issues.append('Potensi hallucination terdeteksi')

        return issues

    def _generate_suggestions(self, scores: Dict[str, float], issues: List[str]) -> List[str]:
        """Generate saran perbaikan."""
        suggestions = []

        if scores['relevance'] < 0.5:
            suggestions.append('Fokus menjawab pertanyaan user secara langsung')

        if scores['completeness'] < 0.5:
            suggestions.append('Tambahkan detail atau contoh yang lebih lengkap')

        if scores['conciseness'] < 0.5:
            suggestions.append('Hapus informasi yang tidak perlu')

        if scores['tool_usage'] < 0.5:
            suggestions.append('Gunakan tools untuk data yang akurat')

        if scores['hallucination'] < 0.5:
            suggestions.append('Verifikasi informasi sebelum memberikan jawaban')

        return suggestions

    def get_stats(self) -> Dict[str, Any]:
        """Dapatkan statistik performa."""
        if not self.history:
            return None

        scores = [r.overall_score for r in self.history]
        return {
            'total_evaluations': len(self.history),
            'average_score': sum(scores) / len(scores),
            'last_score': scores[-1] if scores else 0,
            'best_score': max(scores) if scores else 0,
            'worst_score': min(scores) if scores else 0,
        }

    def get_improvement_trend(self) -> str:
        """Analisis tren perbaikan."""
        if len(self.history) < 5:
            return 'Data belum cukup untuk analisis tren'

        recent = [r.overall_score for r in self.history[-5:]]
        older = [r.overall_score for r in self.history[-10:-5]] if len(self.history) >= 10 else []

        if not older:
            return 'Mulai monitoring performa'

        recent_avg = sum(recent) / len(recent)
        older_avg = sum(older) / len(older)

        if recent_avg > older_avg + 0.1:
            return 'Performa meningkat signifikan'
        elif recent_avg > older_avg:
            return 'Performa sedikit meningkat'
        elif recent_avg < older_avg - 0.1:
            return 'Performa menurun - perlu investigasi'
        else:
            return 'Performa stabil'


# Global instance
reflector = SelfReflector()
