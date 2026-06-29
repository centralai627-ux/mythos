"""
Mythos Smart AI System
======================
Makes AI smarter, more reliable, and anti-fail with:
- Self-reflection and critique
- Confidence scoring
- Error recovery with fallback chains
- Knowledge validation
- Learning from mistakes
- Output validation
"""
from __future__ import annotations
import os
import json
import time
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime


class SmartAI:
    """Smart AI system with self-improvement capabilities."""
    
    def __init__(self, storage_path: Optional[str] = None) -> None:
        self.storage_path = storage_path or os.path.join(
            os.path.expanduser("~"), ".mythos", "smart_ai.json"
        )
        self.mistakes: List[Dict[str, Any]] = []
        self.knowledge_base: Dict[str, Any] = {}
        self.confidence_history: List[Dict[str, Any]] = []
        self._load()
    
    def _load(self) -> None:
        """Load smart AI data."""
        try:
            if os.path.isfile(self.storage_path):
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.mistakes = data.get("mistakes", [])
                    self.knowledge_base = data.get("knowledge_base", {})
                    self.confidence_history = data.get("confidence_history", [])
        except Exception:
            pass
    
    def _save(self) -> None:
        """Save smart AI data."""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({
                    "mistakes": self.mistakes[-100:],  # Keep last 100
                    "knowledge_base": self.knowledge_base,
                    "confidence_history": self.confidence_history[-100:],
                }, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
    
    # ==================== Self-Reflection ==================== #
    
    def reflect_on_response(self, question: str, response: str, tools_used: List[str] = None) -> Dict[str, Any]:
        """AI critiques its own response."""
        reflection = {
            "timestamp": datetime.now().isoformat(),
            "question": question[:200],
            "response_length": len(response),
            "tools_used": tools_used or [],
            "issues": [],
            "suggestions": [],
            "confidence": 1.0,
        }
        
        # Check for common issues
        issues = []
        
        # 1. Response too short
        if len(response) < 50:
            issues.append("Response too short - may be incomplete")
            reflection["confidence"] -= 0.2
        
        # 2. Hedging language
        hedging_words = ["maybe", "perhaps", "might", "possibly", "I think", "not sure"]
        for word in hedging_words:
            if word.lower() in response.lower():
                issues.append(f"Hedging language detected: '{word}'")
                reflection["confidence"] -= 0.1
        
        # 3. Apologetic language
        apology_words = ["sorry", "apologize", "I apologize", "my mistake"]
        for word in apology_words:
            if word.lower() in response.lower():
                issues.append(f"Apologetic language: '{word}'")
                reflection["confidence"] -= 0.15
        
        # 4. Incomplete sentences
        if response.rstrip().endswith("..."):
            issues.append("Response appears incomplete (ends with ...)")
            reflection["confidence"] -= 0.2
        
        # 5. No concrete action for do-requests
        action_words = ["create", "write", "make", "build", "run", "execute", "generate"]
        if any(word in question.lower() for word in action_words):
            if not any(word in response.lower() for word in ["created", "written", "built", "done", "completed"]):
                if "tool" not in response.lower() and "```" not in response:
                    issues.append("Do-request without clear action result")
                    reflection["confidence"] -= 0.3
        
        reflection["issues"] = issues
        reflection["confidence"] = max(0.0, min(1.0, reflection["confidence"]))
        
        # Generate suggestions
        if reflection["confidence"] < 0.7:
            reflection["suggestions"].append("Consider retrying with more specific instructions")
        if len(response) < 100:
            reflection["suggestions"].append("Provide more detailed explanation")
        if not tools_used:
            reflection["suggestions"].append("Use tools for concrete actions")
        
        self.confidence_history.append(reflection)
        self._save()
        
        return reflection
    
    # ==================== Confidence Scoring ==================== #
    
    def calculate_confidence(self, question: str, response: str, context: Dict = None) -> float:
        """Calculate confidence score for a response."""
        confidence = 1.0
        context = context or {}
        
        # 1. Question clarity
        if len(question) < 10:
            confidence -= 0.1  # Very short question
        
        # 2. Response completeness
        if len(response) < 50:
            confidence -= 0.2
        elif len(response) > 500:
            confidence += 0.1  # Detailed response
        
        # 3. Tool usage
        tools_used = context.get("tools_used", [])
        if tools_used:
            confidence += 0.1  # Used tools = more reliable
        
        # 4. Past mistakes
        similar_mistakes = self._find_similar_mistakes(question)
        if similar_mistakes:
            confidence -= 0.1 * len(similar_mistakes)
        
        # 5. Hedging language
        hedging = ["maybe", "perhaps", "might", "possibly", "I think"]
        for word in hedging:
            if word in response.lower():
                confidence -= 0.05
        
        return max(0.0, min(1.0, confidence))
    
    # ==================== Error Recovery ==================== #
    
    def record_mistake(self, question: str, wrong_response: str, error: str, correct_response: str = None) -> None:
        """Record a mistake for learning."""
        mistake = {
            "timestamp": datetime.now().isoformat(),
            "question": question[:200],
            "wrong_response": wrong_response[:200],
            "error": error,
            "correct_response": correct_response[:200] if correct_response else None,
        }
        self.mistakes.append(mistake)
        self._save()
    
    def _find_similar_mistakes(self, question: str) -> List[Dict]:
        """Find similar past mistakes."""
        similar = []
        question_lower = question.lower()
        
        for mistake in self.mistakes[-50:]:  # Check last 50
            mistake_q = mistake.get("question", "").lower()
            # Simple word overlap
            q_words = set(question_lower.split())
            m_words = set(mistake_q.split())
            overlap = len(q_words & m_words)
            
            if overlap >= 3:  # At least 3 words in common
                similar.append(mistake)
        
        return similar
    
    def get_recovery_suggestion(self, error: str) -> str:
        """Get suggestion for recovering from an error."""
        error_lower = error.lower()
        
        if "timeout" in error_lower:
            return "Try with a simpler request or use a faster model"
        elif "rate limit" in error_lower:
            return "Wait a moment and retry, or switch to a different API key"
        elif "invalid" in error_lower or "error" in error_lower:
            return "Check input format and try again with corrected parameters"
        elif "not found" in error_lower:
            return "Verify the path/name exists and try again"
        else:
            return "Try a different approach or ask for help"
    
    # ==================== Knowledge Validation ==================== #
    
    def validate_knowledge(self, claim: str, sources: List[str] = None) -> Dict[str, Any]:
        """Validate a knowledge claim."""
        validation = {
            "claim": claim[:200],
            "is_valid": True,
            "confidence": 0.8,
            "sources": sources or [],
            "warnings": [],
        }
        
        # Check for common false patterns
        false_patterns = [
            "always", "never", "100%", "guaranteed",
            "impossible", "definitely", "absolutely",
        ]
        
        for pattern in false_patterns:
            if pattern in claim.lower():
                validation["warnings"].append(f"Absolute claim detected: '{pattern}'")
                validation["confidence"] -= 0.1
        
        # Check if claim has sources
        if not sources:
            validation["warnings"].append("No sources provided")
            validation["confidence"] -= 0.2
        
        validation["is_valid"] = validation["confidence"] > 0.5
        
        return validation
    
    # ==================== Learning ==================== #
    
    def learn_from_interaction(self, question: str, response: str, feedback: str = None) -> None:
        """Learn from an interaction."""
        key = question[:50].lower()
        
        if key not in self.knowledge_base:
            self.knowledge_base[key] = {
                "question": question[:100],
                "best_response": response[:200],
                "feedback": feedback,
                "count": 1,
                "last_used": datetime.now().isoformat(),
            }
        else:
            self.knowledge_base[key]["count"] += 1
            self.knowledge_base[key]["last_used"] = datetime.now().isoformat()
            if feedback:
                self.knowledge_base[key]["feedback"] = feedback
        
        self._save()
    
    def get_learned_response(self, question: str) -> Optional[str]:
        """Get a previously learned response."""
        key = question[:50].lower()
        
        if key in self.knowledge_base:
            entry = self.knowledge_base[key]
            if entry.get("count", 0) >= 3:  # Only use if seen 3+ times
                return entry.get("best_response")
        
        return None
    
    # ==================== Output Validation ==================== #
    
    def validate_output(self, output: str, expected_type: str = "text") -> Dict[str, Any]:
        """Validate AI output before showing to user."""
        validation = {
            "is_valid": True,
            "issues": [],
            "suggestions": [],
        }
        
        if expected_type == "text":
            # Check for empty/whitespace-only
            if not output.strip():
                validation["is_valid"] = False
                validation["issues"].append("Empty output")
            
            # Check for error markers
            error_markers = ["error", "failed", "cannot", "unable", "invalid"]
            for marker in error_markers:
                if marker in output.lower():
                    validation["suggestions"].append(f"Contains error marker: '{marker}'")
        
        elif expected_type == "code":
            # Check for syntax errors
            if output.count("{") != output.count("}"):
                validation["issues"].append("Mismatched braces")
                validation["is_valid"] = False
            if output.count("(") != output.count(")"):
                validation["issues"].append("Mismatched parentheses")
                validation["is_valid"] = False
        
        elif expected_type == "json":
            try:
                json.loads(output)
            except json.JSONDecodeError as e:
                validation["is_valid"] = False
                validation["issues"].append(f"Invalid JSON: {str(e)[:50]}")
        
        return validation
    
    # ==================== Smart Retry ==================== #
    
    def should_retry(self, error: str, attempt: int, max_attempts: int = 3) -> bool:
        """Determine if should retry after error."""
        if attempt >= max_attempts:
            return False
        
        error_lower = error.lower()
        
        # Retryable errors
        retryable = [
            "timeout",
            "rate limit",
            "temporary",
            "connection",
            "network",
        ]
        
        for pattern in retryable:
            if pattern in error_lower:
                return True
        
        return False
    
    def get_retry_strategy(self, error: str, attempt: int) -> Dict[str, Any]:
        """Get retry strategy."""
        strategy = {
            "should_retry": self.should_retry(error, attempt),
            "wait_seconds": 0,
            "change_approach": False,
            "suggestion": "",
        }
        
        error_lower = error.lower()
        
        if "timeout" in error_lower:
            strategy["wait_seconds"] = 2 ** attempt  # Exponential backoff
            strategy["suggestion"] = "Increase timeout or simplify request"
        elif "rate limit" in error_lower:
            strategy["wait_seconds"] = 5 * attempt
            strategy["suggestion"] = "Wait longer or use different API key"
        elif "invalid" in error_lower:
            strategy["change_approach"] = True
            strategy["suggestion"] = "Try different input format"
        
        return strategy
    
    # ==================== Stats ==================== #
    
    def get_stats(self) -> Dict[str, Any]:
        """Get smart AI statistics."""
        return {
            "total_mistakes": len(self.mistakes),
            "knowledge_entries": len(self.knowledge_base),
            "confidence_entries": len(self.confidence_history),
            "avg_confidence": self._avg_confidence(),
            "most_common_errors": self._most_common_errors(),
        }
    
    def _avg_confidence(self) -> float:
        """Calculate average confidence."""
        if not self.confidence_history:
            return 0.0
        total = sum(c.get("confidence", 0) for c in self.confidence_history)
        return total / len(self.confidence_history)
    
    def _most_common_errors(self) -> List[str]:
        """Get most common error types."""
        error_counts = {}
        for mistake in self.mistakes[-50:]:
            error = mistake.get("error", "unknown")
            error_counts[error] = error_counts.get(error, 0) + 1
        
        return sorted(error_counts.keys(), key=lambda x: error_counts[x], reverse=True)[:5]


# Global instance
smart_ai = SmartAI()
