# Deploying to Streamlit Cloud with theme_switcher Package

## Project Structure

Your project should be structured like this:

```
your-repo/
├── app.py                          # Main Streamlit app
├── requirements.txt                # Python dependencies
├── .streamlit/
│   └── secrets.toml               # MongoDB credentials (NOT in git)
├── theme_switcher/                # Your theme package
│   ├── __init__.py
│   ├── theme_switcher.py
│   ├── theme_base.css
│   └── themes/
│       ├── retro.css
│       ├── glassmorphism.css
│       ├── brutalist.css
│       └── ... (other themes)
├── core/
│   ├── __init__.py
│   ├── state.py
│   ├── scoring.py
│   └── ...
├── ui/
│   ├── __init__.py
│   ├── auth.py
│   ├── components.py
│   └── ...
└── data/
    ├── __init__.py
    ├── deck_store.py
    └── ...
```

## Step 1: Prepare theme_switcher Package

Since you installed theme_switcher as an editable package locally (`pip install -e .`), 
you need to make it work on Streamlit Cloud.

### Option A: Include as Local Package (Recommended)

Just include the `theme_switcher/` folder in your repo. Streamlit Cloud will use it 
as a local module automatically.

**No changes needed!** The import `from theme_switcher import quick_theme_setup` will work.

### Option B: Install from Git (Advanced)

If you want to keep theme_switcher separate, you can:

1. Create a separate Git repo for theme_switcher
2. Add to `requirements.txt`:
```
git+https://github.com/yourusername/theme_switcher.git
```

## Step 2: Update requirements.txt

Make sure all dependencies are listed:

```txt
streamlit>=1.30.0
pymongo>=4.0.0
pandas
```

**Do NOT include theme_switcher in requirements.txt if using Option A**

## Step 3: Fix app.py Usage

In `app.py`, use the package WITHOUT specifying themes_dir:

```python
from theme_switcher import quick_theme_setup

# CORRECT - Let package find its own themes
quick_theme_setup(default_theme='retro')

# WRONG - Don't specify paths
# quick_theme_setup(default_theme='retro', themes_dir='../theme_switcher/themes')
# quick_theme_setup(default_theme='retro', themes_dir='theme_switcher/themes')
```

The `quick_theme_setup()` function automatically finds themes using:
```python
package_dir = Path(__file__).parent  # Gets theme_switcher directory
themes_dir = package_dir / "themes"  # Always looks in package's themes folder
```

## Step 4: Verify Package Structure

Make sure `theme_switcher/__init__.py` exports the function:

```python
"""Theme switcher package for Streamlit apps"""
from .theme_switcher import ThemeSwitcher, quick_theme_setup

__version__ = "0.1.0"
__all__ = ["ThemeSwitcher", "quick_theme_setup"]
```

## Step 5: Configure Streamlit Cloud

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Add theme_switcher package"
   git push
   ```

2. **Deploy on Streamlit Cloud:**
   - Go to share.streamlit.io
   - Click "New app"
   - Select your repository
   - Main file: `app.py`
   - Click "Deploy"

3. **Add Secrets:**
   In Streamlit Cloud dashboard → Settings → Secrets:
   ```toml
   [mongo]
   uri = "mongodb+srv://username:password@cluster.mongodb.net/"
   db_name = "your_database_name"
   ```

## Troubleshooting

### "ModuleNotFoundError: No module named 'theme_switcher'"

**Cause:** Package not properly structured or missing `__init__.py`

**Fix:**
1. Verify `theme_switcher/__init__.py` exists
2. Check that you pushed the entire `theme_switcher/` folder to Git
3. Make sure folder structure matches the example above

### "FileNotFoundError: theme_base.css not found"

**Cause:** CSS files not included in the package

**Fix:**
1. Verify all CSS files are in Git (not in `.gitignore`)
2. Check `theme_switcher/theme_base.css` exists
3. Verify `theme_switcher/themes/*.css` exist

### Themes not loading

**Cause:** CSS files in wrong location

**Fix:**
```
theme_switcher/
├── theme_base.css      ← Must be here
└── themes/
    ├── retro.css       ← Must be here
    ├── luxury.css
    └── ...
```

### "Cannot read properties of undefined"

**Cause:** Trying to specify themes_dir path manually

**Fix:** Remove the `themes_dir` parameter:
```python
# Before (wrong):
quick_theme_setup(default_theme='retro', themes_dir='theme_switcher/themes')

# After (correct):
quick_theme_setup(default_theme='retro')
```

## Local Development vs Production

### Local Development

When developing locally with editable install:
```bash
cd /path/to/streamlit  # Parent directory
pip install -e .       # Install theme_switcher package
cd dna-study-byui      # Your app directory
streamlit run app.py
```

### Streamlit Cloud

Streamlit Cloud automatically:
1. Finds `theme_switcher/` as a local module
2. Imports it like any other package
3. Uses relative paths within the package

**No special configuration needed!**

## Best Practices

1. **Keep theme_switcher self-contained:**
   - All CSS files inside theme_switcher/
   - No external dependencies
   - Uses `Path(__file__).parent` for paths

2. **Don't hardcode paths in app.py:**
   ```python
   # Good
   quick_theme_setup(default_theme='retro')
   
   # Bad
   quick_theme_setup(themes_dir='/absolute/path/themes')
   ```

3. **Version control:**
   ```bash
   # Include in Git:
   theme_switcher/
   ├── __init__.py
   ├── theme_switcher.py
   ├── theme_base.css
   └── themes/*.css
   
   # Exclude from Git (.gitignore):
   __pycache__/
   *.pyc
   .streamlit/secrets.toml
   ```

4. **Test locally before deploying:**
   ```python
   # Test that package can find themes
   from theme_switcher import quick_theme_setup
   import streamlit as st
   
   st.set_page_config(page_title="Test")
   quick_theme_setup()
   st.write("If you see themes, it works!")
   ```

## Example .gitignore

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/

# Streamlit
.streamlit/secrets.toml

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Don't ignore theme files!
# theme_switcher/ should NOT be in .gitignore
```

## Deployment Checklist

- [ ] `theme_switcher/` folder in repository
- [ ] `theme_switcher/__init__.py` exists
- [ ] All CSS files committed to Git
- [ ] `app.py` uses `quick_theme_setup(default_theme='retro')` without paths
- [ ] `requirements.txt` updated
- [ ] Secrets configured in Streamlit Cloud
- [ ] Repository pushed to GitHub
- [ ] App deployed on Streamlit Cloud
- [ ] Themes visible in deployed app

## Summary

**The key insight:** When you use `theme_switcher` as a package (with proper `__init__.py`), 
it's automatically a local module. Streamlit Cloud treats it just like any other Python 
package in your repo. The package uses `Path(__file__).parent` internally to find its 
own files, so it works everywhere without configuration!
