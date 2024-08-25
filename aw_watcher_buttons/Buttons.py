import serial
import time


class LEDController:
    def __init__(self, port, baudrate=115200, timeout=1):
        """
        Initializes the LEDController class with the given serial port parameters.

        Args:
            port (str): The serial port to which the Arduino is connected.
            baudrate (int, optional): The baud rate for the serial communication. Defaults to 115200.
            timeout (int, optional): The timeout for reading from the serial port. Defaults to 1 second.
        """
        self.serial = serial.Serial(port, baudrate, timeout=timeout)
        self.led_state = -1  # -1 means no LED is on

    def _send_command(self, command):
        """
        Sends a command to the Arduino via the serial port.

        Args:
            command (str): The command string to send to the Arduino.
        """
        self.serial.write(f"{command}\n".encode())
        time.sleep(0.1)  # Small delay to allow Arduino to process the command

    def update_led_state(self):
        """
        Updates the internal state of the LED by querying the Arduino.
        """
        self._send_command("state")
        response = self.serial.readline().decode().strip()
        if response.isdigit():
            self.led_state = int(response)
        else:
            self.led_state = -1  # If the response is not a valid number, set to -1

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
        """
        Closes the serial connection.
        """
        self.serial.close()


if __name__ == "__main__":
    led_controller = LEDController("COM12")  # Adjust the port to your Arduino's port
    print(led_controller.get_led_state())
    led_controller.blink_led(1, 5, 3)  # Blink LED 1 with a period of 500ms, 3 times
    led_controller.close()
