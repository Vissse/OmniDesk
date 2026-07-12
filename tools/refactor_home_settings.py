import sys
from refactor_all import extract

def main():
    extract('UI/view_home.py', [
        ('class ModuleCard', 'UI/components/home_components.py', ['ModuleCard'])
    ], 'HomePage')
    
    extract('UI/view_settings.py', [
        ('class SectionHeader', 'UI/components/settings_components.py', ['SectionHeader', 'Separator', 'SettingRow'])
    ], 'SettingsPage')

if __name__ == '__main__':
    main()
