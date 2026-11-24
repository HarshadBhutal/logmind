
import asyncio
from pathlib import Path
from collections.abc import AsyncIterator

from collector.config import settings


class FileReader:
    def __init__(self, file_path: Path | None = None):
        self.file_path = file_path or settings.LOG_FILE_PATH
        self.offset = 0
        self.pending = b""
        self._initialized = False

    async def read_lines(self) -> AsyncIterator[str]:
        while True:
            # Wait until the log file is created.
            if not self.file_path.exists():
                await asyncio.sleep(settings.POLL_INTERVAL)
                continue

            # Initialize the reading position only once.
            if not self._initialized:
                if not settings.READ_FROM_START:
                    self.offset = self.file_path.stat().st_size

                self._initialized = True

            # Read newly appended bytes.
            with self.file_path.open("rb") as file:
                file.seek(self.offset)
                data = file.read()
                self.offset = file.tell()

            if data:
                self.pending += data

                # Split complete lines while retaining incomplete data.
                lines = self.pending.split(b"\n")
                self.pending = lines.pop()

                for line in lines:
                    decoded = line.rstrip(b"\r").decode(
                        "utf-8",
                        errors="replace"
                    )

                    if decoded:
                        yield decoded

            await asyncio.sleep(settings.POLL_INTERVAL)
