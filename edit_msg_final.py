import sys
import re

def process(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # replace phrases
    content = content.replace("readme with professional tone and rename project", "initial project structure and readme")
    content = content.replace("final readme polish and feature highlights", "refine documentation and features")
    content = content.replace("robust refactor of detail.html conditional logic to eliminate jinja2 templatesyntaxerrors permanently", "fix detail.html logic and jinja errors")
    content = content.replace("enhanced dark mode & fixed map routing/calculation. added premium night mode styles for google maps, fixed real-time cost calculation on host page, and improved route visibility with high-contrast polyline", "improve dark mode and map routing")
    content = content.replace("add license, github actions ci, mermaid architecture diagram, and pin dependencies", "setup license, ci, and dependencies")
    content = content.replace("add production dependencies for render", "configure production environment")
    
    # ensure lowercase and no emojis (just in case)
    lines = content.split('\n')
    if lines:
        lines[0] = lines[0].lower().strip()
        lines[0] = re.sub(r'[^\x00-\x7F]+', '', lines[0])
        if lines[0].endswith('.'): lines[0] = lines[0][:-1]
        
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

if __name__ == '__main__':
    process(sys.argv[1])
