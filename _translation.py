import re
import json
from pathlib import Path

base_dir = Path(".").resolve()
translations_dir = Path(".").resolve() / "translations"
template_file = translations_dir / "en.template.json"
exclude_dirs = [".venv", ".vscode", ".git"]
function_name = "_translate"
tr_call_pattern = re.compile(r"(?:^|^[^\#\n]*[^\#\n\w\.])" + function_name + r"\([\n\s]*[rf]?\"([^\"]+)\"\)")
template_tr_call_pattern = re.compile(r"^[^\#\n]*PluginContext\._tr_template\([\n\s]*[rf]?\"([^\"]+)\",[\n\s]*filepath=__file__[\n\s]*\)")  # noqa: E501


def parse_file(path: Path) -> dict[str, str]:
    print(f"Parsing {path.relative_to(base_dir)}... ", end='')
    result = {}
    with open(path, 'r', encoding="utf-8") as f:
        for line in f:
            if (match := re.match(tr_call_pattern, line) or re.match(template_tr_call_pattern, line)) is not None:
                if (string := match.group(1)) not in result:
                    result[string] = string
    print(f"{len(result)} line{'' if len(result) == 1 else 's'} added")
    return result


def travel_dir(path: Path, output: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    for obj in path.iterdir():
        if obj.is_dir() and obj.name not in exclude_dirs:
            travel_dir(obj, output)
        elif obj.is_file() and not obj.is_symlink() and obj.name.endswith(".py"):
            if (strings := parse_file(obj)):
                relative_path = str(obj.relative_to(base_dir))
                output[relative_path] = strings
    return output


def generate_template():
    print("Generating the template file")
    template_file.parent.mkdir(parents=True, exist_ok=True)
    lines = travel_dir(base_dir, {})
    with open(template_file, 'w', encoding="utf-8") as f:
        json.dump(lines, f, ensure_ascii=False, indent=4)


def update_existing_with_template():
    lang_files = [
        f for f in translations_dir.iterdir()
        if f.is_file() and not f.is_symlink()
        and f.name.endswith(".json")
        and "template" not in f.name
    ]
    template: dict[str, dict[str, dict[str, str]]] = json.loads(template_file.read_text(encoding='utf-8'))
    global_missing = set()

    for langfile in lang_files:
        lang: dict[str, dict[str, dict[str, str]]] = json.loads(langfile.read_text(encoding='utf-8'))
        updated = lang.copy()
        print(f"Comparing the template with '{langfile}'...")

        for relative_path in lang:
            if relative_path not in template:
                print(f"\t- Removed unused file: {relative_path}")
                del updated[relative_path]
                continue
            if not lang[relative_path]:
                print(f"\t- Removed empty file: {relative_path}")
                del updated[relative_path]
                continue
            template_lines = set(template[relative_path].keys())
            lang_lines = set(lang[relative_path].keys())
            extra = lang_lines - template_lines
            missing = template_lines - lang_lines
            for line in extra:
                print(f"\t- Removed unused line: {relative_path} / '{line}'")
                del updated[relative_path][line]
            for line in missing:
                updated[relative_path][line] = line
                global_missing.add(f"{relative_path}: '{line}'")

        # missing files
        for relative_path in template:
            if relative_path not in lang:
                updated[relative_path] = dict()
                for line in template[relative_path]:
                    updated[relative_path][line] = line
                    global_missing.add(f"{relative_path}: '{line}'")

        updated = dict(sorted(updated.items()))
        for relpath in updated:
            sorted_relpath = {key: updated[relpath][key] for key in template[relpath]}
            updated[relpath] = sorted_relpath
        with open(langfile, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(updated, f, ensure_ascii=False, indent=4)
            f.write('\n')

    if global_missing:
        print("Missing translation lines:\n - ", end='')
        print('\n - '.join(global_missing))


if __name__ == "__main__":
    generate_template()
    update_existing_with_template()
