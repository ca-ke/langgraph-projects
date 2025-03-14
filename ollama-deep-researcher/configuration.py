import os

from dataclasses import dataclass, fields
from typing import Optional

from langchain_core.runnables import RunnableConfig


@dataclass(kw_only=True)
class Configuration:
    max_web_research_loops: int = int(os.environ.get("MAX_WEB_RESEARCH_LOOPS", "3"))
    ollama_model: str = os.environ.get("OLLAMA_MODEL", "")
    ollama_base_url: str = os.environ.get("OLLAMA_BASE_URL", "")

    @classmethod
    def from_runnable_config(
        cls,
        config: Optional[RunnableConfig],
    ) -> "Configuration":
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )
        values = {}
        for f in fields(cls):
            if f.init:
                env_value = os.environ.get(f.name.upper())
                config_value = configurable.get(f.name)
                value = env_value if env_value is not None else config_value
                if f.type is int and value is not None:
                    value = int(value)
                values[f.name] = value
        return cls(**{k: v for k, v in values.items() if v})
