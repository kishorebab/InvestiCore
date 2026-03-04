from typing import List


class ToolValidator:
    @staticmethod
    def verify_tools_exist(steps: List[dict], registry: List[str]) -> None:
        missing = []
        for step in steps:
            name = step.get("toolName")
            if name not in registry:
                missing.append(name)
        if missing:
            names = ", ".join(str(n) for n in missing)
            raise ValueError(f"Tool(s) not in registry: {names}")