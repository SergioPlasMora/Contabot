import time
import logging
from typing import Callable, Any

class ControlBot:
    def __init__(self, logger: logging.Logger = None):
        """
        Initialize ControlBot with an optional logger.
        
        :param logger: Custom logger instance (default: module-level logger)
        """
        self.logger = logger or logging.getLogger(__name__)

    def wait_for_element(self, element, timeout: int = 60, poll_interval: float = 1.0) -> bool:
        """
        Wait for an element to exist and become visible.
        
        :param element: Element to wait for
        :param timeout: Maximum wait time in seconds
        :param poll_interval: Time between checks in seconds
        :return: True if element appears within timeout
        :raises TimeoutError: If element doesn't appear within timeout
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if element.exists() and element.is_visible():
                    self.logger.info(f"Element {element} found successfully")
                    return True
            except Exception as e:
                self.logger.debug(f"Error checking element: {e}")
            time.sleep(poll_interval)
        
        self.logger.error(f"Element {element} not found within {timeout} seconds")
        raise TimeoutError(f"Element {element} did not appear in {timeout} seconds")

    def verify_element_state(
        self,
        element,
        timeout: int = 5,
        poll_interval: float = 0.1,
        log_errors: bool = True
    ) -> bool:
        """
        Verify element's existence, visibility, and enabled state.
        
        :param element: Element to verify
        :param timeout: Maximum wait time
        :param poll_interval: Check interval
        :param log_errors: Whether to log verification errors
        :return: True if element is ready within timeout, False otherwise
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if element.exists() and element.is_visible() and element.is_enabled():
                    return True
            except Exception as e:
                if log_errors:
                    self.logger.debug(f"Error verifying element state: {e}")
            time.sleep(poll_interval)
        return False

    def retry_action(
        self,
        action: Callable[[], Any],
        max_retries: int = 5,
        initial_delay: float = 1.0,
        backoff_factor: float = 2.0
    ) -> Any:
        """
        Retry an action with exponential backoff.
        
        :param action: Function to retry
        :param max_retries: Maximum number of retry attempts
        :param initial_delay: Initial delay in seconds
        :param backoff_factor: Multiplier for delay between retries
        :return: Result of successful action
        :raises Exception: If all retries fail
        """
        delay = initial_delay
        for attempt in range(max_retries):
            try:
                return action()
            except Exception as e:
                self.logger.warning(
                    f"Attempt {attempt+1} failed: {e}. Retrying in {delay} seconds..."
                )
                time.sleep(delay)
                delay *= backoff_factor
        raise Exception("Action failed after multiple retry attempts")
