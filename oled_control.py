# Author: Fraga

from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import time

from PIInfoPage import PIInfoPage
from PIInfo import PIInfo


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
ITERATION_TIME = 60

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

def parse_ip(unparsed_data: str):
    ip = unparsed_data.split(" ")
    return ip[0]


def parse_uptime(unparsed_data: str):
    load = unparsed_data.split(",")
    return load[0][load[0].find("up")+3:].strip()


def parse_temperature(unparsed_data: str):
    temperature = unparsed_data.replace("\n", "").split("=")
    return temperature[1]

def parse_tcp_connections(unparsed_data: str):
    ## Indices are defined like this since I don't really need all the data coming from the command.
    tcp_connections = []
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
            tcp_connection = {"ip": local_address, "dest": foreign_address, "prog": program}
            #s += local_address + "\n" + foreign_address + " -> " + program + "\n\n" 
        tcp_connections.append(tcp_connection)
        
    return tcp_connections


def parse_eth_interface(unparsed_data: str) -> str:
    global previous_tx_kbytes, previous_rx_kbytes, ITERATION_TIME ## Ugly solution for now
    
    throughput = {"total_rx": 0, "total_tx": 0, "current_rx": 0, "current_tx": 0}
    info = unparsed_data.split("\n")
    try:
        throughput["total_rx"] = int(list(filter(None, info[3].split(" ")))[0]) / 1000
        throughput["total_tx"]  = int(list(filter(None, info[5].split(" ")))[0]) / 1000
        
    except IndexError: ## Again, accesses might fail. This isn't pretty but it's good enough for now
        pass
    
    throughput["current_rx"] = round((throughput["total_rx"] - previous_rx_kbytes) / ITERATION_TIME)
    throughput["current_rx"] = round((throughput["total_tx"] - previous_tx_kbytes) / ITERATION_TIME)

    ## Update previous
    previous_rx_kbytes = throughput["total_rx"]
    previous_tx_kbytes = throughput["total_tx"]

    return throughput






if __name__ == "__main__":
    pi_info_list = [
        PIInfo("IPv4", "hostname -I", parse_ip, "{}"),
                   PIInfo("Temp", "vcgencmd measure_temp", parse_temperature),
                   PIInfo("Up", "top -bn1 | grep load", parse_uptime),
                   PIInfo("Up", "top -bn1 | grep load", parse_uptime),
                   PIInfo("Up", "top -bn1 | grep load", parse_uptime),
                   #PIInfo("TCP", "sudo netstat -npe | grep ESTABLISHED", parse_tcp_connections),
                   #PIInfo("end0", "ip -s  link show dev eth0", parse_eth_interface, lambda d: "rx: {}kb/s tx: {}kb/s".format(d["current_rx"], d["current_tx"])),
                   ]
    
    oled = PIInfoPage(pi_info_list, draw, (display.width, display.height), (3,2))
    
    screen = 0
    total_screens = 3
    while True:
                # Clear current screen
        #draw.rectangle((0, 0, display.width, display.height * 2), outline=0, fill=0)
        #for pi_info in pi_info_list:
        #    pi_info.fetch()
            # Drawing could also take place here if we wanted to draw everything line by line, for example. TODO: Come up with a solution to fill all space automatically

        # For now, simply proceed with hardcoded drawing
        #if screen == 0:
            #draw.text((0, 1),  pi_info_list[0].fetch(), font=font, fill=255)
        #    draw.text((0, 11), pi_info_list[1].fetch(), font=font, fill=255)
        #    draw.text((0, 22), pi_info_list[2].fetch(), font=font, fill=255)
        #elif screen == 1:
        #    draw.text((0, 1), pi_info_list[3].fetch(), font=font, fill=255)
        #elif screen == 2:
        #    draw.text((0, 1), pi_info_list[4].fetch(), font=font, fill=255)


        oled.draw()

        display.image(image)
        display.show()
        
        ##screen = (screen + 1) % total_screens ## Roll screen
        time.sleep(ITERATION_TIME)
