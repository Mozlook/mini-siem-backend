class LogDirUnavailableError(Exception):
    def __init__(self, log_dir: str, message: str = "Log dir not available"):
        self.log_dir: str = log_dir
        super().__init__(message)


class EventDetailsNotFound(Exception):
    def __init__(self, id: int, message: str = "Event details not found"):
        self.id: int = id
        super().__init__(message)
