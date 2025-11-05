![Project cover](readme-cover.png)

# Document Hub

## Overview

Document Hub is a sleek, cross-platform desktop application designed to help you efficiently manage and organize your digital files. Built with Python and PySide6 (Qt for Python), it offers a powerful "Smart Search" functionality with full-text indexing, live file monitoring, and intelligent content preview, alongside an upcoming "File Organizer" for automated sorting.

Whether you're a developer needing to quickly find code snippets or a student managing research papers, Document Hub provides a fast and intuitive way to interact with your local file system.

## Features

**Smart Search Tab:**
* **Full-Text Search (FTS):** Quickly find documents by content, not just filenames.
* **Live Indexing:** Automatically indexes new or modified files in your watched folders in the background, keeping your search results always up-to-date.
* **Syntax Highlighting:** Beautifully renders code and text files with Pygments-powered syntax highlighting in the preview pane.
* **Search Term Highlighting:** Instantly highlights your search keywords within the preview, showing you exactly why a file was a match.
* **Multi-Format Preview:** View text files, code, PDFs, and common image formats directly within the application.
* **Dynamic Filtering:** Filter search results by file type using an intuitive dropdown menu.
* **Instant File Opening:** Double-click any search result to open the file in its default system application.

**File Organizer Tab (Coming Soon):**
* Automated file sorting based on user-defined rules (e.g., move all `.pdf` to 'Documents/PDFs', `.jpg` to 'Pictures/YYYY-MM').
* Rule management and execution.

## Installation and Setup

### Prerequisites
* Python 3.8+
* `pip` (Python package installer)

### Steps

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/gimesha-adikari/doc-hub.git](https://github.com/gimesha-adikari/doc-hub.git)
    cd doc-hub
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Note: You will need to create a `requirements.txt` file as described below.)*

4.  **Run the Application:**
    ```bash
    python main.py
    ```

## Configuration

Upon first launch, you will be prompted to add folders to watch. You can also access settings via the gear icon in the top right.

## Project Structure
```
doc-hub/
├── database/
│   └── doc_hub.db
├── resources/ # UI assets (icons, QSS styles, organizer rules)
│   ├── icons/
│   └── style.qss
├── src/
│   ├── app/ # Application-specific UI logic
│   │   ├── main_window.py
│   │   └── settings_window.py
│   ├── core/ # Core business logic, services, and data models
│   │   ├── background_manager.py
│   │   ├── database.py
│   │   ├── file_indexer.py
│   │   ├── search_service.py
│   │   └── syntax_highlighter.py
│   ├── ui/ # Application-specific UI components
│   │   ├── main_window_ui.py
│   │   └── settings_window_ui.py
├── ui_files/ # Qt Designer UI files
│   ├── main_window.ui
│   └── settings_window.ui
├── .gitignore
└── main.py
```

## Contributing

Contributions are welcome! If you have suggestions for improvements, new features, or find any bugs, please feel free to:

1.  Open an [issue](https://github.com/gimesha-adikari/doc-hub/issues).
2.  Fork the repository and create a [pull request](https://github.com/gimesha-adikari/doc-hub/pulls).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
