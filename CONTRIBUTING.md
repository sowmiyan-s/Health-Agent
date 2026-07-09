# Contributing to HIA (Health Insights Agent) 🩺

Thank you for considering contributing to HIA! This document provides guidelines and instructions to help you get started.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment Setup](#development-environment-setup)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)
- [Security](#security)

## Code of Conduct

Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md). We aim to foster an inclusive and respectful community.

## Getting Started

### Prerequisites

- Python 3.8+
- Streamlit 1.30.0+ 
- Supabase account
- Groq API key
- PDFPlumber
- Python-magic-bin (Windows) or Python-magic (Linux/Mac)

### Development Environment Setup

1. **Fork and clone the repository**:
   ```bash
   git clone https://github.com/ridhupriyaa12/Health-Agent.git
   cd Health-Agent
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**:
   Create `.streamlit/secrets.toml`:
   ```toml
   SUPABASE_URL = "your-supabase-url"
   SUPABASE_KEY = "your-supabase-key"
   GROQ_API_KEY = "your-groq-api-key"
   ```

4. **Set up database**:
   Execute the SQL script in [supabase_schema.sql](supabase_schema.sql)

5. **Run the application**:
   ```bash
   streamlit run src/main.py
   ```

## Development Workflow

### Branching Strategy

- `main`: Production-ready code
- `feature/*`: New features
- `fix/*`: Bug fixes
- `docs/*`: Documentation updates

### Git Workflow

1. **Create a branch**:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes**
3. **Write commit messages**:
   ```
   feat: Add new blood analysis component
   
   - Implement report analysis visualization
   - Add validation for blood test values
   - Update documentation
   ```

4. **Push changes**:
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**

### Pull Request Guidelines

- Fill out the PR template completely
- Reference any related issues
- Include screenshots for UI changes
- Update documentation if needed
- Add tests for new functionality

## Coding Standards

### Python Style Guide

Follow PEP 8 (see official documentation)
 
### Code Organization
- Use type hints for function parameters
- Maximum line length: 88 characters
- Use docstrings for classes and functions
```python
# Imports
from typing import Optional
import streamlit as st

# Constants
MAX_UPLOAD_SIZE = 20

# Classes/Functions
class AnalysisAgent:
    """Agent for analyzing medical reports."""
    
    def __init__(self) -> None:
        """Initialize the analysis agent."""
        self.model = None
```

## Testing Guidelines

1. **Test Coverage**
   - Unit tests for utilities and services
   - Integration tests for major features
   - UI component tests

2. **Running Tests**
   ```bash
   python -m pytest tests/
   ```

## Documentation

- Update README.md for new features
- Add docstrings to new functions/classes
- Include example usage where appropriate
- Document environment variables
- Keep API documentation current

## Security

Follow the Security Policy (see SECURITY.md)

---

We appreciate your contributions to making HIA better! If you have questions, feel free to open an issue or contact ridhupriya.