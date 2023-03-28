import subprocess
import os

superpeer_configs = [
    "config_superpeer1.json",
    "config_superpeer2.json",
    "config_superpeer3.json",
]

for config in superpeer_configs:
    subprocess.Popen(["python", "super_node.py", config], env=os.environ)
