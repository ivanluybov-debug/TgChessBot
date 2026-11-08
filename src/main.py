import asyncio
import sys
from pathlib import Path

# Добавляем корень проекта в sys.path, чтобы работали импорты из корня
sys.path.append(str(Path(__file__).resolve().parent.parent))

from bot import start_bot

if __name__ == "__main__":
    asyncio.run(start_bot())
