"""
Path Helper - Debug script to find the correct themes_dir path
Run this in the same directory as your app.py to find the correct path
"""
from pathlib import Path
import os

print("=" * 60)
print("THEME SWITCHER PATH FINDER")
print("=" * 60)

# Show current working directory
cwd = Path.cwd()
print(f"\n1. Current Working Directory:")
print(f"   {cwd}")

# Show where this script is
script_dir = Path(__file__).parent
print(f"\n2. This Script's Directory:")
print(f"   {script_dir}")

# Check common theme directory locations
print(f"\n3. Looking for 'themes' directories...")

possible_paths = [
    Path('themes'),
    Path('theme_switcher/themes'),
    Path('../theme_switcher/themes'),
    cwd / 'themes',
    cwd / 'theme_switcher' / 'themes',
    cwd.parent / 'theme_switcher' / 'themes',
]

for path in possible_paths:
    resolved = path.resolve()
    exists = resolved.exists()
    status = "✅ FOUND" if exists else "❌ Not found"
    print(f"   {status}: {path}")
    if exists:
        # List CSS files in the directory
        css_files = list(resolved.glob("*.css"))
        if css_files:
            print(f"            CSS files found: {len(css_files)}")
            for css in css_files[:5]:  # Show first 5
                print(f"            - {css.name}")

print("\n" + "=" * 60)
print("RECOMMENDED USAGE:")
print("=" * 60)

# Find the correct path
for path in possible_paths:
    if path.resolve().exists():
        print(f"\nUse this in your app.py:")
        print(f"   quick_theme_setup(default_theme='retro', themes_dir='{path}')")
        break
else:
    print("\n⚠️  No themes directory found!")
    print("   Please ensure your themes are in one of these locations:")
    print("   - streamlit/dna-study-byui/themes/")
    print("   - streamlit/theme_switcher/themes/")
    