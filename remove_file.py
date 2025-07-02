import os
import sys

file_to_remove = sys.argv[1]
os.remove(file_to_remove)
print(f"Successfully removed {file_to_remove}")