import logging
import time

import serial


logger = logging.getLogger(__name__)


class Buttons:
    def __init__(self, ports, baudrate=115200, timeout=1):
        """Manage serial communication with the Arduino-backed button panel."""

        if isinstance(ports, str):
            ports = [ports]
        # Keep port order stable while removing empty entries and duplicates.
        self._ports = []
        for port in ports or []:
            if port and port not in self._ports:
                self._ports.append(port)

        if not self._ports:
            raise ValueError("No serial ports configured for the button device.")

        self.port = None
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial = None
        self.led_state = -1  # -1 means no LED is on
        self._connected = False
        self._warned_disconnected_ports = set()
        self._last_connect_attempt = 0.0
        self._reconnect_interval = 1.0  # seconds between connect attempts

        # Attempt an initial connection so we can fail fast if the port is wrong.
        self._ensure_connection(force=True)

    def _cleanup_serial(self):
        if self.serial:
            try:
                self.serial.close()
            except Exception:  # noqa: BLE001 - ignore cleanup errors
                pass
        self.serial = None

    def _mark_connected(self, port):
        if not self._connected or self.port != port:
            logger.info("Connected to button device on %s", port)
        self.port = port
        self._connected = True
        self._warned_disconnected_ports.discard(port)

    def _mark_disconnected(self, port, exc, *, lost):
        already_warned = port in self._warned_disconnected_ports
        if lost:
            logger.warning("Lost connection to %s: %s", port, exc)
        elif not already_warned:
            logger.warning(
                "Unable to connect to %s (will keep retrying): %s", port, exc
            )
        if not lost:
            self._warned_disconnected_ports.add(port)
        self.port = port
        self._connected = False

    def _connect(self):
        for port in self._ports:
            try:
                self.serial = serial.Serial(
                    port,
                    self.baudrate,
                    timeout=self.timeout,
                )
                self.serial.reset_input_buffer()
                self.serial.reset_output_buffer()
                self._mark_connected(port)
                return True
            except (serial.SerialException, OSError) as exc:
                was_connected = self._connected and self.port == port
                self._cleanup_serial()
                self._mark_disconnected(port, exc, lost=was_connected)
        return False

    def _ensure_connection(self, force=False):
        if self.serial and self.serial.is_open:
            return True

        now = time.monotonic()
        if not force and (now - self._last_connect_attempt) < self._reconnect_interval:
            return False

        self._last_connect_attempt = now
        return self._connect()

    def _handle_serial_error(self, exc):
        was_connected = self._connected
        self._cleanup_serial()
        self._mark_disconnected(self.port, exc, lost=was_connected)

    def _send_command(self, command):
        if not self._ensure_connection():
            return False

        try:
            self.serial.write(f"{command}\n".encode())
            self.serial.flush()
            time.sleep(0.1)  # Small delay to allow Arduino to process the command
            return True
        except (serial.SerialException, OSError) as exc:
            logger.warning("Error sending command '%s': %s", command, exc)
            self._handle_serial_error(exc)
            return False

    def update_led_state(self):
        """Update the cached LED index from the Arduino."""

        if not self._send_command("state"):
            self.led_state = -1
            return

        try:
            response = self.serial.readline().decode(errors="ignore").strip()
            if response.isdigit():
                self.led_state = int(response)
            else:
                self.led_state = -1  # If the response is not a valid number, set to -1
        except (serial.SerialException, OSError) as exc:
            logger.warning("Error reading button state, will retry: %s", exc)
            self._handle_serial_error(exc)
            self.led_state = -1

    def get_led_state(self):
        """
        Returns the current state of the LEDs.

        Returns:
            int: The number of the LED that is currently on, or -1 if no LED is on.
        """
        self.update_led_state()
        return self.led_state

    def blink_led(self, led_number, period, blinks):
        """
        Blinks a specific LED with the given period and number of blinks.

        Args:
            led_number (int): The number of the LED to blink (1-5).
            period (int): The blink period in hundreds of milliseconds (e.g., 5 for 500ms).
            blinks (int): The number of times the LED should blink.
        """
        if 1 <= led_number <= 5 and period > 0 and blinks > 0:
            command = f"b{led_number}{period}{blinks}"
            self._send_command(command)

    def close(self):
        """Close the serial connection."""

        self._cleanup_serial()
        self._connected = False

    def is_connected(self):
        """Return True when the USB device is available and ready."""

        return self._connected
