import numpy as np
from dataclasses import dataclass
from models.db_models import HighwayClassification, HighwayCondition, HighwayDifficult, UnloadingDifficult

@dataclass
class RiskFactors:
    # Base risk scores for highway classification (0-1 scale)
    HIGHWAY_CLASS_RISK = {
        HighwayClassification.HIGHWAY: 0.2,  # Most controlled, lowest risk
        HighwayClassification.FREEWAY: 0.3,
        HighwayClassification.LOCAL: 0.6,  # More intersections, higher risk
        HighwayClassification.RURAL: 0.8  # Least controlled, highest risk
    }

    # Condition multipliers
    HIGHWAY_CONDITION_MULT = {
        HighwayCondition.EXCELLENT: 0.7,
        HighwayCondition.GOOD: 1.0,
        HighwayCondition.FAIR: 1.3,
        HighwayCondition.POOR: 1.8
    }

    # Difficulty multipliers
    HIGHWAY_DIFFICULTY_MULT = {
        HighwayDifficult.EASY: 0.8,
        HighwayDifficult.NORMAL: 1.0,
        HighwayDifficult.HARD: 1.5
    }

    # Unloading difficulty multipliers
    UNLOADING_DIFFICULTY_MULT = {
        UnloadingDifficult.EASY: 0.8,
        UnloadingDifficult.NORMAL: 1.0,
        UnloadingDifficult.HARD: 1.4
    }


def calculate_trouble_score(
        highway_class: HighwayClassification,
        highway_condition: HighwayCondition,
        highway_difficulty: HighwayDifficult,
        unloading_difficulty: UnloadingDifficult,
        driver_experience: float,
        distance: float,
        base_risk: float = 0.1
) -> float:
    """
    Calculate the trouble score for a trip based on various risk factors.

    Args:
        highway_class: Classification of the highway
        highway_condition: Condition of the highway
        highway_difficulty: Difficulty level of the highway
        unloading_difficulty: Difficulty level of unloading
        driver_experience: Years of experience (used for risk reduction)
        distance: Trip distance in km (longer trips increase risk)
        base_risk: Base risk score (default 0.1)

    Returns:
        Float between 0 and 1 representing the trouble score
    """
    risk_factors = RiskFactors()

    # Calculate base risk from highway classification
    base_class_risk = risk_factors.HIGHWAY_CLASS_RISK[highway_class]

    # Apply condition multiplier
    condition_adjusted = base_class_risk * risk_factors.HIGHWAY_CONDITION_MULT[highway_condition]

    # Apply difficulty multipliers
    difficulty_adjusted = condition_adjusted * (
            risk_factors.HIGHWAY_DIFFICULTY_MULT[highway_difficulty] *
            risk_factors.UNLOADING_DIFFICULTY_MULT[unloading_difficulty]
    )

    # Experience reduction factor (exponential decay)
    # More experienced drivers have lower risk, but with diminishing returns
    experience_factor = np.exp(-0.1 * driver_experience)  # Reduces risk up to ~63% for very experienced drivers

    # Distance factor (longer trips have higher risk)
    distance_factor = 1 + np.log1p(distance / 1000)

    # Combine all factors
    final_score = base_risk * difficulty_adjusted * experience_factor * distance_factor

    # Ensure score is between 0 and 1
    return min(1.0, max(0.0, final_score))
