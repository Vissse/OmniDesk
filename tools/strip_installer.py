import sys

def main():
    with open('UI/view_installer.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    start_idx = -1
    end_idx = -1
    
    for i, line in enumerate(lines):
        if line.startswith('class HoverButton(QPushButton):'):
            start_idx = i
        if line.startswith('class InstallerPage(QWidget):'):
            end_idx = i
            break
            
    if start_idx != -1 and end_idx != -1:
        imports = lines[:start_idx]
        components = lines[start_idx:end_idx]
        
        with open('UI/components/installer_components.py', 'w', encoding='utf-8') as f:
            f.writelines(imports + components)
            
        new_lines = imports + ["from UI.components.installer_components import HoverButton, QueueToggleButton, InstallationOptionsDialog, AppDetailPanel, CompactAppWidget\n\n"] + lines[end_idx:]
        with open('UI/view_installer.py', 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print("Success installer")
    else:
        print(f"Failed to find indices: {start_idx}, {end_idx}")

if __name__ == "__main__":
    main()
