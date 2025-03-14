import yaml
from typing import Any, Dict
from string import Template


def load_prompt(path: str) -> Dict:
    try:
        with open(path, "r") as prompt_file:
            prompt = yaml.safe_load(prompt_file)
            return prompt
    except Exception:
        raise Exception(f"Cannot load yaml from path: {path}")


def load_variables(obj: Any, variables: Dict[str, str]) -> Any:
    if isinstance(obj, dict):
        return {k: load_variables(v, variables) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [load_variables(item, variables) for item in obj]
    elif isinstance(obj, str):
        return Template(obj).safe_substitute(variables)
    else:
        return obj


def format(prompt: Dict) -> str:
    results = []
    for key, value in prompt.items():
        results.append(f"<{key.upper()}>\n{value}</{key.upper()}>\n")

    return "".join(results)
