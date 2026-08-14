# OLLAMA-UI

A lightweight web-based interface for interacting with local AI models through Ollama.

This project allows you to run AI models directly on your computer and interact with them through a simple browser-based interface.

---

## Preview

> **Add your screenshot below.**

```markdown
![OLLAMA-UI Screenshot](images/screenshot.png)
```

Create an `images` folder inside the project directory:

```text
OLLAMA-UI
├── app.py
├── README.md
├── images
│   └── screenshot.png
├── static
└── templates
```

---

## Features

* Local AI chat
* Ollama integration
* Browser-based interface
* File system commands
* Lightweight Flask server
* Fast response time
* Keyboard shortcuts
* Open-source

---

## Requirements

Before running this project, install:

* Python 3
* Ollama
* Git

---

## Install Ollama

### Ubuntu

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Check whether Ollama is installed correctly:

```bash
ollama --version
```

---

## Install the AI Model

The model used in this project:

```bash
ollama pull qwen2.5-coder:3b
```

Check installed models:

```bash
ollama list
```

Example output:

```text
NAME                 ID              SIZE
qwen2.5-coder:3b     xxxxxxxxxxxx    1.9 GB
```

You can also install other models:

```bash
ollama pull llama3
ollama pull mistral
ollama pull gemma3
```

---

## Clone the Repository

Using Git:

```bash
git clone git@github.com:sayan08880/OLLAMA-UI.git
```

Move into the project directory:

```bash
cd OLLAMA-UI
```

---

## Install Python Dependencies

If your project contains a `requirements.txt` file:

```bash
pip install -r requirements.txt
```

If not:

```bash
pip install flask
```

---

## Start the Ollama Server

Open a terminal:

```bash
ollama serve
```

Keep this terminal running.

---

## Test the AI Model

Open another terminal:

```bash
ollama run qwen2.5-coder:3b
```

If the model responds, the installation was successful.

---

## Start OLLAMA-UI

Run:

```bash
python app.py
```

You should see something similar to this:

```text
==================================================
  Ollama Web UI v3 + File System Commands
  http://localhost:5000
  Ctrl+Shift+N = New Chat
  /allow = Grant file system access
==================================================
```

Open your browser:

```text
http://localhost:5000
```

---

## Add the `aiui` Terminal Command

Create a new executable file:

```bash
sudo nano /usr/local/bin/aiui
```

Paste:

```bash
#!/bin/bash

cd /home/sayan/path/to/OLLAMA-UI
python app.py
```

Replace:

```text
/home/sayan/path/to/OLLAMA-UI
```

with the actual location of your project.

Save the file.

Make it executable:

```bash
sudo chmod +x /usr/local/bin/aiui
```

Now you can start the application from any directory:

```bash
aiui
```

---

## Keyboard Shortcuts

| Shortcut         | Function                  |
| ---------------- | ------------------------- |
| Ctrl + Shift + N | Create a new chat         |
| /allow           | Enable file system access |

---

## Update the Project

After changing any file:

```bash
git add .
git commit -m "Update"
git push
```

---

## Project Structure

```text
OLLAMA-UI
├── app.py
├── README.md
├── images
├── static
│   ├── style.css
│   ├── logo.png
│   └── script.js
└── templates
    └── index.html
```

---

## Technologies Used

* Python
* Flask
* HTML
* CSS
* JavaScript
* Ollama
* Local LLMs

---

## Future Improvements

* [ ] Multiple model support
* [ ] Dark mode
* [ ] File upload
* [ ] Voice input
* [ ] Chat history
* [ ] Theme customization

---

## Author

**Sayan Mahalanabish**

GitHub: `@sayan08880`

---

## License

This project is released under the MIT License.
