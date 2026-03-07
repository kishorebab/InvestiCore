from dataclasses import dataclass

@dataclass
class ToolDefinition:
    name: str
    description: str
    arguments: dict  # JSON Schema for arguments

class ToolValidator:
    def __init__(self, known_tools: dict[str, ToolDefinition]):
        self.known_tools = known_tools

    def get_definitions(self, registry: list[str]) -> list[ToolDefinition]:
        return [self.known_tools[t] for t in registry if t in self.known_tools]

    def is_valid(self, tool_name: str) -> bool:
        return tool_name in self.known_tools