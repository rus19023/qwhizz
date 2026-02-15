# 🎨 Streamlit Modular Theme System

A drop-in theme system for Streamlit apps with 10 professional themes. No configuration needed - just import and use!

## 🚀 Quick Start

```python
from theme_switcher import quick_theme_setup

# Add this one line at the start of your app
quick_theme_setup()

# Build your app normally
st.title("My Themed App")
st.write("Theme switching is automatic!")
```

That's it! Your app now has a theme selector in the sidebar.

## 📦 Installation

1. **Copy files to your project:**
   ```
   your_project/
   ├── app.py
   ├── theme_switcher.py  ← Copy this
   └── themes/            ← Copy this folder
       ├── glassmorphism.css
       ├── cyberpunk.css
       ├── brutalist.css
       ├── luxury.css
       ├── academic.css
       ├── terminal.css
       ├── retro.css
       ├── corporate.css
       ├── nature.css
       └── neon.css
   ```

2. **Run your app:**
   ```bash
   streamlit run app.py
   ```

## 🎭 Available Themes

### Modern
- **✨ Glassmorphism** - Frosted glass with vibrant gradients
- **⚡ Cyberpunk** - Neon-lit dystopian future
- **🌃 Neon Nights** - Vibrant nightlife energy

### Bold
- **▪ Brutalist** - Raw, honest, no-nonsense design
- **🕹️ Retro Gaming** - 8-bit nostalgia

### Elegant
- **◇ Luxury Minimal** - Refined elegance and sophistication

### Professional
- **💼 Corporate** - Professional business aesthetic
- **📚 Academic** - Scholarly and refined

### Tech
- **💻 Terminal** - Classic green-screen aesthetic

### Organic
- **🌿 Nature** - Organic and calming

## 💡 Usage Examples

### Basic Usage
```python
from theme_switcher import quick_theme_setup

# Initialize with default theme
quick_theme_setup()

# Your app code
st.title("My App")
```

### Advanced Usage
```python
from theme_switcher import ThemeSwitcher

# Create theme switcher instance
ts = ThemeSwitcher(default_theme='cyberpunk')

# Render sidebar with custom title
ts.render_sidebar(
    title="🎨 Choose Your Style",
    show_description=True
)

# Apply the selected theme
ts.apply_theme()

# Get current theme info
info = ts.get_theme_info()
st.write(f"Current theme: {info['name']}")
```

### Set Default Theme
```python
from theme_switcher import quick_theme_setup

# Start with a specific theme
quick_theme_setup(default_theme='terminal')
```

## 🎨 Creating Custom Themes

### 1. Create CSS File

Create a new file in the `themes/` folder (e.g., `themes/myTheme.css`):

```css
/* My Custom Theme */
:root {
    --primary: #ff6b6b;
    --secondary: #4ecdc4;
}

.stApp {
    background: linear-gradient(135deg, var(--primary), var(--secondary));
    font-family: 'Your Font', sans-serif;
    color: white;
}

h1 {
    font-size: 3rem !important;
    color: var(--primary) !important;
}

.stButton > button {
    background: var(--primary) !important;
    color: white !important;
    border-radius: 8px !important;
    padding: 12px 24px !important;
}

/* Style all your components... */
```

### 2. Register Theme

Add your theme to `theme_switcher.py`:

```python
class ThemeSwitcher:
    THEMES = {
        # ... existing themes ...
        'mytheme': {
            'name': '🎨 My Theme',
            'description': 'My awesome custom theme',
            'fonts': 'https://fonts.googleapis.com/css2?family=Your+Font&display=swap',
            'category': 'Custom'
        }
    }
```

That's it! Your theme will appear in the sidebar automatically.

## 🛠️ Customization

### Hide Streamlit Branding

All themes automatically hide:
- Main menu
- Footer
- Header
- Deploy button

### Theme Persistence

Themes are stored in `st.session_state` and persist during the session. To add cross-session persistence, modify `theme_switcher.py` to use browser localStorage or a database.

### Sidebar Customization

```python
ts.render_sidebar(
    title="Pick a Vibe",           # Custom title
    show_description=False         # Hide descriptions
)
```

## 🎯 Use Cases

- **White-label apps** - Let clients choose their brand colors
- **User preferences** - Give users control over appearance
- **Context switching** - Different themes for dev/staging/prod
- **Accessibility** - Offer high-contrast or dyslexia-friendly options
- **Branding** - Match your company's style guide

## 📝 Component Styling

Each theme styles these Streamlit components:
- Headers (h1, h2, h3)
- Buttons
- Text inputs
- Text areas
- Select boxes
- Metrics
- Tabs
- Sliders
- Checkboxes
- Radio buttons
- Dividers (hr)
- Scrollbars

## 🐛 Troubleshooting

### Themes not appearing
- Make sure `themes/` folder is in the same directory as `theme_switcher.py`
- Check that CSS files have the correct names
- Verify fonts are loading (check browser console)

### Theme not applying
- Ensure `apply_theme()` is called after `render_sidebar()`
- Check for CSS conflicts with custom CSS in your app
- Try `st.rerun()` after changing themes

### Cyberpunk theme issues
The improved cyberpunk theme has better contrast and more pronounced neon effects. If you experience performance issues, the animations can be disabled in the CSS file.

## 📄 License

Feel free to use, modify, and distribute. No attribution required.

## 🤝 Contributing

Want to add a theme? 
1. Create the CSS file
2. Add it to the THEMES dict
3. Submit a PR or share it!

## ⭐ Credits

Built for the Streamlit community. Themes inspired by various design systems and aesthetics.

---

**Pro tip:** Mix and match CSS from different themes to create your own unique style!
