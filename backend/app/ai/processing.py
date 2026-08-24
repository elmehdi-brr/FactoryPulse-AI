from enum import StrEnum


class AIProcessingStatus(StrEnum):
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    SKIPPED = "skipped"
    FAILED = "failed"