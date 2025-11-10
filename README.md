![Project cover](readme-cover.png)

# Document Hub

## Overview

Document Hub is a sleek, cross-platform desktop application designed to help you efficiently manage and organize your digital files. Built with Python and PySide6 (Qt for Python), it offers a powerful "Smart Search" functionality with full-text indexing, live file monitoring, and intelligent content preview, alongside an upcoming "File Organizer" for automated sorting.

Whether you're a developer needing to quickly find code snippets or a student managing research papers, Document Hub provides a fast and intuitive way to interact with your local file system.

---

## Features

**Smart Search Tab:**
* **Full-Text Search (FTS):** Quickly find documents by content, not just filenames.
* **Live Indexing:** Automatically indexes new or modified files in your watched folders in the background.
* **Syntax Highlighting:** Beautifully renders code and text files using Pygments.
* **Search Term Highlighting:** Instantly highlights matched terms.
* **Multi-Format Preview:** View text, code, PDFs, and common images directly.
* **Dynamic Filtering:** Filter results by file type.
* **Instant File Opening:** Double-click to open in your default system app.

**File Organizer Tab (Coming Soon):**
* Automated file sorting based on user-defined rules (e.g., move all `.pdf` files to `Documents/PDFs`).
* Configurable rule management.

---

## Offline AI Mode

Document Hub supports offline AI assistance using a locally hosted LLM (Mistral 7B).  
This enables intelligent summaries and contextual responses without an internet connection.

### Setup Steps
1. Install dependencies:
   ```bash
   pip install llama-cpp-python fastapi uvicorn
   ```
2. Set your model path:
   ```bash
   export LLM_MODEL_PATH="/path/to/mistral-7b-instruct-v0.2.Q4_K_M.gguf"
   ```
3. Launch the local AI server:
   ```bash
   bash launch_model.sh
   ```
4. The application automatically connects to `http://127.0.0.1:7860` for offline queries.

---

## Auto Dependency Detection & Packaging

Use the `auto_build.py` script to automatically detect external dependencies and update `pyproject.toml` before building.

```bash
python auto_build.py
```

This scans all Python files in `src/`, updates dependencies, and runs the packaging process.

---

## Environment Variables

Document Hub uses a `.env` file to store API keys and sensitive configuration:

```
GOOGLE_API_KEY=your_google_gemini_key_here
```

This is required for AI-powered semantic search when using the online mode.

---

## Installation and Setup

### Prerequisites
* Python 3.10+
* `pip` (Python package installer)

### Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/gimesha-adikari/doc-hub.git
   cd doc-hub
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install .
   ```
   or
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**
   ```bash
   python main.py
   ```

---

## Building the Application

To create a distributable version of Document Hub:

```bash
python -m build
```

The packaged files (`.whl`, `.tar.gz`) will be located in the `dist/` folder.

---

## Project Structure

```
doc-hub/
├── .env
├── database/
│   └── doc_hub.db
├── offline_ai/
│   ├── model_server.py
│   ├── model_worker.py
│   ├── reason_server.py
│   └── launch_model.sh
├── resources/
│   ├── icons/
│   └── style.qss
├── src/
│   ├── core/
│   │   ├── ai_service.py
│   │   ├── background_manager.py
│   │   ├── database.py
│   │   ├── file_indexer.py
│   │   ├── search_service.py
│   │   ├── incremental_indexer.py
│   │   ├── duplicate_detector.py
│   │   ├── search_index_service.py
│   │   └── resource_utils.py
│   ├── workers/
│   │   ├── ai_worker.py
│   │   ├── duplicate_worker.py
│   │   ├── index_worker.py
│   │   ├── search_worker.py
│   │   ├── organizer_worker.py
│   │   └── delete_worker.py
│   ├── ui/
│   │   ├── main_window_ui.py
│   │   └── settings_window_ui.py
│   ├── app/
│   │   ├── main_window.py
│   │   └── settings_window.py
│   └── main.py
├── ui_files/
│   ├── main_window.ui
│   └── settings_window.ui
├── FeaturePlan.md
├── auto_build.py
├── LICENSE
└── README.md
```

---

## Background Workers

The `src/doc_hub/workers/` package includes threaded background components for:
- **Indexing**: Continuous file system monitoring and index updates.
- **Search**: Non-blocking full-text query execution.
- **AI Tasks**: Delegating content analysis and summaries to AI services.
- **Duplicate Detection**: Hash-based content comparison.
- **Organizer**: Background file rule processing.

---

## Roadmap

See [FeaturePlan.md](FeaturePlan.md) for the full development roadmap, including:
- Incremental Indexing
- Duplicate File Detection
- Semantic Search (AI-powered)
- Smart Organizer
- Cloud Sync and Collaboration
- Plugin Framework and Voice Commands

---

## Contributing

Contributions are welcome!  
To contribute:
1. Open an issue.
2. Fork the repository.
3. Submit a pull request.

---

## License

This project is licensed under the MIT License.  
See the [LICENSE](LICENSE) file for details.
