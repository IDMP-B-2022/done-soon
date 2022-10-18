from dataclasses import dataclass, field
from typing import Optional
from bson.objectid import ObjectId


@dataclass
class StatisticsSnapshot:
    """
    Class representing the statistics output at a single time"""
    percent: int  # percentage of time-limit (TL) at which the capture occurs
    features: dict[str, float] = field(default_factory=dict)


@dataclass
class Problem:
    """
    Class containing all information about a problem, and its data (label, features)
    """
    _id: ObjectId
    mzn: str
    dzn: Optional[str]
    time_limit: Optional[str]
    generated_features: bool = False
    generated_label: bool = False
    claimed_features_generation: bool = False
    claimed_label_generation: bool = False
    type: str = 'SAT'
    time_to_solution: float or None = None


    # Label/Features
    solved: bool = False  # solved within TL
    statistics: list[StatisticsSnapshot] = field(default_factory=list)
