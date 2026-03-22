# Installation

## Requirements

- Python 3.9 or later
- pip

## From source (recommended)

```bash
git clone https://github.com/your-username/dicentra.git
cd dicentra

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install runtime dependencies
pip install -r requirements.txt

# Run
python main.py
```

## For development

```bash
# Install dev dependencies (includes testing + linting tools)
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v
```

## Platform notes

### Windows
No extra steps required. PyQt5 ships its own Qt binaries.

### Linux
You may need to install Qt system libraries:

```bash
sudo apt-get install libxcb-xinerama0 libxkbcommon-x11-0
```

### macOS
No extra steps required on modern macOS with an Apple Silicon or Intel machine.
