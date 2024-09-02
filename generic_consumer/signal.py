from enum import Enum
import uuid


class Signal(Enum):
    CONTINUE = uuid.uuid4()
    """
    Empty signal.
    
    This does nothing,
    and will not be returned.
    """
    BREAK = uuid.uuid4()
    """
    Stops the current process
    for the current consumer.
    """
    INTERRUPT = uuid.uuid4()
    """
    Stops the current and the next processes
    for the current consumer.
    """
    TERMINATE = uuid.uuid4()
    """
    Stops the current and the next processes
    for all consumer.
    """
