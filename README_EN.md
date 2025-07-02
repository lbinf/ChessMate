# ChessMate

## Project Introduction
ChessMate is a Xiangqi (Chinese Chess) assistant analysis platform based on Flask. It integrates image recognition and AI engines to automatically recognize board screenshots and provide the best move suggestions, supporting major platforms such as JJ Xiangqi.

## Features
- Intelligent board image recognition, generates FEN strings
- AI engine analysis, best moves powered by [ChessDB Cloud](https://www.chessdb.cn/) and [Pikafish](https://github.com/official-pikafish/Pikafish)
- Multi-platform support
- Command-line Xiangqi assistant
- History records
- Modern frontend
- Logging & error handling
- Message queue (Redis) support for JJ Xiangqi AI battles and automatic hint features. [Documentation](doc/REDIS_MESSAGE_QUEUE.md)

---

## UI Screenshots
- Web interface
![Main UI Screenshot](doc/images/ui_screenshot.png)
- Command line
![CLI Screenshot 1](doc/images/cli_1.png)
![CLI Screenshot 2](doc/images/cli_2.png)

---

## Installation

### Clone the repository
```bash
git clone https://github.com/lbinf/ChessMate
cd ChessMate
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Ensure Pikafish engine is executable
See Pikafish build and usage: https://github.com/official-pikafish/Pikafish

```bash
chmod +x ./app/Pikafish/src/pikafish
```

### Run the app
```bash
python run.py
```

### Run the command-line interface
- Linux
```
./start_chess.sh
```
- Windows
```
start_chess.bat
```
- Python
```
python chess_cli.py --cli
```

---

## Testing
- Run all tests:
```bash
pytest
```
- Covers API, algorithms, database, etc.

---

## Deployment
- Local development: `python run.py`
- Production: `gunicorn -c gunicorn.conf.py run:app`
- Docker: `docker-compose up -d`
- See [doc/DEPLOYMENT_GUIDE.md](doc/DEPLOYMENT_GUIDE.md)

---

## Contribution Guide
- Follow PEP8
- Add docstrings
- Ensure all tests pass
- PRs & Issues welcome

---

## Completed Features
- Board image recognition
- AI engine analysis
- Multi-platform support
- Parameter tuning
- Basic frontend
- Logging & error handling
- Unit & integration tests
- Redis message queue integration

---

## License
MIT
- See [LICENSE](LICENSE)

## Acknowledgements
- Pikafish
- OpenCV
- Flask
- Bootstrap 