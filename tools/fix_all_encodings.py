import os

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            content = f.read()
    except UnicodeDecodeError:
        print(f"Skipped {filepath}: Cannot read as UTF-8")
        return

    try:
        fixed_content = content.encode('cp1250').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        return

    if fixed_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print(f"Fixed {filepath}")

def main():
    root_dir = r"g:\OmniDesk"
    for subdir, dirs, files in os.walk(root_dir):
        if 'venv' in subdir or '.git' in subdir or '__pycache__' in subdir:
            continue
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(subdir, file)
                process_file(filepath)

if __name__ == "__main__":
    main()
