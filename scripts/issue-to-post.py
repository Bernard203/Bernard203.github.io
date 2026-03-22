#!/usr/bin/env python3
"""Convert GitHub Issue to Hugo content post."""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from slugify import slugify
import requests

def get_env(name, required=True):
    val = os.environ.get(name, "")
    if required and not val:
        print(f"ERROR: Missing environment variable: {name}")
        sys.exit(1)
    return val

def parse_labels(labels_json):
    """Parse labels to determine content type and language."""
    labels = json.loads(labels_json)
    content_type = None
    language = None

    type_map = {
        "type:software": "software",
        "type:design": "design",
        "type:article": "articles",
        "type:multimedia": "multimedia",
    }

    for label in labels:
        if label in type_map:
            content_type = type_map[label]
        if label.startswith("lang:"):
            language = label.replace("lang:", "")

    return content_type, language

def parse_issue_body(body):
    """Parse GitHub Issue Forms body into sections."""
    sections = {}
    current_key = None
    current_lines = []

    for line in body.split('\n'):
        # Issue forms render as ### Header\n\nValue
        header_match = re.match(r'^### (.+)$', line.strip())
        if header_match:
            if current_key:
                sections[current_key] = '\n'.join(current_lines).strip()
            current_key = header_match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_key:
        sections[current_key] = '\n'.join(current_lines).strip()

    return sections

def split_bilingual(content):
    """Split content by ## zh-cn and ## en markers."""
    zh_match = re.search(r'## zh-cn\s*\n(.*?)(?=## en|$)', content, re.DOTALL)
    en_match = re.search(r'## en\s*\n(.*?)$', content, re.DOTALL)

    zh_content = zh_match.group(1).strip() if zh_match else ""
    en_content = en_match.group(1).strip() if en_match else ""

    return zh_content, en_content

def extract_title_and_body(content):
    """Extract title from ### 标题/Title line and remaining body."""
    lines = content.split('\n')
    title = ""
    body_lines = []
    found_title = False

    for line in lines:
        title_match = re.match(r'^###\s+(?:标题|Title)\s*$', line.strip())
        if title_match and not found_title:
            found_title = True
            continue
        if found_title and not title and line.strip():
            title = line.strip()
            continue
        body_lines.append(line)

    body = '\n'.join(body_lines).strip()
    return title, body

def download_images(content, dest_dir):
    """Download GitHub-hosted images and rewrite URLs."""
    img_pattern = r'!\[([^\]]*)\]\((https://(?:github\.com/user-attachments|user-images\.githubusercontent\.com)[^\)]+)\)'

    dest_dir.mkdir(parents=True, exist_ok=True)

    def replace_image(match):
        alt_text = match.group(1)
        url = match.group(2)

        # Generate filename from URL
        ext = '.png'  # default
        if '.jpg' in url or '.jpeg' in url:
            ext = '.jpg'
        elif '.gif' in url:
            ext = '.gif'
        elif '.webp' in url:
            ext = '.webp'

        filename = f"image-{hash(url) % 10000:04d}{ext}"
        filepath = dest_dir / filename

        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            filepath.write_bytes(resp.content)
            print(f"Downloaded: {url} -> {filename}")
            return f'![{alt_text}]({filename})'
        except Exception as e:
            print(f"WARNING: Failed to download {url}: {e}")
            return match.group(0)  # keep original

    return re.sub(img_pattern, replace_image, content)

def generate_front_matter(title, date, section, params):
    """Generate TOML front matter."""
    lines = ['---']
    lines.append(f'title: "{title}"')
    lines.append(f'date: {date}')

    if params.get('summary'):
        summary = params['summary'].replace('"', '\\"')
        lines.append(f'summary: "{summary}"')

    if params.get('tags'):
        tags = [t.strip() for t in params['tags'].split(',') if t.strip()]
        lines.append(f'tags: {json.dumps(tags)}')

    if params.get('tools'):
        tools = [t.strip() for t in params['tools'].split(',') if t.strip()]
        lines.append(f'tools: {json.dumps(tools)}')

    if params.get('github'):
        lines.append(f'github: "{params["github"]}"')

    if params.get('demo'):
        lines.append(f'demo: "{params["demo"]}"')

    if params.get('mediaType'):
        lines.append(f'mediaType: "{params["mediaType"]}"')

    if params.get('duration'):
        lines.append(f'duration: "{params["duration"]}"')

    lines.append('---')
    return '\n'.join(lines)

def main():
    issue_number = get_env('ISSUE_NUMBER')
    issue_body = get_env('ISSUE_BODY')
    labels_json = get_env('ISSUE_LABELS')

    section, language = parse_labels(labels_json)

    if not section:
        print("ERROR: No valid type: label found")
        sys.exit(1)

    if not language:
        language = "bilingual"

    # Parse issue body (GitHub Issue Forms format)
    fields = parse_issue_body(issue_body)

    # Get the content field
    content_raw = fields.get('内容 / Content', '') or fields.get('Content', '') or fields.get('内容', '')
    if not content_raw:
        print("ERROR: No content found in issue body")
        sys.exit(1)

    date = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+08:00')

    # Collect extra params from issue form fields
    params = {}
    params['tags'] = fields.get('技术栈 / Tech Stack', '') or fields.get('标签 / Tags', '') or ''
    params['tools'] = fields.get('工具 / Tools', '') or ''
    params['github'] = fields.get('GitHub URL', '') or ''
    params['demo'] = fields.get('Demo URL', '') or ''
    params['mediaType'] = fields.get('媒体类型 / Media Type', '') or ''
    params['duration'] = fields.get('时长 / Duration', '') or ''

    # Clean up _No response_ placeholders from GitHub Issue Forms
    for k, v in params.items():
        if v == '_No response_':
            params[k] = ''

    base_path = Path('.')

    if language == 'bilingual':
        zh_content, en_content = split_bilingual(content_raw)

        zh_title, zh_body = extract_title_and_body(zh_content)
        en_title, en_body = extract_title_and_body(en_content)

        if not zh_title or not en_title:
            print("ERROR: Could not extract titles for bilingual content")
            sys.exit(1)

        slug = slugify(en_title, max_length=60)

        for lang, title, body in [('zh-cn', zh_title, zh_body), ('en', en_title, en_body)]:
            dest_dir = base_path / 'content' / lang / section / slug
            body = download_images(body, dest_dir)
            summary = body[:100].replace('\n', ' ').strip()
            params['summary'] = summary
            front_matter = generate_front_matter(title, date, section, params)

            dest_dir.mkdir(parents=True, exist_ok=True)
            (dest_dir / 'index.md').write_text(f'{front_matter}\n\n{body}\n', encoding='utf-8')
            print(f"Created: {dest_dir / 'index.md'}")

    else:
        lang = 'zh-cn' if language == 'zh' else 'en'
        title, body = extract_title_and_body(content_raw)

        if not title:
            # Fallback: use issue title
            title = get_env('ISSUE_TITLE')

        slug = slugify(title, max_length=60)
        dest_dir = base_path / 'content' / lang / section / slug
        body = download_images(body, dest_dir)
        summary = body[:100].replace('\n', ' ').strip()
        params['summary'] = summary
        front_matter = generate_front_matter(title, date, section, params)

        dest_dir.mkdir(parents=True, exist_ok=True)
        (dest_dir / 'index.md').write_text(f'{front_matter}\n\n{body}\n', encoding='utf-8')
        print(f"Created: {dest_dir / 'index.md'}")

    print("Done!")

if __name__ == '__main__':
    main()
