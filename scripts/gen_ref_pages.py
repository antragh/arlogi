import re
import sys
from pathlib import Path

# Constants
FILE = Path(__file__).resolve()
ROOT_DIR = FILE.parents[2]
PACKAGE_DIR = ROOT_DIR / "src"
REFERENCE_DIR = ROOT_DIR / "docs" / "reference"


def extract_classes_and_functions(filepath: Path) -> tuple[list[str], list[str]]:
    """Extracts class and function names from a given Python file."""
    content = filepath.read_text(encoding="utf-8")

    # Simple regex for classes and functions.
    # Not perfect but good enough for this automation.
    class_pattern = r"(?:^|\n)class\s(\w+)(?:\(|:)"
    func_pattern = r"(?:^|\n)def\s(\w+)\("

    classes = re.findall(class_pattern, content)
    functions = [f for f in re.findall(func_pattern, content) if not f.startswith("_")]

    return classes, functions


def create_markdown(md_filepath: Path, module_path: str, classes: list, functions: list):
    """Creates a Markdown file containing the API reference for the given Python module."""

    title = module_path.split('.')[-1].replace('_', ' ').capitalize()

    md_content = [
        f"# {title}\n",
        f"::: {module_path}",
        "    options:",
        "      show_root_heading: false",
        "      show_source: true",
    ]

    # We use the module-level mkdocstrings instead of individual classes/functions
    # as it handles everything correctly, including docstrings and signatures.

    md_text = "\n".join(md_content) + "\n"

    md_filepath.parent.mkdir(parents=True, exist_ok=True)
    md_filepath.write_text(md_text, encoding="utf-8")

    return md_filepath.relative_to(ROOT_DIR / "docs")


def create_nav_menu_yaml(nav_items: list[Path]):
    """Prints a YAML-friendly navigation structure."""

    # Simple nested structure generation
    nav_tree = {}

    for item_path in nav_items:
        parts = Path(item_path).parts
        # parts will be like ('reference', 'cpaiops', 'api', 'client.md')

        current = nav_tree
        for part in parts[:-1]:
            name = part.replace('_', ' ').capitalize()
            if name not in current:
                current[name] = {}
            current = current[name]

        file_name = parts[-1].replace('.md', '').replace('_', ' ').capitalize()
        current[file_name] = str(item_path)

    def _format_nav(d, indent=0):
        lines = []
        for key, value in sorted(d.items()):
            if isinstance(value, dict):
                lines.append(f"{'  ' * indent}- {key}:")
                lines.extend(_format_nav(value, indent + 1))
            else:
                lines.append(f"{'  ' * indent}- {key}: {value}")
        return lines

    print("\nScan complete. Update your mkdocs.yml 'nav' section with:\n")
    print("\n".join(_format_nav(nav_tree)))


def main():
    """Main function to generate reference documentation."""
    nav_items = []

    # Ensure src is in path for any imports
    sys.path.insert(0, str(PACKAGE_DIR))

    for py_filepath in PACKAGE_DIR.rglob("*.py"):
        rel_parts = py_filepath.relative_to(PACKAGE_DIR).parts
        if any(part.startswith("_") and part != "__init__.py" for part in rel_parts):
            continue

        classes, functions = extract_classes_and_functions(py_filepath)

        if classes or functions:
            py_filepath_rel = py_filepath.relative_to(PACKAGE_DIR)
            md_filepath = REFERENCE_DIR / py_filepath_rel.with_suffix(".md")

            # module_path calculation: cpaiops.api.client
            module_path = py_filepath_rel.with_suffix("").as_posix().replace("/", ".")

            if py_filepath.name == "__init__.py":
                module_path = py_filepath_rel.parent.as_posix().replace("/", ".")

            md_rel_filepath = create_markdown(md_filepath, module_path, classes, functions)
            nav_items.append(md_rel_filepath)

    print(f"Generated {len(nav_items)} files.")
    create_nav_menu_yaml(sorted(nav_items))


if __name__ == "__main__":
    main()
