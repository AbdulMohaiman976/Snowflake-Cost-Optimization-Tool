import sys

with open('d:/snowflake/app.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Strip ALL rogue inserts globally
text = text.replace('\n    render_ai_recs("notebooks")', '')
text = text.replace('\n        render_ai_recs("notebooks")', '')

# 2. Add it back EXACTLY in Tab 7 (Notebooks) where it belongs
target_anchor = '''        st.dataframe(df_nb[cols_nb].rename(columns=rename_nb),
                     use_container_width=True, hide_index=True)'''

new_block = '''        st.dataframe(df_nb[cols_nb].rename(columns=rename_nb),
                     use_container_width=True, hide_index=True)
    render_ai_recs("notebooks")'''

if target_anchor in text:
    text = text.replace(target_anchor, new_block)
else:
    print("WARNING: Could not find target anchor for notebooks tab!")

with open('d:/snowflake/app.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Repaired app.py successfully.")
