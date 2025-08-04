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

from .prompt import (
    DecisionCriteria,
    PromptCreate,
    PromptUpdate,
    PromptResponse,
    PromptList,
    PromptTestRequest,
    PromptTestResponse
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
    "EmailStatusResponse",
    
    # Prompt models
    "DecisionCriteria",
    "PromptCreate",
    "PromptUpdate",
    "PromptResponse",
    "PromptList",
    "PromptTestRequest",
    "PromptTestResponse"
]