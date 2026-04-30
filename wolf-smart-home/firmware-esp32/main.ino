#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <DHT.h>
const char* ssid="WIFI"; const char* pass="PASS"; const char* broker="mqtt";
WiFiClient espClient; PubSubClient client(espClient); DHT dht(4,DHT22);
void reconnectWiFi(){if(WiFi.status()!=WL_CONNECTED){WiFi.begin(ssid,pass);while(WiFi.status()!=WL_CONNECTED){delay(500);}}}
void callback(char* topic, byte* payload, unsigned int length){ if(String(topic)=="home/001/light/set"){digitalWrite(2,payload[0]=='1');}}
void reconnectMQTT(){while(!client.connected()){if(client.connect("esp32-001")){client.subscribe("home/001/light/set");}else delay(1000);}}
void setup(){pinMode(2,OUTPUT);Serial.begin(115200);dht.begin();reconnectWiFi();client.setServer(broker,1883);client.setCallback(callback);} 
void loop(){reconnectWiFi();if(!client.connected())reconnectMQTT();client.loop();StaticJsonDocument<128> doc;doc["temperature"]=dht.readTemperature();doc["humidity"]=dht.readHumidity();doc["heartbeat"]=millis();char out[128];serializeJson(doc,out);client.publish("home/001/sensors",out);delay(10000);} 
