from pymodbus.client.serial import ModbusSerialClient
import struct
import time
import paho.mqtt.client as mqtt
import json

# Configuration
PORT = 'COM5'
BAUDRATE = 9600  # Ensure this matches your Modbus device settings
SLAVE_ID = 1  # Slave ID of the Modbus device
CURRENT_R_ADDRESS = 3022  
CURRENT_S_ADDRESS = 3020
VOLTAGE_R_ADDRESS = 3028  
VOLTAGE_S_ADDRESS = 3030
ACTIVE_POWER_ADDRESS =3020
COUNT = 2  # Number of registers to read for each float32 (2 registers)

# MQTT Configuration
MQTT_BROKER = '203.194.112.238'  # Replace with your EMQX broker address
MQTT_PORT = 1883  # Default MQTT port
MQTT_TOPIC = 'testing/mgi/Afif'  # Topic to publish the float value
MQTT_USER = "das"
MQTT_PASS = "mgi2022"

# Function to convert two registers to a float32 value (little-endian)
def convert_to_float32(registers):
    if len(registers) != 2:
        raise ValueError("Exactly 2 registers are required to convert to float32.")
    
    # Combine the registers into a 32-bit integer (little-endian)
    combined = (registers[1] << 16) | registers[0]
    
    # Convert the combined 32-bit integer to a float
    return struct.unpack('<f', combined.to_bytes(4, byteorder='little'))[0]

# MQTT Setup
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
    else:
        print(f"Failed to connect to MQTT Broker, return code {rc}")

client_mqtt = mqtt.Client()
client_mqtt.on_connect = on_connect
client_mqtt.connect(MQTT_BROKER, MQTT_PORT, 60)
client_mqtt.username_pw_set(username=MQTT_USER, password=MQTT_PASS)

# Initialize Modbus RTU client
client_modbus = ModbusSerialClient(
    port=PORT,
    baudrate=BAUDRATE,
    parity='E',  # Even parity (E), or None (N)
    timeout=1,
    stopbits=1,
    bytesize=8,
)

# Connect to the Modbus device
if client_modbus.connect():
    client_mqtt.loop_start()  # Start the MQTT loop to handle communication

    while True:
        voltageRResponse = client_modbus.read_holding_registers(VOLTAGE_R_ADDRESS, count=COUNT, slave=SLAVE_ID)        
        voltageSResponse = client_modbus.read_holding_registers(VOLTAGE_S_ADDRESS, count=COUNT, slave=SLAVE_ID)
        currentRResponse = client_modbus.read_holding_registers(CURRENT_R_ADDRESS, count=COUNT, slave=CURRENT_R_ADDRESS)
        currentSResponse = client_modbus.read_holding_registers(CURRENT_S_ADDRESS, count=COUNT, slave=CURRENT_S_ADDRESS)
        

        if not voltageRResponse.isError() and not voltageSResponse.isError():
            # Convert the registers to float32 values
            try:
                voltageRValue = convert_to_float32(voltageRResponse.registers)
                voltageSValue = convert_to_float32(voltageSResponse.registers)
                currentRValue = convert_to_float32(currentRResponse.registers)
                currentSValue = convert_to_float32(currentSResponse.registers)
                print("Converted float32 voltageR:", voltageRValue)
                print("Converted float32 voltageS:", voltageSValue)
                print("Converted float32 currentR:", currentSValue)
                print("Converted float32 currentS:", currentSValue)
                # Prepare the JSON payload with both values
                data = {
                    "data_type": "float",
                    "alias_1": "voltage phase R",
                    "value_1": voltageRValue,
                    "alias_2": "voltage phase S",
                    "value_2": voltageSValue
                }

                # Convert the data to a JSON string
                json_payload = json.dumps(data)

                # Publish the JSON data to the MQTT broker
                client_mqtt.publish(MQTT_TOPIC, payload=json_payload, qos=1)
            except Exception as e:
                print("Error converting to float32:", e)
        else:
            print("Error reading registers:", voltageRResponse, voltageSResponse)

        time.sleep(1)  # Wait 1 second before the next read
else:
    print("Failed to connect to Modbus device on", PORT)

# Close the connections
client_modbus.close()
client_mqtt.loop_stop()
