# Chatty Patty

A terminal-based chat application with a modern TUI (Textual User Interface) built using Python and Textual.

![Chatty Patty Screenshot](screenshot.png)

## Features

- 🚀 Modern terminal-based user interface
- 👥 User directory with online/offline status
- 🔍 Search functionality to find users quickly
- 📝 Profile setup for new users
- 💬 Simple chat interface (coming soon)

## Prerequisites

- Python 3.8 or higher
- Poetry (for dependency management)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/tui.git
   cd tui
   ```

2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```

## Usage

1. Activate the virtual environment:
   ```bash
   poetry shell
   ```

2. Run the application:
   ```bash
   poetry run chat-app
   ```
   or
   ```bash
   python main.py
   ```

## Building the Application

To create a standalone executable:

```bash
poetry run pyinstaller --onefile --name ChattyPatty main.py
```

The executable will be available in the `dist` directory.

## Project Structure

```
tui/
├── src/
│   ├── __init__.py
│   ├── main.py            # Application entry point
│   ├── users_discovery.py # User directory and interface
│   └── profile_setup.py   # User profile setup
├── pyproject.toml         # Project dependencies and metadata
└── README.md              # This file
```

## Dependencies

- [Textual](https://textual.textualize.io/) - Modern Python framework for TUI applications
- Poetry - Python dependency management

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with ❤️ using Python and Textual
- Inspired by modern chat applications
