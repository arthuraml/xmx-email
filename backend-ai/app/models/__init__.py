"""
Modelos Pydantic para o backend AI
"""

from .email import (
    EmailPriority,
    EmailMetadata,
    EmailInput,
    EmailSummary,
    EmailBatch
)

from .response import (
    DecisionType,
    EmailType,
    ResponseTone,
    ProcessingStatus,
    SuggestedResponse,
    GeminiDecision,
    EmailProcessingResult,
    BatchProcessingResult,
    EmailStatusResponse
)


__all__ = [
    # Email models
    "EmailPriority",
    "EmailMetadata",
    "EmailInput",
    "EmailSummary",
    "EmailBatch",
    
    # Response models
    "DecisionType",
    "EmailType",
    "ResponseTone",
    "ProcessingStatus",
    "SuggestedResponse",
    "GeminiDecision",
    "EmailProcessingResult",
    "BatchProcessingResult",
    "EmailStatusResponse"
]