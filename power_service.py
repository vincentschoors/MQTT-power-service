import paho.mqtt.client as mqtt
from wakeonlan import send_magic_packet
import os
import sys
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Setup logging to file
log_file_path = "/app/logs/wol_service.log"
logging.basicConfig(filename=log_file_path, 
                    level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Logging to stdout for real-time Docker logging
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(console_handler)

logging.info("load_dotenv")

# MQTT Settings from environment variables
MQTT_BROKER = os.getenv("MQTT_BROKER", "mqtt-broker")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TARGET_TOPIC = os.getenv("MQTT_TARGET_TOPIC")
MQTT_SERVICE_STATUS_TOPIC = os.getenv("MQTT_SERVICE_STATUS_TOPIC")
MQTT_SHUTDOWN_TOPIC= os.getenv("MQTT_SHUTDOWN_TOPIC")
MQTT_USERNAME = os.getenv("MQTT_USERNAME")
MQTT_PASSWORD = os.getenv("MQTT_PASSWORD")
logging.info("Environment variables loaded")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
logging.info("MQTT client initialization")


def on_subscribe(client, userdata, mid, reason_code_list, properties):
    if reason_code_list[0].is_failure:
        logging.error(f"Broker rejected subscription: {reason_code_list[0]}")
    else:
        logging.info(f"Broker granted the following QoS: {reason_code_list[0].value}")

def on_unsubscribe(client, userdata, mid, reason_code_list, properties):
    if len(reason_code_list) == 0 or not reason_code_list[0].is_failure:
        logging.info("Unsubscribe succeeded")
    else:
        logging.error(f"Broker replied with failure: {reason_code_list[0]}")
    client.disconnect()

# Callback function for when a message is received on a subscribed topic
def on_message(client, userdata, msg):
    logging.info(f"Message received: Topic: {msg.topic}, Payload: {msg.payload.decode()}")
    command = msg.payload.decode()
    if command.startswith("ON:"):
        # Extract the MAC address from the payload
        target_mac_address = command[3:].strip()
    
        # Validate MAC address format (basic validation, can be extended if needed)
        if len(target_mac_address) == 17 and all(c in "0123456789ABCDEFabcdef:" for c in target_mac_address):
            logging.info(f"Sending Wake-on-LAN magic packet to {target_mac_address}")
            send_magic_packet(target_mac_address)
        else:
            logging.error(f"Invalid MAC address: {target_mac_address}")
            return False
    elif command == "OFF":
        client.publish(MQTT_SHUTDOWN_TOPIC, "shutdown", qos=1)

def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        logging.info("Connected to MQTT Broker!")
        client.subscribe(MQTT_TARGET_TOPIC)
    else:
        logging.error(f"Failed to connect, return code {rc}")

def setup_mqtt_client():
    try:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        client.will_set(f"{MQTT_SERVICE_STATUS_TOPIC}", "Wol service offline", retain=True)
        client.on_connect = on_connect
        client.on_subscribe = on_subscribe
        client.on_unsubscribe = on_unsubscribe
        client.on_message = on_message
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        logging.info("MQTT client setup complete")
    except Exception as e:
        logging.error(f"Failed to setup MQTT client: {e}")
        raise

def main():
    setup_mqtt_client()
    # Start the MQTT client loop to process incoming messages
    client.loop_forever()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"An error occurred: {e}")
