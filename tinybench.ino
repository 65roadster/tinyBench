////////////////////////////////////////////////////////
//
// Developed by R. Crampton
// V0.6
// Oct, 2022
//
// Teensy 3.2 "tinybench"
// DEBUG_PIN is used for debug purposes
//    - One minimum width pulse will be output on pin 2 after the CPU is rebooted
//    - Two minimum width pulse will be output on pin 2 when a command is received
//    - Three minimum width pulses will be output on pin 2 if an invalid command is received
//    - Minimum width pulses are 484ns wide

#include <i2c_t3.h>
#include <SPI.h>

#define CMD_PING            "00"
#define CMD_GET_FW_REV      "01"
#define CMD_ADC_GET         "02"
#define CMD_DAC_SET         "03"
#define CMD_GPIO_GET        "04"
#define CMD_GPIO_SET        "05"
#define CMD_I2C_START       "06"
#define CMD_I2C_WRITE_BYTE  "07"
#define CMD_I2C_END         "08"
#define CMD_END_OF_LIST     "FF"

#define VERSION "0.6"

// pin name lookup table for CMD_ADC_GET
const uint8_t ADCPINS[] = {A0, A1, A2, A3, A4, A5, A6, A7, A8, A9};

char message[8];
char cmd[5];
uint8_t incomingByte;
uint8_t bytecount = 0;

//#define DEBUG
const uint8_t DEBUG_PIN = 1;

void setup() {
  // reset message back to empty string
  strncpy(message, "\0\0\0\0\0\0\0\0", 8);
  
  // Wire bus, SCL pin 19, SDA pin 18, ext pullup, 100kHz
  Wire.begin(I2C_MASTER, 0x00, I2C_PINS_18_19, I2C_PULLUP_EXT, 100000);
  Wire.setDefaultTimeout(250000); // 250ms default timeout

  // set up SPI port and CS pins
  SPI.begin();
  SPI.beginTransaction(SPISettings(250000, MSBFIRST, SPI_MODE0));

  pinMode(DEBUG_PIN, OUTPUT);

  // startup pulse for debug
  #ifdef DEBUG
    digitalWrite(DEBUG_PIN, LOW);
    digitalWrite(DEBUG_PIN, HIGH);
    digitalWrite(DEBUG_PIN, LOW);
  #endif

  analogWriteResolution(12);
  analogReadRes(16);
}

void loop() {

  while (Serial.available()) {
    incomingByte = Serial.read();
    message[bytecount] = incomingByte;
    bytecount++;
    
    // if we have a complete command
    if (bytecount == 6) {
      #ifdef DEBUG
        digitalWrite(DEBUG_PIN, LOW);
        digitalWrite(DEBUG_PIN, HIGH);
        digitalWrite(DEBUG_PIN, LOW);
        digitalWrite(DEBUG_PIN, HIGH);
        digitalWrite(DEBUG_PIN, LOW);
      #endif

      // cmd[0:1] = command being sent
      // message[2:5] are additional parameters used by certain commands
      cmd[0] = message[0];
      cmd[1] = message[1];
      cmd[2] = '\0';

      // ~4us execution time
      if (!strcmp(cmd, CMD_PING)) {
        Serial.print("PING");
      }
      // ~4us execution time
      else if (!strcmp(cmd, CMD_GET_FW_REV)) {
        Serial.print(VERSION);
      }
      // ~25us execution time
      else if (!strcmp(cmd, CMD_ADC_GET)) {
        int channel = message[2] - '0';
        pinMode(ADCPINS[channel], INPUT);
        Serial.println(analogRead(ADCPINS[channel]));
      }
      // ~8us execution time
      else if (!strcmp(cmd, CMD_GPIO_GET)) {
        int pin = message[2] - '0';
        pinMode(pin, INPUT);

        if (digitalRead(pin)) {
          Serial.println('1');
        }
        else {
          Serial.println('0');
        }
      }
      // ~2us execution time
      else if (!strcmp(cmd, CMD_GPIO_SET)) {
        int pin = message[2] - '0';
        pinMode(pin, OUTPUT);
        bool state = LOW;
        if (message[3] - '0' == 1) {
          state = HIGH;
        }
        digitalWrite(pin,state);
      }
      // ~0.9us execution time
      else if (!strcmp(cmd, CMD_I2C_START)) {
        int address;
        address = 10*(message[2] - '0') + (message[3] - '0');
        Wire.beginTransmission(address);
      }
      // ~4us execution time
      else if (!strcmp(cmd, CMD_I2C_WRITE_BYTE)) {
        char stuff[2];
        stuff[0] = message[2];
        stuff[1] = message[3];
        int stufftosend = strtol(stuff, NULL, 16);
        Wire.write(stufftosend);
      }
      // 200us execution time, 100kHz I2C - waits for data to be sent over bus
      else if (!strcmp(cmd, CMD_I2C_END)) {
        Wire.endTransmission();
      }
      // ~14us execution time
      else if (!strcmp(cmd, CMD_DAC_SET)) {
        char value[5];
        value[0] = message[2];
        value[1] = message[3];
        value[2] = message[4];
        value[3] = message[5];
        value[4] = '\0';

        int val;
        sscanf(value, "%d", &val);
        analogWrite(A14, val);
      }
      else {
        #ifdef DEBUG
          digitalWrite(DEBUG_PIN, LOW);
          digitalWrite(DEBUG_PIN, HIGH);
          digitalWrite(DEBUG_PIN, LOW);
          digitalWrite(DEBUG_PIN, HIGH);
          digitalWrite(DEBUG_PIN, LOW);
          digitalWrite(DEBUG_PIN, HIGH);
          digitalWrite(DEBUG_PIN, LOW);
        #endif
      }
      
      // reset message string
      strncpy(message, "\0\0\0\0\0\0\0\0", 8);
      bytecount = 0;

      // reset command to unused value
      strncpy(cmd, "FF\0\0\0", 5);
    }
  }
}
