# 🤖 OLLAMA-UI

<div align="center">

<img src="images/screenshot.png" width="100%" alt="OLLAMA-UI Screenshot">

### A modern, lightweight, and powerful web interface for local AI models powered by Ollama.

Run AI completely on your own computer. No cloud. No API keys. No subscriptions.

![Python](https://img.shields.io/badge/Python-3.x-blue)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-black)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-green)
![License](https://img.shields.io/badge/License-MIT-red)
![Platform](https://img.shields.io/badge/Platform-Linux-orange)

</div>

---

## ✨ Overview

**OLLAMA-UI** is a lightweight browser-based interface designed for interacting with **local AI models** through **Ollama**.

Instead of using cloud-based AI services, this application allows you to run powerful language models directly on your computer while providing a clean and simple web interface.

Perfect for:

- 💻 Developers
- 🎓 Students
- 🔬 Researchers
- 🤖 AI enthusiasts
- 🐧 Linux users

---

## 📸 Preview

> Add your screenshot inside the `images` folder.

```text
OLLAMA-UI
├── images
│   └── screenshot.png
```

```markdown
![OLLAMA-UI Screenshot](images/screenshot.png)
```

---

## 🚀 Features

- ✅ Local AI chat
- ✅ Ollama integration
- ✅ Browser-based interface
- ✅ File system commands
- ✅ Lightweight Flask server
- ✅ Fast response time
- ✅ Keyboard shortcuts
- ✅ Open-source
- ✅ No API keys required
- ✅ Run completely offline

---

## 🧠 Supported Models

The application works with any Ollama-compatible model.

| Model | Installation Command |
| --- | --- |
| Qwen 2.5 Coder | `ollama pull qwen2.5-coder:3b` |
| Llama 3 | `ollama pull llama3` |
| Mistral | `ollama pull mistral` |
| Gemma | `ollama pull gemma3` |
| DeepSeek | `ollama pull deepseek-r1` |
| CodeLlama | `ollama pull codellama` |

---

## 🖥️ Requirements

Before installing the project, make sure the following software is installed:

| Software | Required |
| --- | --- |
| Python 3 | ✅ |
| Ollama | ✅ |
| Git | ✅ |
| Flask | ✅ |

---

# ⚙️ Installation

---

## 1️⃣ Install Ollama

### Ubuntu

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verify the installation:

```bash
ollama --version
```

Example:

```text
ollama version 0.xx.x
```

---

## 2️⃣ Install the AI Model

Install the model used in this project:

```bash
ollama pull qwen2.5-coder:3b
```

Check installed models:

```bash
ollama list
```

Example:

```text
NAME                 ID              SIZE
qwen2.5-coder:3b     xxxxxxxxxxxx     1.9 GB
```

---

## 3️⃣ Clone the Repository

```bash
git clone git@github.com:sayan08880/OLLAMA-UI.git
```

Move into the project directory:

```bash
cd OLLAMA-UI
```

---

## 4️⃣ Install Dependencies

If a `requirements.txt` file exists:

```bash
pip install -r requirements.txt
```

Otherwise:

```bash
pip install flask
```

---

## ▶️ Running the Application

---

### Start the Ollama Server

Open a terminal and run:

```bash
ollama serve
```

Keep the terminal running.

---

### Test the AI Model

Open another terminal:

```bash
ollama run qwen2.5-coder:3b
```

If the model responds correctly, everything is working.

---

### Start OLLAMA-UI

```bash
python app.py
```

Expected output:

```text
==================================================
  Ollama Web UI v3 + File System Commands
  http://localhost:5000
  Ctrl+Shift+N = New Chat
  /allow       = Grant file system access
==================================================
```

---

## 🌐 Open in Your Browser

```text
http://localhost:5000
```

---

## ⌨️ Create the `aiui` Terminal Command

Create the executable file:

```bash
sudo nano /usr/local/bin/aiui
```

Paste:

```bash
#!/bin/bash

cd /home/sayan/Desktop/OLLAMA-UI
python app.py
```

Make it executable:

```bash
sudo chmod +x /usr/local/bin/aiui
```

Now launch the application from anywhere:

```bash
aiui
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action |
| --- | --- |
| `Ctrl + Shift + N` | Create a new chat |
| `/allow` | Enable file system access |

---

## 📁 Project Structure

```text
OLLAMA-UI
├── app.py
├── README.md
├── images
│   └── screenshot.png
├── static
│   ├── style.css
│   ├── script.js
│   └── logo.png
└── templates
    └── index.html
```

---

## 🔄 Updating the Project

After making changes:

```bash
git add .
git commit -m "Update project"
git push
```

Pull the latest changes:

```bash
git pull
```

---

## 🛠️ Technologies Used

- Python
- Flask
- HTML5
- CSS3
- JavaScript
- Ollama
- Local LLMs

---

## 📋 Example Workflow

```text
Install Ollama
        ↓
Install AI Model
        ↓
Clone Repository
        ↓
Install Dependencies
        ↓
Start Ollama
        ↓
Run app.py
        ↓
Open localhost:5000
        ↓
Start Chatting
```

---

## 🔮 Planned Features

- [ ] Multiple AI model support
- [ ] Dark mode
- [ ] Chat history
- [ ] File upload
- [ ] Voice input
- [ ] Drag-and-drop files
- [ ] Theme customization
- [ ] Model switching
- [ ] Export conversations
- [ ] Markdown support
- [ ] Syntax highlighting
- [ ] Multi-chat sessions
- [ ] Mobile-friendly UI
- [ ] Docker support

---

## 🤝 Contributing

Contributions are welcome.

```bash
# Fork the repository

# Create a new branch

git checkout -b feature-name

# Commit your changes

git commit -m "Add new feature"

# Push your branch

git push origin feature-name
```

---

## ⭐ Support the Project

If you like this project:

- ⭐ Star the repository
- 🍴 Fork the project
- 🐛 Report bugs
- 💡 Suggest new features

---

## 👨‍💻 Author

**Sayan Mahalanabish**

GitHub: **@sayan08880**

---

## 📜 License

This project is licensed under the **MIT License**.

---

<div align="center">

### Built with ❤️ using Python + Flask + Ollama

**Run AI locally. Own your data. Control your models.**

</div>
