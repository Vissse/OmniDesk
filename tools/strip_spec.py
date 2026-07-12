import sys

def main():
    with open('UI/view_specs.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    start_idx = -1
    end_idx = -1
    
    for i, line in enumerate(lines):
        if line.startswith('class SpecRow(QFrame):'):
            start_idx = i
        if line.startswith('class SpecsPage(QWidget):'):
            end_idx = i
            break
            
    if start_idx != -1 and end_idx != -1:
        new_lines = lines[:start_idx] + ["from UI.components.spec_components import SpecRow, SpecGroup, DiskRow, AnimatedNavItem, AnimatedCard, MiniToast, InfoHeaderCard\n\n"] + lines[end_idx:]
        with open('UI/view_specs.py', 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        print("Success")
    else:
        print(f"Failed to find indices: {start_idx}, {end_idx}")

if __name__ == "__main__":
    main()
