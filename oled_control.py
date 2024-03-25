# Author: Fraga

from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import time
from typing import Callable

import subprocess # To run commands and fetch os information

# Create the I2C interface.
i2c = busio.I2C(SCL, SDA)
display = adafruit_ssd1306.SSD1306_I2C(128, 64, i2c, addr=0x3C)
width = display.width
height = display.height
image = Image.new("1", (width, height))
display.fill(0)
display.show()

previous_tx_kbytes = 0
previous_rx_kbytes = 0
ITERATION_TIME = 5

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8)
font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 6)



def parse_ip(unparsed_data: str) -> str:
    ip = unparsed_data.split(" ")
    return ip[0]


def parse_uptime(unparsed_data: str) -> str:
    load = unparsed_data.split(",")
    return load[0][load[0].find("up")+3:]


def parse_temperature(unparsed_data: str) -> str:
    temperature = unparsed_data.split("=")
    return temperature[1]

def parse_tcp_connections(unparsed_data: str) -> str:
    ## Indices are defined like this since I don't really need all the data coming from the command.
    local_address_idx = 3
    foreign_address_idx = 4
    pid_program_idx = 8

    s = ""
    lines = unparsed_data.split("\n")
    for l in lines:
        info = list(filter(None, l.split(" "))) # Filter removes all empty spaces created by the original split
        try:
            local_address = info[local_address_idx]
            foreign_address = info[foreign_address_idx]
            program = info[pid_program_idx].split("/")[1] # The second element of the split is the program. (pid/program_name)
        except IndexError: ## Some access might have gone wrong into the arrays. This solution isn't pretty but I can't bother taking care of all cases for now
            pass
        ## For now, Ignore local 127.0.0.1 stuff
        if '127.0.0.1' not in local_address and '127.0.0.1' not in foreign_address:
            s += local_address + "\n" + foreign_address + " -> " + program + "\n\n" 
        
    
    return s if len(s) > 0 else "No TCP Connections"

def parse_eth_interface(unparsed_data: str) -> str:
    global previous_tx_kbytes, previous_rx_kbytes, ITERATION_TIME ## Ugly solution for now

    info = unparsed_data.split("\n")
    rx_kbytes = 0
    tx_kbytes = 0
    try:
        rx_kbytes = int(list(filter(None, info[3].split(" ")))[0]) / 1000
        tx_kbytes  = int(list(filter(None, info[5].split(" ")))[0]) / 1000
    except IndexError: ## Again, accesses might fail. This isn't pretty but it's good enough for now
        pass
    
    rx_kbytes_second = (rx_kbytes - previous_rx_kbytes) / ITERATION_TIME
    tx_kbytes_second = (tx_kbytes - previous_tx_kbytes) / ITERATION_TIME

    ## Update previous
    previous_rx_kbytes = rx_kbytes
    previous_tx_kbytes = tx_kbytes
    return "Total: \nTx: {} KB\nRx: {} KB\nTx: {} KB/sec\nRx: {} KB/sec".format(round(tx_kbytes), round(rx_kbytes), round(tx_kbytes_second), round(rx_kbytes_second))

class PIInfo:

    def __init__(self, name: str, cmd: str, parse_function: Callable[[str], str]=None):
        self.bash_cmd = cmd
        self.info_name = name
        self.parse_function = parse_function

        self.info = None
        self.unparsed_info = None


    def fetch(self) -> str:
        self.unparsed_info = subprocess.check_output(self.bash_cmd, shell=True).decode("utf-8")
        self.info = self.parse(self.unparsed_info)

        return str(self.info_name) + ": " + str(self.info)
    
    def parse(self, unparsed_info: str) -> str:
        return self.parse_function(unparsed_info)
    





if __name__ == "__main__":
    pi_info_list = [PIInfo("IPv4", "hostname -I", parse_ip),
                   PIInfo("Temp", "vcgencmd measure_temp", parse_temperature),
                   PIInfo("Up", "top -bn1 | grep load", parse_uptime),
                   PIInfo("TCP", "sudo netstat -npe | grep ESTABLISHED", parse_tcp_connections),
                   PIInfo("end0", "ip -s  link show dev end0", parse_eth_interface)]
    
    
    screen = 0
    total_screens = 3
    while True:
        
        # Clear current screen
        draw.rectangle((0, 0, display.width, display.height * 2), outline=0, fill=0)
        #for pi_info in pi_info_list:
        #    pi_info.fetch()
            # Drawing could also take place here if we wanted to draw everything line by line, for example. TODO: Come up with a solution to fill all space automatically

        # For now, simply proceed with hardcoded drawing
        if screen == 0:
            draw.text((0, 1),  pi_info_list[0].fetch(), font=font, fill=255)
            draw.text((0, 11), pi_info_list[1].fetch(), font=font, fill=255)
            draw.text((0, 22), pi_info_list[2].fetch(), font=font, fill=255)
        elif screen == 1:
            draw.text((0, 1), pi_info_list[3].fetch(), font=font, fill=255)
        elif screen == 2:
            draw.text((0, 1), pi_info_list[4].fetch(), font=font, fill=255)

        display.image(image)
        display.show()
        
        screen = (screen + 1) % total_screens ## Roll screen
        time.sleep(ITERATION_TIME)
