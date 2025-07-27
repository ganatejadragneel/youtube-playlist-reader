# YouTube Playlist Reader 🎬

An AI-powered YouTube playlist analyzer that uses local Ollama LLMs to answer questions about video content. Built with Python, FastAPI, and modern web technologies.

![Python](https://img.shields.io/badge/python-v3.10+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)
![Ollama](https://img.shields.io/badge/Ollama-Local%20LLM-orange.svg)

## ✨ Features

- 🤖 **AI-Powered Q&A**: Ask questions about playlist content using local Ollama
- 📺 **YouTube Integration**: Fetch playlist metadata and video information
- 🔍 **Smart Search**: Find videos by keywords with intelligent matching
- 🌐 **Modern Web UI**: Clean, responsive interface with real-time updates
- 📊 **Analytics**: Get AI-generated summaries and insights
- 🔒 **Privacy-First**: All AI processing happens locally via Ollama

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai/) installed and running
- YouTube Data API v3 key (optional, for enhanced features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/youtube_reader.git
   cd youtube_reader
   ```

2. **Set up virtual environment**
   ```bash
   python3.10 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env to add your YouTube API key and playlist URL
   ```

5. **Start Ollama**
   ```bash
   # Make sure Ollama is running with llama3.2
   ollama serve
   ollama pull llama3.2
   ```

6. **Run the application**
   ```bash
   python run_server.py
   ```

7. **Open your browser**
   ```
   http://localhost:8000
   ```

## 🎯 Usage

### Web Interface

- **📋 Get Summary**: AI analysis of your playlist content
- **🤖 Ask Questions**: Natural language queries about videos
- **🔍 Search Videos**: Find specific content by keywords
- **📺 Browse Videos**: View recent uploads and metadata

### API Endpoints

- `GET /api/health` - Check service status
- `GET /api/summary` - Get playlist summary
- `POST /api/ask` - Ask questions about content
- `POST /api/search` - Search videos
- `GET /api/playlist/videos` - List videos

### Example Questions

- "What kind of games do they play?"
- "How many videos are in this playlist?"
- "What can viewers expect from these videos?"
- "Are these videos recent or older content?"

## 🔧 Configuration

Edit `.env` file:

```env
# YouTube Configuration
YOUTUBE_PLAYLIST_URL=https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID
YOUTUBE_API_KEY=your_youtube_api_key_here

# Ollama Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest

# Application Configuration
LOG_LEVEL=INFO
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Test specific components
pytest tests/unit/test_qa_service.py -v

# Test the demo
python demo_qa.py
```

## 📁 Project Structure

```
youtube_reader/
├── src/
│   ├── adapters/           # External service integrations
│   │   ├── youtube_adapter.py     # YouTube API client
│   │   ├── ollama_adapter.py      # Ollama LLM client
│   │   └── transcript_extractor.py # Video transcript extraction
│   ├── api/                # FastAPI web interface
│   │   ├── app.py         # Main FastAPI application
│   │   ├── routes.py      # API route definitions
│   │   ├── models.py      # Request/response models
│   │   └── static/        # Web UI files
│   ├── core/              # Domain models
│   ├── config/            # Configuration management
│   ├── interfaces/        # Abstract interfaces
│   └── services/          # Business logic
├── tests/                 # Comprehensive test suite
├── data/                  # Local data storage
└── docs/                  # Documentation
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai/) for local LLM capabilities
- [FastAPI](https://fastapi.tiangolo.com/) for the web framework
- [HTMX](https://htmx.org/) for dynamic web interactions
- [Tailwind CSS](https://tailwindcss.com/) for styling

## 🐛 Issues & Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/yourusername/youtube_reader/issues) page
2. Create a new issue with detailed information
3. Include logs and configuration details

## 🔮 Roadmap

- [ ] Vector embeddings for semantic search
- [ ] Support for multiple LLM providers
- [ ] Video transcript analysis
- [ ] Export capabilities (PDF, markdown)
- [ ] Batch playlist processing
- [ ] Docker containerization