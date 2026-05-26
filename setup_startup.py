import os

def main():
    # Paths
    workspace_dir = r"c:\Users\USER\openwave"
    startup_dir = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
    vbs_filename = "start_bot_hidden.vbs"

    # 1. Create the VBScript content
    vbs_content = f"""Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd.exe /c \"{os.path.join(workspace_dir, 'run.bat')}\"", 0, False
"""

    # Write to project directory
    project_vbs_path = os.path.join(workspace_dir, vbs_filename)
    with open(project_vbs_path, "w", encoding="utf-8") as f:
        f.write(vbs_content)
    print(f"Created VBScript at {project_vbs_path}")

    # Write/Copy to Windows Startup directory
    startup_vbs_path = os.path.join(startup_dir, vbs_filename)
    with open(startup_vbs_path, "w", encoding="utf-8") as f:
        f.write(vbs_content)
    print(f"Added bot to Windows Startup folder at: {startup_vbs_path}")

    # 2. Start the bot right now silently in the background
    import subprocess
    try:
        subprocess.Popen(f'wscript "{project_vbs_path}"', shell=True)
        print("Bot has been successfully started silently in the background!")
    except Exception as e:
        print(f"Failed to start bot silently: {e}")

if __name__ == "__main__":
    main()
