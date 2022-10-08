import os
import pycarwings2
import paho.mqtt.client as mqtt
import schedule
import time
import logging

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

logging.info('Starting Leaf2MQTT')

mode = os.environ.get('MODE', 'normal');

leaf_username = os.environ['LEAF_USERNAME']
leaf_password = os.environ['LEAF_PASSWORD']
leaf_region = os.environ['LEAF_REGION']
leaf_polling = os.environ['LEAF_POLLING']

mqtt_username = os.environ['MQTT_USERNAME']
mqtt_password = os.environ['MQTT_PASSWORD']
mqtt_host = os.environ['MQTT_HOST']
mqtt_port = os.environ['MQTT_PORT']
mqtt_topic = os.environ['MQTT_TOPIC']
mqtt_client_id = os.environ.get('MQTT_CLIENT_ID', 'leaf2mqtt')

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    logging.info("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(mqtt_topic + "/command/#")
    client.publish(mqtt_topic + "/log", 'connected')

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    logging.info(msg.topic+" "+str(msg.payload))

def on_disconnect(client, userdata,  rc):
    logging.info("MQTT Disconnected, trying to reconnect...")
    client.connect(mqtt_host, int(mqtt_port), 60)

def send_value(client, key, value):
    topic = mqtt_topic + '/status/' + key
    if mode != 'debug':
        client.publish(topic, value)
    logging.debug('send: topic=' + topic + ' value=' + str(value))

def retrieve_data(client, s):
    logging.info("get_latest_battery_status from servers")
    leaf = s.get_leaf()
    leaf.request_update()
    leaf_info = leaf.get_latest_battery_status()
    send_value(client, 'operation_date_and_time', leaf_info.answer["BatteryStatusRecords"]["OperationDateAndTime"])
    send_value(client, 'notification_date_and_time', leaf_info.answer["BatteryStatusRecords"]["NotificationDateAndTime"])
    send_value(client, 'battery_percentage', leaf_info.battery_percent)
    send_value(client, 'is_charging', leaf_info.is_charging)
    send_value(client, 'charging_status', leaf_info.charging_status)
    send_value(client, 'battery_capacity', leaf_info.battery_capacity)
    send_value(client, 'battery_remaining_amount', leaf_info.battery_remaining_amount)

def alive(client):
    send_value(client, 'alive', 1)


logging.info('Setting up MQTT to server: ' + mqtt_username + '@' + mqtt_host + ':' + mqtt_port)
client = mqtt.Client(client_id=mqtt_client_id, clean_session=True)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.username_pw_set(mqtt_username, mqtt_password)
client.connect(mqtt_host, int(mqtt_port), 60)

logging.info("Prepare communication with the leaf")
leaf_session = pycarwings2.Session(leaf_username, leaf_password, leaf_region)

# Initialize schedules
schedule.every(int(leaf_polling)).minutes.do(lambda: retrieve_data(client, leaf_session))
schedule.every(1).minutes.do(lambda: alive(client))
schedule.run_pending()

# Fast initial retrieval
alive(client)
retrieve_data(client, leaf_session)


while True:
    schedule.run_pending()
    client.loop()
    time.sleep(1)