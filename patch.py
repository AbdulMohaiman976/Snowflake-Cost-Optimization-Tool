import re

with open("d:/snowflake/app.py", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Add ai_recommendations to result dict (Connect)
text = text.replace(
    '"filepath":     None,\n                                    }',
    '"filepath":     None,\n                                        "ai_recommendations": data.get("ai_recommendations", {}),\n                                    }'
)

# 2. Add ai_recommendations to result dict (Load)
text = text.replace(
    '"filepath":     None,\n                                }',
    '"filepath":     None,\n                                    "ai_recommendations": data.get("ai_recommendations", {}),\n                                }'
)

# 3. Add `render_ai_recs` to Helpers
helpers_str = """
def render_ai_recs(module_key):
    recs = st.session_state.result.get("ai_recommendations", {}).get(module_key) if st.session_state.result else None
    if recs:
        # Pre-process markdown so Streamlit handles it better inside HTML if needed, but we'll try raw st.markdown first.
        st.markdown(f'''
        <div style="background:linear-gradient(135deg,#1e1e2d,#252538);border-left:5px solid #8b5cf6;border-radius:10px;padding:1.4rem;margin-top:1.5rem;margin-bottom:1rem;border:1px solid #3b2b5e;">
          <h4 style="color:#a78bfa;margin-top:0;font-size:1.1rem;margin-bottom:0.8rem;">✨ AI Optimization Insights</h4>
          <div style="color:#e2e8f0;font-size:0.95rem;line-height:1.6;white-space:pre-wrap;">{recs}</div>
        </div>
        ''', unsafe_allow_html=True)
    elif st.session_state.connected and st.session_state.session_id:
        st.markdown('''
        <div style="background:linear-gradient(135deg,#161b22,#1c2128);border-left:5px solid #475569;border-radius:10px;padding:1.2rem;margin-top:1.5rem;margin-bottom:1rem;border:1px solid #30363d;">
          <p style="color:#94a3b8;margin:0;font-size:0.85rem;">⏳ <i>AI Insights are generating in the background... Paste the session token in Load Session again in a few seconds to see them.</i></p>
        </div>
        ''', unsafe_allow_html=True)
"""
text = text.replace("# ─────────────────────────────────────────────────────────────────\n# SIDEBAR", helpers_str + "\n# ─────────────────────────────────────────────────────────────────\n# SIDEBAR")

# 4. Change Tabs text
tabs_old = """tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🏭  Warehouse",
    "🔍  Query Intelligence",
    "📈  Spend Anomaly",
    "💰  Cost Breakdown",
    "🗄️  Storage",
    "🔐  Security & Users",
    "📓  Notebooks",
    "💡  Savings & History",
])"""
tabs_new = """tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "🏭  Warehouse",
    "🔍  Query Intelligence",
    "📈  Spend Anomaly",
    "💰  Cost Breakdown",
    "🗄️  Storage",
    "🔐  Security & Users",
    "📓  Notebooks",
    "☁️  Cloud Services",
    "🗑️  Unused Objects",
    "💡  Estimator & History",
])"""
text = text.replace(tabs_old, tabs_new)

# Replace "with tab8:" with "with tab10:" for Savings
text = text.replace("with tab8:\n    sav = ar.get(", "with tab10:\n    sav = ar.get(")

# Append render_ai_recs to tabs
# Tab 1
text = text.replace('show_recs(wh["recommendations"])', 'show_recs(wh["recommendations"])\n    render_ai_recs("warehouse")')
# Tab 2
text = text.replace('show_recs(qry["recommendations"])', 'show_recs(qry["recommendations"])\n    render_ai_recs("queries")')
# Tab 3
text = text.replace('show_recs(anom["recommendations"])', 'show_recs(anom["recommendations"])\n    render_ai_recs("anomaly")')
# Tab 4
text = text.replace('show_recs(cost["recommendations"])', 'show_recs(cost["recommendations"])\n    render_ai_recs("cost")')
# Tab 5
text = text.replace('show_recs(stor["recommendations"])', 'show_recs(stor["recommendations"])\n    render_ai_recs("storage")')
# Tab 6
text = text.replace('show_recs(usr["recommendations"])', 'show_recs(usr["recommendations"])\n    render_ai_recs("users")')
# Tab 7 Notebooks - it doesn't have show_recs at the end. It ends with:
# st.dataframe(df_nb[cols_nb].rename(columns=rename_nb),
#              use_container_width=True, hide_index=True)
text = text.replace(
    'use_container_width=True, hide_index=True)',
    'use_container_width=True, hide_index=True)\n    render_ai_recs("notebooks")'
)

# Insert Tab 8 and 9 code between Tab 7 and Tab 10
tab89_code = """
# ══════════════════════════════════════════════════════════════════
# TAB 8 — CLOUD SERVICES
# ══════════════════════════════════════════════════════════════════
with tab8:
    cs = ar.get("cloud_services", {})
    st.markdown("<div style='margin-bottom:1rem;'><h3 style='color:#c8daf0;font-size:1.1rem;font-weight:700;margin:0;'>Cloud Services Credits</h3><p style='color:#2d5a8a;font-size:0.75rem;margin:4px 0 0;'>Cloud services billing overhead tracking</p></div>", unsafe_allow_html=True)
    if cs:
        k1, k2, k3 = st.columns(3)
        k1.metric("Total CS Credits", f'{cs.get("total_cs_credits",0):.4f}')
        k2.metric("Billed CS Credits", f'{cs.get("billed_cs_credits",0):.4f}')
        k3.metric("Free CS Credits", f'{cs.get("free_cs_credits",0):.4f}')
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        show_recs(cs.get("recommendations", []))
    else:
        st.info("No cloud services data found.")
    render_ai_recs("cloud_services")

# ══════════════════════════════════════════════════════════════════
# TAB 9 — UNUSED OBJECTS
# ══════════════════════════════════════════════════════════════════
with tab9:
    uo = ar.get("unused_objects", {})
    st.markdown("<div style='margin-bottom:1rem;'><h3 style='color:#c8daf0;font-size:1.1rem;font-weight:700;margin:0;'>Unused Object Detection</h3><p style='color:#2d5a8a;font-size:0.75rem;margin:4px 0 0;'>Role and table utilization</p></div>", unsafe_allow_html=True)
    if uo:
        st.write(f"Unused Roles: {uo.get('unused_roles_count', 0)}")
        st.write(f"Stale Tables: {uo.get('stale_tables_count', 0)}")
    else:
        st.info("No unused object data found.")
    render_ai_recs("unused_objects")
"""

text = text.replace("# ══════════════════════════════════════════════════════════════════\n# TAB 8 — SAVINGS & HISTORY", tab89_code + "\n# ══════════════════════════════════════════════════════════════════\n# TAB 10 — SAVINGS & HISTORY")

# Modify Export JSON text to make it clear this is raw data NOT the AI
text = text.replace('🤖 AI Insights File — Export for LLM Analysis', '⚙️ Raw JSON Export (Internal tool)')

with open("d:/snowflake/app.py", "w", encoding="utf-8") as f:
    f.write(text)

print(f"Patch applied successfully.")
