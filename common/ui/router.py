from dataclasses import dataclass
from typing import Callable, Sequence
import traceback
import streamlit as st

@dataclass(frozen=True)
class TabSpec:
    label: str
    render: Callable[[], None]
    admin_only: bool = False

def render_tabs(tab_specs: Sequence[TabSpec], is_admin: bool) -> None:
    visible = [t for t in tab_specs if (is_admin or not t.admin_only)]
    tab_labels = [t.label for t in visible]
    tab_objs = st.tabs(tab_labels)

    for spec, tab in zip(visible, tab_objs):
        with tab:
            try:
                spec.render()
            except Exception as e:
                st.error(str(e))
                st.code(traceback.format_exc())