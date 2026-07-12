import sys

def extract(file_path, definitions, main_class):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    start_idx = -1
    for i, line in enumerate(lines):
        if line.startswith(definitions[0][0]):
            start_idx = i
            break
            
    end_idx = -1
    for i, line in enumerate(lines):
        if line.startswith(f'class {main_class}'):
            end_idx = i
            break
            
    if start_idx == -1 or end_idx == -1:
        print(f"Failed to find bounds for {file_path}")
        return
        
    imports = lines[:start_idx]
    
    import_statements = []
    
    current_idx = start_idx
    for i, (cls_prefix, target_file, cls_names) in enumerate(definitions):
        next_idx = end_idx
        if i + 1 < len(definitions):
            for j in range(current_idx + 1, end_idx):
                if lines[j].startswith(definitions[i+1][0]):
                    next_idx = j
                    break
                    
        content = lines[current_idx:next_idx]
        
        with open(target_file, 'w', encoding='utf-8') as f:
            f.writelines(imports + content)
            
        import_statements.append(f"from {target_file.replace('/', '.').replace('.py', '')} import {', '.join(cls_names)}\n")
        
        current_idx = next_idx
        
    new_lines = imports + ["\n"] + import_statements + ["\n"] + lines[end_idx:]
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"Successfully processed {file_path}")

def main():
    # view_uninstaller.py
    extract('UI/view_uninstaller.py', [
        ('class UninstallWorker', 'UI/workers/uninstall_worker.py', ['UninstallWorker']),
        ('class AppItemWidget', 'UI/components/uninstaller_components.py', ['AppItemWidget'])
    ], 'UninstallerPage')
    
    # view_updater.py
    extract('UI/view_updater.py', [
        ('class ScanWorker', 'UI/workers/update_worker.py', ['ScanWorker', 'UpdateWorker']),
        ('class UpdateRowWidget', 'UI/components/updater_components.py', ['UpdateRowWidget'])
    ], 'UpdaterPage')
    
    # view_queue.py
    extract('UI/view_queue.py', [
        ('class VersionFetchWorker', 'UI/workers/install_worker.py', ['VersionFetchWorker']),
        ('class QueueRowWidget', 'UI/components/queue_components.py', ['QueueRowWidget'])
    ], 'QueuePage')
    
    # view_health.py
    extract('UI/view_health.py', [
        ('class PlayButton', 'UI/components/health_components.py', ['PlayButton', 'ToolRowWidget']),
        ('class CommandWorker', 'UI/workers/command_worker.py', ['CommandWorker']),
        ('class LogDialog', 'UI/dialogs/log_dialog.py', ['LogDialog'])
    ], 'HealthCheckPage')

if __name__ == '__main__':
    main()
