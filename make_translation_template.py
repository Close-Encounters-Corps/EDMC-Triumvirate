import re
import json
from pathlib import Path

base_dir = Path(".").resolve()
output_file = Path(".").resolve() / "translations" / "en.template.json"
exclude_dirs = [".venv", ".vscode", ".git"]
function_name = "_translate"
tr_call_pattern = re.compile(r"(?:^|^[^\#\n]*[^\#\n\w\.])" + function_name + r"\([\n\s]*[rf]?\"([^\"]+)\"\)")
template_tr_call_pattern = re.compile(r"^[^\#\n]*PluginContext\._tr_template\([\n\s]*[rf]?\"([^\"]+)\",[\n\s]*filepath=__file__[\n\s]*\)")  # noqa: E501


def parse_file(path: Path) -> dict[str, str]:
    result = {}
    with open(path, 'r', encoding="utf-8") as f:
        for line in f:
            if (match := re.match(tr_call_pattern, line) or re.match(template_tr_call_pattern, line)) is not None:
                if (string := match.group(1)) not in result:
                    result[string] = string
    return result


def travel_dir(path: Path, output: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    for obj in path.iterdir():
        if obj.is_dir() and obj.name not in exclude_dirs:
            travel_dir(obj, output)
        elif obj.is_file() and obj.name.endswith(".py"):
            if (strings := parse_file(obj)):
                relative_path = str(obj.relative_to(base_dir))
                output[relative_path] = strings
    return output


if __name__ == "__main__":
    output_file.parent.mkdir(parents=True, exist_ok=True)
    lines = travel_dir(base_dir, {})
    with open(output_file, 'w', encoding="utf-8") as f:
        json.dump(lines, f, ensure_ascii=False, indent=4)
