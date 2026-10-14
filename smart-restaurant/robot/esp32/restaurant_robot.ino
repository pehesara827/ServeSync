// Restaurant delivery robot: subscribes to kitchen COMPLETED orders via MQTT.
// Topic (must match backend exactly): restaurant/robot/command
// Payload: {"action":"NAVIGATE_TO_TABLE","tableNumber":<int>}
// Broker: 10.66.49.162:1883 (TCP). Requires PubSubClient + ArduinoJson.
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ---- Configure these for your network ----
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* MQTT_HOST = "10.66.49.162";
const uint16_t MQTT_PORT = 1883;
const char* MQTT_TOPIC = "restaurant/robot/command";
const char* CLIENT_ID = "restaurant-robot-01";

WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);

void handleNavigateToTable(int tableNumber) {
  // TODO: replace with your motor / navigation routine.
  Serial.print("NAVIGATE_TO_TABLE table=");
  Serial.println(tableNumber);
}

void onMqttMessage(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message on [");
  Serial.print(topic);
  Serial.print("]: ");
  Serial.write(payload, length);
  Serial.println();

  if (strcmp(topic, MQTT_TOPIC) != 0) return;

  StaticJsonDocument<256> doc;
  DeserializationError err = deserializeJson(doc, payload, length);
  if (err) {
    Serial.print("JSON parse failed: ");
    Serial.println(err.c_str());
    return;
  }
  const char* action = doc["action"] | "";
  if (strcmp(action, "NAVIGATE_TO_TABLE") != 0) {
    Serial.print("Ignored action: ");
    Serial.println(action);
    return;
  }
  if (!doc.containsKey("tableNumber") || !doc["tableNumber"].is<int>()) {
    Serial.println("Missing/invalid tableNumber");
    return;
  }
  int tableNumber = doc["tableNumber"].as<int>();
  if (tableNumber <= 0) {
    Serial.println("Invalid tableNumber (must be > 0)");
    return;
  }
  handleNavigateToTable(tableNumber);
}

void ensureMqttConnected() {
  while (!mqtt.connected()) {
    Serial.print("Connecting MQTT to ");
    Serial.print(MQTT_HOST);
    Serial.print(":");
    Serial.println(MQTT_PORT);
    if (mqtt.connect(CLIENT_ID)) {
      Serial.println("MQTT connected, subscribing...");
      mqtt.subscribe(MQTT_TOPIC, 1);
    } else {
      Serial.print("MQTT failed rc=");
      Serial.print(mqtt.state());
      Serial.println(" retry in 3s");
      delay(3000);
    }
  }
}

void setup() {
  Serial.begin(115200);
  delay(500);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println();
  Serial.print("WiFi IP: ");
  Serial.println(WiFi.localIP());

  mqtt.setServer(MQTT_HOST, MQTT_PORT);
  mqtt.setCallback(onMqttMessage);
  mqtt.setBufferSize(512);
  ensureMqttConnected();
}

void loop() {
  if (!mqtt.connected()) ensureMqttConnected();
  mqtt.loop();
}
