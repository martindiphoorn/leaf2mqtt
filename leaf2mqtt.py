import os
import pycarwings2
import paho.mqtt.client as mqtt
import schedule
import time

leaf_username = os.environ['LEAF_USERNAME']
leaf_password = os.environ['LEAF_PASSWORD']
leaf_region = os.environ['LEAF_REGION']
leaf_polling = os.environ['LEAF_POLLING']

mqtt_username = os.environ['MQTT_USERNAME']
mqtt_password = os.environ['MQTT_PASSWORD']
mqtt_host = os.environ['MQTT_HOST']
mqtt_port = os.environ['MQTT_PORT']
mqtt_topic = os.environ['MQTT_TOPIC']

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(mqtt_topic + "/command/#")
    client.publish(mqtt_topic + "/log", 'connected')

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

def send_value(client, key, value):
    topic = mqtt_topic + '/status/' + key
    client.publish(topic, value)
    print('send: topic=' + topic + ' value=' + str(value))

def retrieve_data(client, s):
    print("get_latest_battery_status from servers")
    leaf = s.get_leaf()
    leaf_info = leaf.get_latest_battery_status()
    send_value(client, 'battery_percentage', leaf_info.battery_percent)
    send_value(client, 'is_charging', leaf_info.is_charging)
    send_value(client, 'charging_status', leaf_info.charging_status)
    send_value(client, 'battery_capacity', leaf_info.battery_capacity)
    send_value(client, 'battery_remaining_amount', leaf_info.battery_remaining_amount)


print('Setting up MQTT to server: ' + mqtt_username + '@' + mqtt_host + ':' + mqtt_port)
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.username_pw_set(mqtt_username, mqtt_password)
client.connect(mqtt_host, int(mqtt_port), 60)

print("Prepare Session")
s = pycarwings2.Session(leaf_username, leaf_password, leaf_region)

# Poll first time
retrieve_data(client, s)

schedule.every(int(leaf_polling)).minutes.do(lambda: retrieve_data(client, s))

while True:
    schedule.run_pending()
    client.loop()
    time.sleep(500)