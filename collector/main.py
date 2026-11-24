
import asyncio
import logging

from collector.buffer import LogBuffer
from collector.config import settings
from collector.exporter import LogExporter
from collector.parser import LogParser
from collector.reader import FileReader

logger = logging.getLogger(__name__)


class LogCollector:
    def __init__(self):
        self.reader = FileReader()
        self.parser = LogParser()
        self.buffer = LogBuffer(capacity=settings.BUFFER_CAPACITY)
        self.exporter = LogExporter()

        self.running = False
        self.shutdown_event = asyncio.Event()

    async def collect_logs(self):
        """Read, parse, and buffer incoming log lines."""
        try:
            async for raw_line in self.reader.read_lines():
                if not self.running:
                    break

                event = self.parser.parse(raw_line)

                if event is None:
                    logger.warning("Skipping invalid log line: %s", raw_line)
                    continue

                if not self.buffer.add(event):
                    logger.warning(
                        "Log buffer is full. Dropped events: %s",
                        self.buffer.dropped
                    )
        except asyncio.CancelledError:
            logger.info("Log collection task cancelled")
            raise

    async def export_logs(self):
        """Export buffered events while collection is active."""
        while self.running:
            batch = self.buffer.peek_batch(settings.BATCH_SIZE)

            if not batch:
                await asyncio.sleep(settings.POLL_INTERVAL)
                continue

            success = await self.exporter.send_batch(batch)

            if success:
                self.buffer.acknowledge(len(batch))
                logger.info("Successfully exported %s events", len(batch))
            else:
                logger.warning(
                    "Batch delivery failed. Events remain in buffer."
                )
                await asyncio.sleep(settings.RETRY_BACKOFF)

    async def flush_buffer(self):
        """Attempt to export remaining events during shutdown."""
        logger.info("Flushing remaining buffered events")

        try:
            while self.buffer.size > 0:
                batch = self.buffer.peek_batch(settings.BATCH_SIZE)

                success = await self.exporter.send_batch(batch)

                if not success:
                    logger.error(
                        "Unable to export remaining buffered events"
                    )
                    break

                self.buffer.acknowledge(len(batch))
                logger.info("Flushed %s events", len(batch))

        except Exception:
            logger.exception("Error while flushing buffer")

        if self.buffer.size:
            logger.warning(
                "%s events remain in memory and may be lost",
                self.buffer.size
            )

    async def start(self):
        """Start collection and export tasks."""
        self.running = True
        logger.info("LogMind Collector started")

        collection_task = asyncio.create_task(self.collect_logs())
        export_task = asyncio.create_task(self.export_logs())

        try:
            await self.shutdown_event.wait()

        finally:
            logger.info("Starting collector shutdown")

            # Stop new collection and normal exporting.
            self.running = False

            collection_task.cancel()

            await asyncio.gather(
                collection_task,
                return_exceptions=True
            )

            # Let the normal exporter finish its current operation.
            try:
                await asyncio.wait_for(
                    export_task,
                    timeout=settings.SHUTDOWN_TIMEOUT
                )
            except asyncio.TimeoutError:
                logger.warning("Exporter shutdown timed out")
                export_task.cancel()
                await asyncio.gather(
                    export_task,
                    return_exceptions=True
                )

            # Try to deliver anything still buffered.
            try:
                await asyncio.wait_for(
                    self.flush_buffer(),
                    timeout=settings.SHUTDOWN_TIMEOUT
                )
            except asyncio.TimeoutError:
                logger.error("Buffer flush timed out")

            await self.exporter.close()

            logger.info("LogMind Collector stopped")

    async def stop(self):
        """Request graceful shutdown."""
        logger.info("Shutdown requested")
        self.shutdown_event.set()


async def main():
    collector = LogCollector()

    try:
        await collector.start()
    except KeyboardInterrupt:
        await collector.stop()


if __name__ == "__main__":
    asyncio.run(main())
