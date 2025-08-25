from app.core.logging_utils import get_logger


logger = get_logger()


class SmsService:
    def __init__(self, dev_mode: bool = True):
        self.dev_mode = dev_mode

    def send(self, recipient: str, message: str) -> str:
        if self.dev_mode:
            logger.info(f"[MOCK SMS] Would send to {recipient}:\n{message}")
            return "mocked"
        return "failed"