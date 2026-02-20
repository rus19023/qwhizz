"""
Modular Theme Switcher for Streamlit

A drop-in solution for adding professional themes to any Streamlit app.
Supports both built-in themes (from THEMES dict) and custom themes (CSS files in /themes directory).
"""

import streamlit as st
from pathlib import Path
import re


class ThemeSwitcher:
    """
    Manages theme switching in Streamlit apps.
    
    Supports two sources for themes:
    1. Built-in themes defined in THEMES dictionary
    2. Custom theme CSS files in the themes directory
    
    Usage:
        ts = ThemeSwitcher(default_theme='glassmorphism')
        ts.render_selector()  # Shows dropdown in sidebar
        ts.apply_theme()      # Applies the selected theme
    """
    
    # Built-in themes with embedded configuration
    THEMES = {
        'glassmorphism': {
            'name': '✨ Glassmorphism',
            'description': 'Modern glass effect with animated gradients',
            'css_file': 'glassmorphism.css',
            'fonts': 'https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Space+Mono:wght@400;700&display=swap'
        },
        'brutalist': {
            'name': '▪ Brutalist',
            'description': 'Raw concrete and bold geometry',
            'css_file': 'brutalist.css',
            'fonts': 'https://fonts.googleapis.com/css2?family=Courier+Prime:wght@400;700&family=Space+Grotesk:wght@300;400;700&family=JetBrains+Mono:wght@400;700&display=swap'
        },
        'luxury': {
            'name': '◇ Luxury Minimal',
            'description': 'Elegant sophistication',
            'css_file': 'luxury.css',
            'fonts': 'https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@300;400;500;600&family=Montserrat:wght@200;300;400;500&family=Cinzel:wght@400;500;600&display=swap'
        },
        'cyberpunk': {
            'name': '⚡ Cyberpunk',
            'description': 'Neon-lit dystopian future',
            'css_file': 'cyberpunk.css',
            'fonts': 'https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@300;500;700&display=swap'
        },
        'academic': {
            'name': '📚 Academic',
            'description': 'Classic serif typography',
            'css_file': 'academic.css',
            'fonts': 'https://fonts.googleapis.com/css2?family=Merriweather:wght@300;400;700&family=Source+Sans+Pro:wght@300;400;600&display=swap'
        },
        'terminal': {
            'name': '💻 Terminal',
            'description': 'Retro command line interface',
            'css_file': 'terminal.css',
            'fonts': 'https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;700&family=IBM+Plex+Mono:wght@400;600&display=swap'
        },
        'retro': {
            'name': '🕹️ Retro Gaming',
            'description': '8-bit nostalgia',
            'css_file': 'retro.css',
            'fonts': 'https://fonts.googleapis.com/css2?family=Press+Start+2P&family=VT323&display=swap'
        },
        'corporate': {
            'name': '💼 Corporate',
            'description': 'Professional business aesthetic',
            'css_file': 'corporate.css',
            'fonts': 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Roboto:wght@300;400;500;700&display=swap'
        },
        'nature': {
            'name': '🌿 Nature',
            'description': 'Organic and calming',
            'css_file': 'nature.css',
            'fonts': 'https://fonts.googleapis.com/css2?family=Quicksand:wght@300;400;600&family=Abril+Fatface&display=swap'
        },
        'neon': {
            'name': '🌃 Neon Nights',
            'description': 'Vibrant nightlife energy',
            'css_file': 'neon.css',
            'fonts': 'https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Bebas+Neue&display=swap'
        }
    }
    
    def __init__(self, default_theme='glassmorphism', themes_dir='themes', key_prefix='theme_switcher'):
        """
        Initialize the theme switcher.
        
        Args:
            default_theme: Theme key to use by default
            themes_dir: Directory containing CSS theme files (relative to caller or absolute)
            key_prefix: Unique prefix for widget keys to prevent conflicts
        """
        # Handle path resolution - if relative, resolve from current working directory
        themes_path = Path(themes_dir)
        if not themes_path.is_absolute():
            # Try relative to current working directory first
            if themes_path.exists():
                self.themes_dir = themes_path
            else:
                # Try relative to this file's directory
                self.themes_dir = Path(__file__).parent / themes_dir
        else:
            self.themes_dir = themes_path
            
        self.default_theme = default_theme
        self.key_prefix = key_prefix
        
        # Discover all available themes (built-in + custom)
        self.available_themes = self._discover_themes()
        
        # Initialize theme in session state with unique key
        theme_state_key = f'{self.key_prefix}_current_theme'
        if theme_state_key not in st.session_state:
            st.session_state[theme_state_key] = default_theme if default_theme in self.available_themes else list(self.available_themes.keys())[0]
    
    def _discover_themes(self):
        """
        Discover all available themes from both THEMES dict and filesystem.
        
        Returns:
            dict: Combined themes dictionary with all available themes
        """
        available = {}
        
        # Add built-in themes from THEMES dict
        for key, data in self.THEMES.items():
            available[key] = {
                'name': data.get('name', key.title()),
                'description': data.get('description', ''),
                'source': 'built-in',
                'css_file': data.get('css_file'),
                'fonts': data.get('fonts', '')
            }
        
        # Scan themes directory for custom CSS files
        if self.themes_dir.exists():
            for css_file in self.themes_dir.glob("*.css"):
                # Skip base and template files
                if css_file.stem in ['theme_base', 'theme_template']:
                    continue
                
                # If not already in built-in themes, add as custom theme
                if css_file.stem not in available:
                    available[css_file.stem] = {
                        'name': css_file.stem.replace('_', ' ').title(),
                        'description': 'Custom theme',
                        'source': 'custom',
                        'css_file': css_file.name,
                        'fonts': ''
                    }
        
        return available
    
    def render_selector(self, title="🎨 Theme Selector", location='sidebar', show_description=False):
        """
        Render theme selection dropdown.
        
        Must be called on EVERY script run for Streamlit widgets to persist.
        
        Args:
            title: Header text for the theme selector
            location: Where to render ('sidebar' or 'main')
            show_description: Whether to show theme descriptions below selector
        """
        container = st.sidebar if location == 'sidebar' else st
        theme_state_key = f'{self.key_prefix}_current_theme'
        
        with container:
            if st.secrets["app"]["show_theme_switcher"]:
                st.markdown(f"### {title}")                
                # Create options list with theme names
                theme_options = {key: data['name'] for key, data in self.available_themes.items()}
                theme_keys = list(theme_options.keys())
                theme_labels = list(theme_options.values())
                
                # Find current theme index
                try:
                    current_index = theme_keys.index(st.session_state[theme_state_key])
                except (ValueError, KeyError):
                    current_index = 0
                    st.session_state[theme_state_key] = theme_keys[0]
                
                # Dropdown selector with unique key
                loc = location or "main"
                selected_label = st.selectbox(
                    "Choose a theme:",
                    options=theme_labels,
                    index=current_index,
                    key=f"{self.key_prefix}_{loc}_selector_dropdown"
                )
                
                # Get the theme key from the selected label
                selected_theme = theme_keys[theme_labels.index(selected_label)]
                
                # Update session state if changed
                if st.session_state[theme_state_key] != selected_theme:
                    st.session_state[theme_state_key] = selected_theme
                    st.rerun()
                
                # Show description if requested
                if show_description:
                    theme_data = self.available_themes[st.session_state[theme_state_key]]
                    st.caption(f"_{theme_data['description']}_")
                    st.caption(f"Source: {theme_data['source']}")
    
    def apply_theme(self):
        """
        Apply the currently selected theme by injecting CSS.
        
        This loads:
        1. Base CSS (theme_base.css) if it exists
        2. Theme-specific CSS from either built-in or custom source
        3. Google Fonts if specified
        """
        theme_state_key = f'{self.key_prefix}_current_theme'
        theme_key = st.session_state[theme_state_key]
        theme_data = self.available_themes.get(theme_key)
        
        if not theme_data:
            st.error(f"Theme '{theme_key}' not found!")
            return
        
        # Step 1: Load base CSS
        base_css_content = self._load_base_css()
        
        # Step 2: Load theme CSS
        theme_css_content = self._load_theme_css(theme_data)
        
        # Step 3: Inject Google Fonts
        self._inject_fonts(theme_data)
        
        # Step 4: Combine and inject all CSS
        combined_css = f"""
<style>
/* === HIDE STREAMLIT BRANDING === */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}
.stDeployButton {{display: none;}}

/* === RESET === */
* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

/* === BASE CSS === */
{base_css_content}

/* === THEME CSS === */
{theme_css_content}
</style>
"""
        st.markdown(combined_css, unsafe_allow_html=True)
    
    def _load_base_css(self):
        """Load the base CSS file if it exists."""
        base_css_file = Path(__file__).parent / "theme_base.css"
        
        if base_css_file.exists():
            try:
                with open(base_css_file, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                st.warning(f"Could not load theme_base.css: {e}")
        
        return ""
    
    def _load_theme_css(self, theme_data):
        """Load the theme-specific CSS file."""
        css_file = self.themes_dir / theme_data['css_file']
        
        if not css_file.exists():
            st.error(f"Theme CSS file not found: {css_file}")
            return ""
        
        try:
            with open(css_file, 'r', encoding='utf-8') as f:
                css_content = f.read()
            
            # Remove @import statements for fonts (we handle separately)
            font_pattern = r'@import\s+url\([\'"]?(https://fonts\.googleapis\.com/[^\'")\s]+)[\'"]?\);?\s*'
            css_content = re.sub(font_pattern, '', css_content)
            
            # Remove @import for theme_base.css (we already loaded it)
            css_content = re.sub(r'@import\s+url\([\'"]?theme_base\.css[\'"]?\);?\s*', '', css_content)
            
            return css_content
            
        except Exception as e:
            st.error(f"Error loading theme CSS: {e}")
            return ""
    
    def _inject_fonts(self, theme_data):
        """Inject Google Fonts link tags."""
        # First check if fonts URL is in theme data
        fonts_url = theme_data.get('fonts', '')
        
        if fonts_url:
            st.markdown(
                f'<link href="{fonts_url}" rel="stylesheet">',
                unsafe_allow_html=True
            )
        else:
            # Try to extract from CSS file @import statements
            css_file = self.themes_dir / theme_data['css_file']
            if css_file.exists():
                try:
                    with open(css_file, 'r', encoding='utf-8') as f:
                        css_content = f.read()
                    
                    font_pattern = r'@import\s+url\([\'"]?(https://fonts\.googleapis\.com/[^\'")\s]+)[\'"]?\);?'
                    font_urls = re.findall(font_pattern, css_content)
                    
                    for font_url in font_urls:
                        st.markdown(
                            f'<link href="{font_url}" rel="stylesheet">',
                            unsafe_allow_html=True
                        )
                except:
                    pass


# Quick setup function (most common use case)
def quick_theme_setup(default_theme='glassmorphism', themes_dir='themes', key_prefix='theme_switcher'):
    """
    Quickest way to add themes to your app - just one line!
    
    This automatically:
    - Shows theme dropdown in sidebar
    - Applies the selected theme
    - No customization controls (keeps it simple)
    
    Args:
        default_theme: Theme to use by default
        themes_dir: Directory containing theme CSS files
        key_prefix: Unique prefix for widget keys (default: 'theme_switcher')
        
    Returns:
        ThemeSwitcher: Instance for advanced usage if needed
        
    Example:
        from theme_switcher import quick_theme_setup
        quick_theme_setup('cyberpunk')
    """
    return apply_theme(
        default_theme=default_theme,
        themes_dir=themes_dir,
        show_selector=True,
        allow_customization=False,
        key_prefix=key_prefix
    )


# Standalone function for simple usage
def apply_theme(default_theme='glassmorphism', themes_dir='themes', 
                show_selector=True, allow_customization=False,
                selector_location='sidebar', key_prefix='theme_switcher'):
    """
    Simple function-based API for applying themes.
    
    This is a convenience wrapper around ThemeSwitcher class.
    Uses session state to ensure only one instance exists.
    
    Args:
        default_theme: Default theme to use
        themes_dir: Directory containing theme CSS files
        show_selector: Whether to show theme selector
        allow_customization: Whether to enable theme customization controls
        selector_location: Where to show selector ('sidebar' or 'main')
        key_prefix: Unique prefix for this theme switcher instance
        
    Returns:
        ThemeSwitcher: Instance for advanced usage
    """
    # Use session state to ensure we only create one instance
    ts_key = f'_ts_instance_{key_prefix}'
    selector_rendered_key = f'_ts_selector_rendered_{key_prefix}'
    
    if ts_key not in st.session_state:
        st.session_state[ts_key] = ThemeSwitcher(
            default_theme=default_theme, 
            themes_dir=themes_dir,
            key_prefix=key_prefix
        )
        st.session_state[selector_rendered_key] = False
    
    ts = st.session_state[ts_key]
    
    # Render selector - MUST happen every script run, but use flag to track first render
    if show_selector:
        # Always render, the flag just tracks if we've done it before
        ts.render_selector(location=selector_location)
        if not st.session_state[selector_rendered_key]:
            st.session_state[selector_rendered_key] = True
    
    ts.apply_theme()
    
    # Add customization controls if requested
    if allow_customization:
        _add_customization_controls(ts, selector_location)
    
    return ts


def _add_customization_controls(ts, location='sidebar'):
    """
    Add theme customization controls.
    
    Allows users to adjust font size, spacing, border radius, and accent color.
    """
    container = st.sidebar if location == 'sidebar' else st
    
    # Initialize customization settings
    if 'theme_customizations' not in st.session_state:
        st.session_state.theme_customizations = {
            'font_size_multiplier': 1.0,
            'spacing_multiplier': 1.0,
            'border_radius_multiplier': 1.0,
            'custom_accent_color': None
        }
    
    with container:
        st.markdown("---")
        st.markdown("### ⚙️ Customize Theme")
        
        # Font size control
        font_size = st.slider(
            "Font Size",
            min_value=0.8,
            max_value=1.3,
            value=st.session_state.theme_customizations['font_size_multiplier'],
            step=0.1,
            help="Adjust the overall font size",
            key="custom_font_size"
        )
        st.session_state.theme_customizations['font_size_multiplier'] = font_size
        
        # Spacing control
        spacing = st.slider(
            "Spacing",
            min_value=0.7,
            max_value=1.3,
            value=st.session_state.theme_customizations['spacing_multiplier'],
            step=0.1,
            help="Adjust padding and margins",
            key="custom_spacing"
        )
        st.session_state.theme_customizations['spacing_multiplier'] = spacing
        
        # Border radius control
        radius = st.slider(
            "Roundness",
            min_value=0.0,
            max_value=2.0,
            value=st.session_state.theme_customizations['border_radius_multiplier'],
            step=0.1,
            help="Adjust border radius (0 = sharp, 2 = very round)",
            key="custom_radius"
        )
        st.session_state.theme_customizations['border_radius_multiplier'] = radius
        
        # Custom accent color
        use_custom_accent = st.checkbox(
            "Custom Accent Color",
            value=st.session_state.theme_customizations['custom_accent_color'] is not None,
            key="use_custom_accent"
        )
        
        if use_custom_accent:
            accent_color = st.color_picker(
                "Pick Accent Color",
                value=st.session_state.theme_customizations['custom_accent_color'] or "#d4af37",
                key="custom_accent_color_picker"
            )
            st.session_state.theme_customizations['custom_accent_color'] = accent_color
        else:
            st.session_state.theme_customizations['custom_accent_color'] = None
        
        # Reset button
        if st.button("Reset Customizations", key="reset_custom"):
            st.session_state.theme_customizations = {
                'font_size_multiplier': 1.0,
                'spacing_multiplier': 1.0,
                'border_radius_multiplier': 1.0,
                'custom_accent_color': None
            }
            st.rerun()
    
    # Apply customizations as CSS
    _apply_customization_css()


def _apply_customization_css():
    """Apply CSS customizations based on user settings."""
    custom = st.session_state.theme_customizations
    
    customization_css = f"""
<style>
/* === THEME CUSTOMIZATIONS === */
:root {{
    --custom-font-multiplier: {custom['font_size_multiplier']};
    --custom-spacing-multiplier: {custom['spacing_multiplier']};
    --custom-radius-multiplier: {custom['border_radius_multiplier']};
}}

/* Font size adjustments */
h1 {{ font-size: calc(3.5rem * var(--custom-font-multiplier)) !important; }}
h2 {{ font-size: calc(2rem * var(--custom-font-multiplier)) !important; }}
h3 {{ font-size: calc(1.3rem * var(--custom-font-multiplier)) !important; }}
p, label, div {{ font-size: calc(1rem * var(--custom-font-multiplier)) !important; }}

/* Spacing adjustments */
.stButton > button {{ 
    padding: calc(12px * var(--custom-spacing-multiplier)) calc(32px * var(--custom-spacing-multiplier)) !important; 
}}
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {{ 
    padding: calc(12px * var(--custom-spacing-multiplier)) calc(16px * var(--custom-spacing-multiplier)) !important; 
}}
[data-testid="metric-container"] {{ 
    padding: calc(1.5rem * var(--custom-spacing-multiplier)) !important; 
}}

/* Border radius adjustments */
.stButton > button {{ border-radius: calc(12px * var(--custom-radius-multiplier)) !important; }}
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {{ 
    border-radius: calc(8px * var(--custom-radius-multiplier)) !important; 
}}
[data-testid="metric-container"] {{ border-radius: calc(16px * var(--custom-radius-multiplier)) !important; }}
"""
    
    # Add custom accent color if set
    if custom['custom_accent_color']:
        customization_css += f"""
/* Custom accent color override */
.stButton > button {{
    background: {custom['custom_accent_color']} !important;
    border-color: {custom['custom_accent_color']} !important;
}}
h2 {{ color: {custom['custom_accent_color']} !important; }}
.stTabs [aria-selected="true"] {{
    background: {custom['custom_accent_color']} !important;
}}
a {{ color: {custom['custom_accent_color']} !important; }}
"""
    
    customization_css += "</style>"
    st.markdown(customization_css, unsafe_allow_html=True)
