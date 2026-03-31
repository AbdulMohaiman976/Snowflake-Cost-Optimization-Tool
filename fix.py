import sys
import json

with open('d:/snowflake/api/ai_service.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Define the exact new prompt structure the user wants
new_prompt_code = '''            prompt = f\"\"\"You are a Snowflake optimization and anomaly detection expert. Your task is to analyze the data provided for the '{module_key}' tab and deliver exactly 2 concise, highly actionable recommendations to improve performance or resolve critical issues.

**Requirements:**

- Focus on anomalies, cost reduction, and tangible, measurable improvements
- For each recommendation, provide a specific SQL snippet if applicable to address storage optimization, query performance, or permission issues
- Output format: Plain text explanations with markdown bullets only—no raw JSON, no data echoes, no technical jargon without explanation
- Each recommendation must be immediately implementable by the target audience

**Structure each recommendation as:**
1. **Issue identified** (1-2 sentences describing the problem)
2. **Business impact** (why this matters—cost, performance, or risk)
3. **Solution** (clear steps or SQL code to resolve it)

Prioritize recommendations by potential impact. If you cannot generate a SQL snippet for a recommendation, explain why and suggest an alternative approach instead.

Data:
{json.dumps(data, default=str)[:2500]}\"\"\"'''

# We will just split on the known identifier
parts = text.split("            prompt = (")
if len(parts) == 1:
    print("Already fixed or different format.")
    sys.exit(0)

part1 = parts[0]
after_prompt = parts[1].split('            )')[1]

final_text = part1 + new_prompt_code + after_prompt

with open('d:/snowflake/api/ai_service.py', 'w', encoding='utf-8') as f:
    f.write(final_text)

print("Fixed syntax in ai_service.py successfully.")
