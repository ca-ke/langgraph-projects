import operator
from dataclasses import dataclass, field
from typing_extensions import Annotated
from typing import Optional


@dataclass(kw_only=True)
class SummaryState:
    research_topic: Optional[str] = field(default=None)
    search_query: Optional[str] = field(default=None)
    web_search_results: Annotated[list, operator.add] = field(default_factory=list)
    sources_gathered: Annotated[list, operator.add] = field(default_factory=list)
    research_loop_count: int = field(default=8)
    running_summary: Optional[str] = field(default=None)


@dataclass(kw_only=True)
class SummaryStateInput:
    research_topic: Optional[str] = field(default=None)


@dataclass(kw_only=True)
class SummaryStateOutput:
    running_summary: Optional[str] = field(default=None)
