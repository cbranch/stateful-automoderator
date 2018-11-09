import re
import time

template_re = re.compile(r'{{(\w+)\s+([^}]+)}}')
def render_template_expression(matchobj):
    if matchobj.group(1) == "date":
        return time.strftime(matchobj.group(2))
    else:
        return matchobj.group(0)

def render_template(text):
    return template_re.sub(render_template_expression, text)
