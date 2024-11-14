class FrameNotFoundException(Exception):
    """Exception raised when a specific frame is not found in the page."""
    def __init__(self, frame_name: str, message: str = None):
        if message is None:
            message = f"Frame '{frame_name}' could not be found."
        super().__init__(message)
        self.frame_name = frame_name