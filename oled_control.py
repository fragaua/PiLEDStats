# Author: Fraga

from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import time



from PIInfoPage import PIInfoPage
from PIInfo import PIInfo


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
ITERATION_TIME = 60

# Get drawing object to draw on image.

def parse_ip(unparsed_data: str):
    ip = unparsed_data.split(" ")
    return ip[0]


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
    ## Indices are defined like this since I don't really need all the data coming from the command.
    tcp_connections = []
    local_address_idx = 3
    foreign_address_idx = 4
    pid_program_idx = 8
    print(unparsed_data)
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
            #tcp_connection = {"ip": local_address, "dest": foreign_address, "prog": program}
            tcp_connection = "{}  {}  {}".format(local_address, foreign_address, program)
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

    display, image, draw = setup_oled()

    pi_info_list = [PIInfo("IPv4", "hostname -I", parse_ip, "IP: {}"),
                    PIInfo("Temp", "vcgencmd measure_temp", parse_temperature),
                    PIInfo("Up", "top -bn1 | grep load", parse_uptime),
                    PIInfo("Cpu Load", "top -bn1 | grep load", parse_cpuload, "CPU: {}%"),
                    #PIInfo("TCP", "sudo netstat -npe | grep ESTABLISHED", parse_tcp_connections, "{}\n"),
                    #PIInfo("end0", "ip -s  link show dev eth0", parse_eth_interface, lambda d: "rx: {}kb/s tx: {}kb/s".format(d["current_rx"], d["current_tx"])),
                   ]
    
    oled = PIInfoPage(pi_info_list, draw, (display.width, display.height), (3,2))

    while True:
        oled.draw()

        display.image(image)
        display.show()
        
        time.sleep(ITERATION_TIME)
