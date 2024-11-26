from cx_Freeze import setup, Executable

# Set the base to None to indicate it's a GUI application (no console window)
base = None

# Define your executable file
executables = [Executable("scrap.py", base=base)]

# Setup function to build the executable
setup(
    name="ProxyScraper",
    version="1.0",
    description="Description of your app",
    executables=executables
)
