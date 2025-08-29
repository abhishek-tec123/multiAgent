from dataclasses import dataclass, field
from typing import Optional, List, Dict


# @dataclass
# class PipelineContext:
#     query: str
#     response: Optional[str] = None
#     summary: Optional[str] = None
#     subject: Optional[str] = None
#     phone: Optional[str] = None
#     email_status: Optional[str] = None
#     sms_status: Optional[str] = None
#     trace: List[dict] = field(default_factory=list)
#     meta: Dict[str, object] = field(default_factory=dict)


@dataclass
class PipelineContext:
    query: str = ""
    response: Optional[str] = None
    summary: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None        # Add this
    phone: Optional[str] = None
    to_email: Optional[str] = None    # Add this
    email_status: Optional[str] = None
    sms_status: Optional[str] = None
    url: Optional[str] = None
    trace: List[dict] = field(default_factory=list)
    meta: Dict[str, object] = field(default_factory=dict)
