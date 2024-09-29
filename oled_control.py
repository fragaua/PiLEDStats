# Author: Fraga

from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import time
import re

import subprocess # To run commands and fetch os information



#from PIInfoPage import PIInfoPage
from PIInfo import PIInfo
font_small = ImageFont.load_default(size=9)

font_big = ImageFont.load_default(size=12)

def setup_oled():
    # Create the I2C interface.
    i2c = busio.I2C(SCL, SDA)
    display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)

    image = Image.new("1", (display.width, display.height))

    display.fill(0)
    display.show()

    draw = ImageDraw.Draw(image)

    return display, image, draw

previous_tx_kbytes = 0
previous_rx_kbytes = 0
ITERATION_TIME = 1

# Get drawing object to draw on image.

def fetch_command_data(cmd):
    return subprocess.check_output(cmd, shell=True).decode("utf-8")

def parse_ip(unparsed_data: str):
    ip = unparsed_data.split(" ")
    return {"ip": ip[0]}


def parse_uptime(unparsed_data: str):
    load = unparsed_data.split(",")
    return load[0][load[0].find("up")+3:].strip()

def parse_cpuload(unparsed_data: str):
    load = unparsed_data[unparsed_data.find("average:")+9:].replace("\n", "").split(",")
    return str(float(load[0]) * 100)



def parse_temperature(unparsed_data: str):
    temperature = unparsed_data.replace("\n", "").split("=")
    return temperature[1]

def parse_tcp_connections(unparsed_data: str):
    # Define private IP ranges to exclude local connections
    private_ip_patterns = [
        re.compile(r"^127\."),
        re.compile(r"^10\."),
        re.compile(r"^192\.168\."),
    ]

    # Create a list to hold parsed dictionaries
    parsed_connections = []

    # Iterate through each line of the netstat output
    for line in unparsed_data.splitlines():
        if "ESTABLISHED" in line:  # We only want established connections
            # Use regex to capture the fields: proto, recv-Q, send-Q, local address, foreign address, PID/program
            match = re.match(
                r"^\S+\s+(\d+)\s+(\d+)\s+(\S+):\S+\s+(\S+):\S+\s+\S+\s+(\d+)/(\S+)",
                line
            )
            if match:
                recv_q = match.group(1)  # Received queue
                send_q = match.group(2)  # Send queue
                local_address = match.group(3)  # Local address (IP only)
                foreign_address = match.group(4)  # Foreign address (IP only)
                pid = match.group(5)  # PID
                program = match.group(6)  # Program name

                # Skip local connections (127.0.0.1)
                if local_address.startswith("127."):
                    continue

                # Determine if the foreign address is external (i.e., not in private IP ranges)
                external_flag = not any(pattern.match(foreign_address) for pattern in private_ip_patterns)

                # Create the parsed connection dictionary
                connection_info = {
                    "local address": local_address,
                    "foreign address": foreign_address,
                    "received": recv_q,
                    "sent": send_q,
                    "program": program,
                    "external_flag": external_flag
                }

                # Append this connection's information to the list
                parsed_connections.append(connection_info)
    print(parsed_connections)
    return parsed_connections



def parse_eth_interface(unparsed_data: str) -> str:
    global previous_tx_kbytes, previous_rx_kbytes, ITERATION_TIME ## Ugly solution for now
    
    throughput = {"total_rx": 0, "total_tx": 0, "current_rx": 0, "current_tx": 0}
    info = unparsed_data.split("\n")
    try:
        throughput["total_rx"]  = int(int(list(filter(None, info[3].split(" ")))[0]) / 1000)
        throughput["total_tx"]  = int(int(list(filter(None, info[5].split(" ")))[0]) / 1000)

        throughput["current_rx"] = round((throughput["total_rx"] - previous_rx_kbytes) / ITERATION_TIME)
        throughput["current_tx"] = round((throughput["total_tx"] - previous_tx_kbytes) / ITERATION_TIME)
        
    except IndexError: ## Again, accesses might fail. This isn't pretty but it's good enough for now
        pass
    


    ## Update previous
    previous_rx_kbytes = throughput["total_rx"]
    previous_tx_kbytes = throughput["total_tx"]

    return throughput






if __name__ == "__main__":

    display, image, draw = setup_oled()

    pi_info_list = [{"cmd": "hostname -I", "parse_function": parse_ip, "format_string": "IP: {}"},
                    #PIInfo("Temp", "vcgencmd measure_temp", parse_temperature),
                    #PIInfo("Up", "top -bn1 | grep load", parse_uptime),
                    #PIInfo("Cpu Load", "top -bn1 | grep load", parse_cpuload, "CPU: {}%"),
                    ##PIInfo("TCP", "sudo netstat -npe | grep ESTABLISHED", parse_tcp_connections, "{}"),
                    {"cmd" : "ip -s  link show dev eth0", "parse_function": parse_eth_interface, "format_string" : "totalrx: {}\ntotal_tx: {}\ncurrent_rx: {}\ncurrent_tx: {}"},
                   ]
    pi_info_tcp_connections = {"cmd" : "sudo netstat -np", "parse_function": parse_tcp_connections}

    toggle = True
    cnt = 5
    while True:
        draw.rectangle((0, 0, display.width, display.height), outline=0, fill=0)
        
        if toggle:
            for info in pi_info_list:
                unparsed_data = fetch_command_data(info["cmd"])
                data = info["parse_function"](unparsed_data)
                final_info = info["format_string"].format(*data.values())
            draw.text((0,0), final_info, fill=255, font=font_small)

        
        else:

            margin = 5
            x = margin
            y = margin
            tcp_connections_unparsed = fetch_command_data(pi_info_tcp_connections["cmd"])
            tcp_connections = pi_info_tcp_connections["parse_function"](tcp_connections_unparsed)
            sorted_connections = sorted(tcp_connections, key=lambda x: not x['external_flag'])
            for conn in sorted_connections:
                connection_text  = f"{conn['local address']}->: {conn['foreign address']} | "
                connection_text2 = f"{conn['program']} | Rx: {conn['received']} Tx: {conn['sent']}"

                # Draw the text line
    
                draw.text((x, y), connection_text, fill=255, font=font_small)

                y += font_small.size  # Move down for the next connection
                draw.text((x, y), connection_text2, fill=255, font=font_small)
                y += font_small.size  # Move down for the next connection


                # Check if we run out of space, break if we exceed the display height
                if y + margin >= display.height:
                    break

        cnt +=1


        if cnt == 10:
            cnt = 0
            toggle = not toggle     
            print("toggled")


    
        # Display image
        display.image(image)
        display.show()
        time.sleep(ITERATION_TIME)
        
