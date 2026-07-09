# 🩺 HIA (Health Insights Agent)

AI-powered agent to analyze blood reports and deliver detailed, personalized health insights.

<p align="center">

  <a href="https://github.com/ridhupriyaa12/Health-Agent/issues"><img src="https://img.shields.io/github/issues/ridhupriyaa12/Health-Agent" alt="Issues"></a>

  <a href="https://github.com/ridhupriyaa12/Health-Agent/stargazers"><img src="https://img.shields.io/github/stars/ridhupriyaa12/Health-Agent" alt="Stars"></a>
  <a href="https://github.com/ridhupriyaa12/Health-Agent/network/members"><img src="https://img.shields.io/github/forks/ridhupriyaa12/Health-Agent" alt="Forks"></a>
  <a href="https://github.com/ridhupriyaa12/Health-Agent/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
</p>

<p align="center">
  <a href="https://github.com/ridhupriyaa12/Health-Agent"><img src="https://raw.githubusercontent.com/ridhupriyaa12/Health-Agent/main/public/HIA_demo.gif" alt="Usage Demo"></a>
</p>

---

## 🌟 Features

* Multi-model agent architecture for intelligent analysis
* In-context learning with knowledge base updates
* Personalized health insights from medical reports
* PDF upload, validation, and extraction (up to 20MB)
* Secure user authentication and session management
* Session history with detailed analysis tracking
* Modern, responsive UI with real-time feedback

---

## 🛠️ Tech Stack

* **Frontend**: Streamlit
* **AI Models** (via Groq):

  * Primary: `meta-llama/llama-4-maverick-17b-128e-instruct`
  * Secondary: `llama-3.3-70b-versatile`
  * Tertiary: `llama-3.1-8b-instant`
  * Fallback: `llama3-70b-8192`
* **Database**: Supabase
* **PDF Processing**: PDFPlumber
* **Authentication**: Supabase Auth

---

## 🚀 Installation

### Requirements

* Python 3.8+
* Streamlit 1.30.0+
* Supabase account
* Groq API key
* PDFPlumber
* Python-magic-bin (Windows) / Python-magic (Linux/Mac)

### Steps

1. Clone the repository:

```bash
git clone https://github.com/ridhupriyaa12/Health-Agent.git
cd Health-Agent
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "your-supabase-url"
SUPABASE_KEY = "your-supabase-key"
GROQ_API_KEY = "your-groq-api-key"
```

4. Set up Supabase database schema:
   Use the SQL script provided at [`public/db/script.sql`](https://github.com/ridhupriyaa12/Health-Agent/blob/main/public/db/script.sql).

> Tip: You can turn off email confirmation in Supabase settings under Signup → Email.

5. Run the application:

```bash
streamlit run src/main.py
```

---

## 📁 Project Structure

```
Health-Agent/
├── requirements.txt
├── README.md
├── src/
│   ├── main.py                 # Entry point
│   ├── auth/                   # Authentication modules
│   │   ├── auth_service.py     # Supabase auth integration
│   │   └── session_manager.py  # Session handling
│   ├── components/             # UI components
│   │   ├── analysis_form.py    # Report form
│   │   ├── auth_pages.py       # Login/Signup pages
│   │   ├── footer.py           # Footer
│   │   └── sidebar.py          # Sidebar navigation
│   ├── config/                 # Configuration
│   │   ├── app_config.py       # App settings
│   │   └── prompts.py          # AI prompts
│   ├── services/               # Integrations
│   │   └── ai_service.py       # AI service integration
│   ├── agents/                 # Agent logic
│   │   ├── agent_manager.py    # Agent manager
│   │   └── model_fallback.py   # Model fallback logic
│   └── utils/                  # Utilities
│       ├── validators.py       # Input validation
│       └── pdf_extractor.py    # PDF processing
```

---

## 📄 License

This project is licensed under the MIT License. See [LICENSE](https://github.com/ridhupriyaa12/Health-Agent/blob/main/LICENSE) for details.

---

## 🙋‍♂️ Author

Created by NithuPriyaa
