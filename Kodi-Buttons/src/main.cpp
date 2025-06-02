#include <Arduino.h>
#include <HT_SSD1306Wire.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

static SSD1306Wire display(0x3c, 500000, SDA_OLED, SCL_OLED, GEOMETRY_128_64, RST_OLED); // addr , freq , i2c group , resolution , rst
static int mode = 0;
BLEServer *pServer = NULL;
BLECharacteristic * pTxCharacteristic;
bool deviceConnected = false;
bool oldDeviceConnected = false;
uint8_t txValue = 0;

#define SERVICE_UUID           "6E400001-B5A3-F393-E0A9-E50E24DCCA9E" // UART service UUID
#define CHARACTERISTIC_UUID_RX "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
#define CHARACTERISTIC_UUID_TX "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

class MyServerCallbacks: public BLEServerCallbacks {
  void onConnect(BLEServer* pServer, esp_ble_gatts_cb_param_t *param) {
    Serial.println("Client connected");
    pServer->updateConnParams(param->connect.remote_bda, 6, 6, 0, 100);
    pServer->getAdvertising()->stop();
    deviceConnected = true;
  };

  void onDisconnect(BLEServer* pServer) {
    deviceConnected = false;
  }
};

int pos_after_nth_occurance(const char *str, char c, int n) {
  int i, j;
  for (i = 0, j = 0; i < strlen(str); i++) {
    if (str[i] == c) {
      if (j == n-1) break;
      j++;
    }
  }
  return i+1;
}

class MyCallbacks: public BLECharacteristicCallbacks {
  void onWrite(BLECharacteristic *pCharacteristic) override {
    std::string rxValue = pCharacteristic->getValue();
    int x0,y0,x1,y1, i, j, offset, bit;

    if (rxValue.length() > 0) {
      if (rxValue[0] == 'L') {
        sscanf(rxValue.c_str(), "L%d %d %d %d", &x0, &y0, &x1, &y1);
        display.drawLine(x0, y0, x1, y1);
      } else if (rxValue[0] == 'C') {
        display.clear();
      } else if (rxValue[0] == 'S') {
        sscanf(rxValue.c_str(), "S%d %d", &x0, &y0);
        display.drawString(x0, y0, rxValue.c_str() + pos_after_nth_occurance(rxValue.c_str(), ' ', 2));
      } else if (rxValue[0] == 'D') {
        display.display();
      } else if (rxValue[0] == 'V') {
        if (rxValue[1] == 'T') {
          switch(rxValue[2]) {
            case '1':
              display.setFont(ArialMT_Plain_10);
              break;
            case '2':
              display.setFont(ArialMT_Plain_16);
              break;
            case '3':
              display.setFont(ArialMT_Plain_24);
              break;
          }
        }
      } else if (rxValue[0] == 'P') {
        sscanf(rxValue.c_str(), "P%d %d %d %d", &x0, &y0, &x1, &y1);
        offset = pos_after_nth_occurance(rxValue.c_str(), ' ', 4);
        //for (i = 0; i < offset; i++) Serial.print(rxValue[i]);
        //Serial.print("\n");
        //Serial.printf("offset: %d, x: %d, y: %d\n", offset, x0, y0);
        for (i = 0; i < x1; i++) {
          for (j = 0; j < y1; j++) {
            // if (j % 8 == 0) Serial.printf("%02x ", rxValue[offset+i*8+j/8]);
            if (i+j/8 < rxValue.length()) {
              bit = (rxValue[offset+i*8+j/8] & (1 << (j%8)));
              //Serial.print(bit ? '1' : '0');
              display.setPixelColor(i+x0, j+y0, bit ? WHITE : BLACK);
            }
          }
          //Serial.print("\n");
        }
      } else if (rxValue[0] == 'T') {
        for (i = 0; i < 25; i++) {
          display.setPixelColor(20, 20+i, WHITE);
        }
        sleep(2);
        display.fillRect(0, 0, 128, 64);
        sleep(2);
      }
      Serial.println("*********");
      Serial.print("Received Value: ");

      if (rxValue.length() < 20) {
        for (int i = 0; i < rxValue.length(); i++)
          Serial.print(rxValue[i]);
      }

      Serial.println();
      Serial.println("*********");
    }
  }
  void onRead(BLECharacteristic *pCharacteristic) override {
    pCharacteristic->setValue("Hey");
  }
};
void VextON(void)
{
  pinMode(Vext,OUTPUT);
  digitalWrite(Vext, LOW);
}

void VextOFF(void) //Vext default OFF
{
  pinMode(Vext,OUTPUT);
  digitalWrite(Vext, HIGH);
}

void IRAM_ATTR ISR() {
  if (digitalRead(0) == 1) {
    pTxCharacteristic->setValue("down");
  } else {
    pTxCharacteristic->setValue("up");
  }
  pTxCharacteristic->notify();
}


void setup() {
  Serial.begin(115200);

  // Create the BLE Device
  BLEDevice::init("UART Service");


  // Create the BLE Server
  pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  // Create the BLE Service
  BLEService *pService = pServer->createService(SERVICE_UUID);

  // Create a BLE Characteristic
  pTxCharacteristic = pService->createCharacteristic(
										CHARACTERISTIC_UUID_TX,
										BLECharacteristic::PROPERTY_NOTIFY
									);
                      
  pTxCharacteristic->addDescriptor(new BLE2902());

  BLECharacteristic * pRxCharacteristic = pService->createCharacteristic(
											 CHARACTERISTIC_UUID_RX,
											BLECharacteristic::PROPERTY_WRITE
										);

  pRxCharacteristic->setCallbacks(new MyCallbacks());

  // Start the service
  pService->start();

  // Start advertising
  pServer->getAdvertising()->start();
  Serial.println("Waiting a client connection to notify...");

  // VextON();
  delay(100);

  display.init();
  display.clear();
  display.display();
  
  //display.setContrast(100, 5, 0);
  display.setBrightness(10);

  attachInterrupt(0, ISR, CHANGE);
}

void loop() {
  // put your main code here, to run repeatedly:

  // disconnecting
  if (!deviceConnected && oldDeviceConnected) {
      delay(500); // give the bluetooth stack the chance to get things ready
      pServer->startAdvertising(); // restart advertising
      Serial.println("start advertising");
      oldDeviceConnected = deviceConnected;
  }
  // connecting
  if (deviceConnected && !oldDeviceConnected) {
  // do stuff here on connecting
      oldDeviceConnected = deviceConnected;
  }
}
