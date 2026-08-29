from enum import Enum
from dataclasses import dataclass

class ResultCategory(str, Enum):
    MATCHED = "MATCHED"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    UNMATCHED = "UNMATCHED"
    DUPLICATE = "DUPLICATE"

@dataclass
class ClassificationResult:
    """
    Represents the final classification category of a candidate match.
    """
    category: ResultCategory

def classify_result(confidence_score: float, is_duplicate: bool) -> ClassificationResult:
    """
    Classifies a candidate match into exactly one of the four categories.
    
    Rules:
    - DUPLICATE: When the same invoice is associated with more than one eligible candidate.
    - MATCHED: confidence_score >= 85.0
    - NEEDS_REVIEW: confidence_score >= 60.0 and < 85.0
    - UNMATCHED: confidence_score < 60.0
    """
    if is_duplicate:
        return ClassificationResult(category=ResultCategory.DUPLICATE)
        
    if confidence_score >= 85.0:
        return ClassificationResult(category=ResultCategory.MATCHED)
    elif confidence_score >= 60.0:
        return ClassificationResult(category=ResultCategory.NEEDS_REVIEW)
    else:
        return ClassificationResult(category=ResultCategory.UNMATCHED)
