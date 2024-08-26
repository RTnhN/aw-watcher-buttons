const int numButtons = 5;                 // Number of buttons and LEDs
const int buttonPins[numButtons] = {9, 10, 11, 12, 13}; // the number of the button pins
const int ledPins[numButtons] = {4, 5, 6, 7, 8};       // the number of the LED pins

int buttonStates[numButtons] = {0, 0, 0, 0, 0};        // variable for reading the button status
int lastButtonStates[numButtons] = {0, 0, 0, 0, 0};    // the previous reading from the input pin
int ledStates[numButtons] = {0, 0, 0, 0, 0};           // stores the state of each LED

unsigned long lastDebounceTimes[numButtons] = {0, 0, 0, 0, 0}; // the last time the output pin was toggled
unsigned long debounceDelay = 2;                              // the debounce time; increase if the output flickers

// Structures to hold the state of each blinking LED
struct BlinkState {
  unsigned long previousMillis = 0; // Stores the last time the LED was updated
  int blinkCount = 0;               // Number of blinks performed
  int totalBlinks = 0;              // Total number of blinks requested
  int ledState = LOW;               // Current state of the LED
  int period = 0;                   // Blinking period
  int initialState = LOW;           // Initial state of the LED before blinking
};

BlinkState blinkStates[numButtons]; // Array to hold the blink states of each LED

void setup() {
  for (int i = 0; i < numButtons; i++) {
    pinMode(ledPins[i], OUTPUT);       // initialize the LED pin as an output
    pinMode(buttonPins[i], INPUT_PULLUP); // initialize the button pin as an input
  }
  Serial.begin(115200);                // initialize the serial communication
}

void loop() {
  // Handle serial data at the beginning of the loop
  if (Serial.available() > 0) {
    String incomingData = Serial.readStringUntil('\n'); // read until newline
    if (incomingData.length() > 0) { // check if there's data
      handleSerialCommand(incomingData); // Process the serial command
    }
  }

  // Process button states
  for (int i = 0; i < numButtons; i++) {
    int reading = digitalRead(buttonPins[i]);
    if (reading != lastButtonStates[i]) {
      lastDebounceTimes[i] = millis(); // Reset debounce timer on state change
    }

    if ((millis() - lastDebounceTimes[i]) > debounceDelay) {
      if (reading != buttonStates[i]) {
        buttonStates[i] = reading;
        if (buttonStates[i] == LOW) { // Button is pressed
          turnOnLED(i);               // Turn on the corresponding LED
        }
      }
    }
    lastButtonStates[i] = reading; // Update the last button state
  }

  // Update the blinking LEDs
  updateBlinkingLEDs();
}

// Function to handle serial commands
void handleSerialCommand(String command) {
  if (command == "state") {
    // Respond with the number of the LED that is currently on
    int ledOn = -1;
    for (int i = 0; i < numButtons; i++) {
      if (ledStates[i] == HIGH) {
        ledOn = i + 1; // LED numbers are 1-based
        break;
      }
    }
    Serial.println(ledOn); // Print the LED number or -1 if none are on
  } else if (command.startsWith("b")) {
    // Parse the blink command in the form of bxyz where x is the led, y is the number of 100's of ms, and z is 
    // the number of blinks up to 9 
    int ledNumber = command.substring(1, 2).toInt();   // Extract the LED number x
    int period = command.substring(2, 3).toInt() * 100; // Extract and convert the blink period (y * 100 ms)
    int blinks = command.substring(3).toInt();         // Extract the number of blinks (z)
    if (ledNumber >= 1 && ledNumber <= numButtons) {
      blinkLED(ledNumber - 1, period, blinks); // Initiate the blink operation
    }
  }
}

// Function to turn on a specific LED and turn off all others
void turnOnLED(int ledIndex) {
  // Turn off all LEDs first to maintain mutual exclusivity
  for (int i = 0; i < numButtons; i++) {
    digitalWrite(ledPins[i], LOW);
    ledStates[i] = LOW;
    blinkStates[i].blinkCount = blinkStates[i].totalBlinks * 2; 
    blinkStates[i].initialState = LOW; 
  }

  // Turn on the selected LED
  digitalWrite(ledPins[ledIndex], HIGH);
  ledStates[ledIndex] = HIGH;
  blinkStates[ledIndex].initialState = HIGH; 
}

// Non-blocking function to blink a specific LED with a given period and number of blinks
void blinkLED(int ledIndex, int period, int blinks) {
  blinkStates[ledIndex].blinkCount = 0;         // Reset the blink count
  blinkStates[ledIndex].totalBlinks = blinks;   // Set the total number of blinks
  blinkStates[ledIndex].period = period;        // Set the blinking period
  blinkStates[ledIndex].previousMillis = millis(); // Reset the timer
  blinkStates[ledIndex].initialState = ledStates[ledIndex]; // Save the initial state of the LED
  blinkStates[ledIndex].ledState = ledStates[ledIndex];     // Start with the LED in its current state
}

void updateBlinkingLEDs() {
  for (int i = 0; i < numButtons; i++) {
    if (blinkStates[i].blinkCount < blinkStates[i].totalBlinks * 2) {
      unsigned long currentMillis = millis();

      // Check if it's time to toggle the LED state
      if (currentMillis - blinkStates[i].previousMillis >= (blinkStates[i].period / 2)) {
        blinkStates[i].previousMillis = currentMillis; // Reset the timer
        // Toggle the LED state
        blinkStates[i].ledState = !blinkStates[i].ledState;
        digitalWrite(ledPins[i], blinkStates[i].ledState);

        // Increment the blink count after every complete blink (on and off)
        if (blinkStates[i].ledState == blinkStates[i].initialState) {
          blinkStates[i].blinkCount++;
        }
      }
    } else {
      // Restore the LED to its initial state after blinking is complete
      digitalWrite(ledPins[i], blinkStates[i].initialState);
      ledStates[i] = blinkStates[i].initialState;
    }
  }
}
