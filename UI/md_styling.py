def bold(text: str) -> str:
    return f"**{text}**"

def underline(text: str) -> str:
    return f"__{text}__"

def spoiler(text: str) -> str:
    return f"||{text}||"

def inline_code(text: str) -> str:
    return f"\'{text}\'"

def multiline_code(text: str, language: str = 'python') -> str:
    return f"\'\'\'{language}\n{text}\'\'\'"