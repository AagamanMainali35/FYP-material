import os
import subprocess
import time

def open_cmd():
    current_directory = os.getcwd()
    subprocess.Popen("cmd", cwd=current_directory)

def open_vs_code():
    current_directory = os.getcwd()
    subprocess.Popen("code .", cwd=current_directory, shell=True)

def main():
    open_cmd()
    time.sleep(1) 
    open_vs_code()

if __name__ == "__main__":
    main()
