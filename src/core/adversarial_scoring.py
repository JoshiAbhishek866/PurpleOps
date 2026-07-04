"""
Adversarial Self-Improvement Scoring for PurpleOps

Tracks Red vs Blue performance with ELO-like ratings.
After Blue patches a vulnerability, auto-queues Red to re-probe the patch.
Measures whether the system is actually getting better over time.

Fail-graceful: stores in MongoDB, falls back to in-memory if DB unavailable.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timezone
from collections import defaultdict

logger = logging.getLogger(__name__)

# Default ELO rating for new agents
DEFAULT_RATING = 1200
# K-factor: how much a single round affects the rating
K_FACTOR = 32


class AdversarialScoring:
    """
    Tracks Red vs Blue agent performance with ELO ratings.

    After each campaign:
    1. Score Red: Did it find vulns that Blue hadn't already patched?
    2. Score Blue: Did it successfully mitigate Red's findings?
    3. Update ratings based on the outcome
    4. If Blue patched something → auto-queue Red to re-probe
    """

    def __init__(self, db=None):
        self.db = db
        # In-memory fallback
        self._ratings: Dict[str, float] = defaultdict(lambda: DEFAULT_RATING)
        self._history: List[Dict] = []

    # ==================== ELO Rating ====================

    def _expected_score(self, rating_a: float, rating_b: float) -> float:
        """Calculate expected score for player A against player B."""
        return 1.0 / (1.0 + 10 ** ((rating_b - rating_a) / 400))

    def update_ratings(
        self,
        red_score: float,
        blue_score: float,
        target: str,
        campaign_id: str,
    ) -> Dict:
        """
        Update Red and Blue ratings based on a campaign outcome.

        Args:
            red_score: 0.0 to 1.0 — how well Red did (1.0 = found many unpatched vulns)
            blue_score: 0.0 to 1.0 — how well Blue did (1.0 = mitigated everything)
            target: The target URL/domain
            campaign_id: Campaign identifier

        Returns:
            Dict with old and new ratings for both agents.
        """
        red_key = f"red_{target}"
        blue_key = f"blue_{target}"

        old_red = self._ratings[red_key]
        old_blue = self._ratings[blue_key]

        # Calculate expected scores
        expected_red = self._expected_score(old_red, old_blue)
        expected_blue = self._expected_score(old_blue, old_red)

        # Update ratings
        new_red = old_red + K_FACTOR * (red_score - expected_red)
        new_blue = old_blue + K_FACTOR * (blue_score - expected_blue)

        self._ratings[red_key] = new_red
        self._ratings[blue_key] = new_blue

        result = {
            "campaign_id": campaign_id,
            "target": target,
            "red": {"old_rating": round(old_red), "new_rating": round(new_red), "score": red_score},
            "blue": {"old_rating": round(old_blue), "new_rating": round(new_blue), "score": blue_score},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self._history.append(result)
        return result

    # ==================== Campaign Scoring ====================

    def score_campaign(
        self,
        red_result: Dict,
        blue_result: Dict,
        target: str,
        campaign_id: str,
    ) -> Dict:
        """
        Analyze campaign results and compute scores for Red and Blue.

        Logic:
        - Red scores high if it found vulnerabilities Blue hadn't addressed
        - Blue scores high if it mitigated/patched all Red's findings
        - A draw means both are equal — system is balanced
        """
        red_score = self._compute_red_score(red_result)
        blue_score = self._compute_blue_score(blue_result, red_result)

        ratings = self.update_ratings(red_score, blue_score, target, campaign_id)

        # Determine winner
        if red_score > blue_score + 0.1:
            ratings["winner"] = "red"
            ratings["interpretation"] = "Red found gaps in Blue's defenses — defenses need improvement"
        elif blue_score > red_score + 0.1:
            ratings["winner"] = "blue"
            ratings["interpretation"] = "Blue successfully defended — attack strategies need evolution"
        else:
            ratings["winner"] = "draw"
            ratings["interpretation"] = "Balanced engagement — both agents operating at similar capability"

        # Check if re-probe is recommended
        ratings["recommend_reprobe"] = red_score > 0.3  # If Red found anything, re-probe after Blue patches

        return ratings

    def _compute_red_score(self, red_result: Dict) -> float:
        """Score Red Agent performance (0.0 - 1.0)."""
        if not red_result:
            return 0.0

        score = 0.0
        result_str = str(red_result).lower()

        # Base points for finding something
        if "vulnerability" in result_str or "detected" in result_str:
            score += 0.3
        if "sql injection" in result_str:
            score += 0.2
        if "xss" in result_str:
            score += 0.2
        if "privilege" in result_str and "escalation" in result_str:
            score += 0.3

        # Deduct for being blocked
        if "rejected" in result_str or "blocked" in result_str:
            score -= 0.2

        return max(0.0, min(1.0, score))

    def _compute_blue_score(self, blue_result: Dict, red_result: Dict) -> float:
        """Score Blue Agent performance (0.0 - 1.0)."""
        if not blue_result:
            return 0.0

        score = 0.0
        result_str = str(blue_result).lower()

        # Points for taking defensive actions
        if "waf" in result_str and ("updated" in result_str or "rule" in result_str):
            score += 0.3
        if "security group" in result_str and "modified" in result_str:
            score += 0.2
        if "mitigation" in result_str:
            score += 0.2
        if "compliance" in result_str and "report" in result_str:
            score += 0.1

        # Bonus if Blue addressed Red's specific findings
        if red_result:
            red_str = str(red_result).lower()
            if "sql injection" in red_str and "sql" in result_str:
                score += 0.1
            if "xss" in red_str and ("xss" in result_str or "csp" in result_str):
                score += 0.1

        return max(0.0, min(1.0, score))

    # ==================== Auto-Requeue ====================

    def get_reprobe_targets(self) -> List[Dict]:
        """
        Get targets that should be re-probed by Red after Blue patched them.
        """
        targets = []
        for entry in reversed(self._history):
            if entry.get("recommend_reprobe") and entry.get("winner") == "red":
                targets.append({
                    "target": entry["target"],
                    "last_campaign_id": entry["campaign_id"],
                    "red_rating": entry["red"]["new_rating"],
                    "reason": "Red found vulnerabilities — re-probe after Blue patches",
                })
        return targets

    # ==================== Analytics ====================

    def get_ratings(self, target: str = None) -> Dict:
        """Get current ratings for all or a specific target."""
        if target:
            return {
                "red": round(self._ratings.get(f"red_{target}", DEFAULT_RATING)),
                "blue": round(self._ratings.get(f"blue_{target}", DEFAULT_RATING)),
                "target": target,
            }
        return {k: round(v) for k, v in self._ratings.items()}

    def get_improvement_trend(self, target: str = None) -> Dict:
        """
        Analyze whether agents are improving over time.
        """
        relevant = self._history
        if target:
            relevant = [h for h in relevant if h["target"] == target]

        if len(relevant) < 2:
            return {"data_points": len(relevant), "trend": "insufficient_data"}

        # Compare first half vs second half
        mid = len(relevant) // 2
        first_half_blue = sum(h["blue"]["score"] for h in relevant[:mid]) / mid
        second_half_blue = sum(h["blue"]["score"] for h in relevant[mid:]) / (len(relevant) - mid)

        improvement = second_half_blue - first_half_blue
        return {
            "data_points": len(relevant),
            "early_blue_avg": round(first_half_blue, 3),
            "recent_blue_avg": round(second_half_blue, 3),
            "improvement": round(improvement, 3),
            "trend": "improving" if improvement > 0.05 else ("declining" if improvement < -0.05 else "stable"),
        }

    async def persist_ratings(self):
        """Persist ratings to MongoDB for durability."""
        if not self.db:
            return
        try:
            for key, rating in self._ratings.items():
                await self.db.agent_ratings.update_one(
                    {"agent_key": key},
                    {"$set": {"rating": rating, "updated_at": datetime.now(timezone.utc).isoformat()}},
                    upsert=True,
                )
            if self._history:
                await self.db.scoring_history.insert_many(self._history[-10:])
                self._history = self._history[:-10]  # Keep last 10 in memory
        except Exception as e:
            logger.error(f"Failed to persist ratings: {e}")

    async def load_ratings(self):
        """Load ratings from MongoDB on startup."""
        if not self.db:
            return
        try:
            cursor = self.db.agent_ratings.find({})
            async for doc in cursor:
                self._ratings[doc["agent_key"]] = doc["rating"]
            logger.info(f"Loaded {len(self._ratings)} agent ratings")
        except Exception as e:
            logger.warning(f"Failed to load ratings: {e}")
