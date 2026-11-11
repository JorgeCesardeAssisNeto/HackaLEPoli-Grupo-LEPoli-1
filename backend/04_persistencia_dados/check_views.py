with open('nhanes_explorer/templates/index.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'<div[^>]*id="(view-[^"]+)"[^>]*class="([^"]+)"', text)
for m in matches:
    print(m[0], "-->", m[1])
