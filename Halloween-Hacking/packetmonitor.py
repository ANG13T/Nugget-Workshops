import gc
import time
import board
import digitalio
import supervisor
import random
import wifi
import espidf
import ipaddress
import socketpool
import ssl
import neopixel
from board import SCL, SDA
import busio
import displayio
import adafruit_framebuf
import adafruit_displayio_sh1106

displayio.release_displays()

WIDTH = 130 # Change these to the right size for your display!
HEIGHT = 64
BORDER = 1

i2c = busio.I2C(SCL, SDA) # Create the I2C interface.
display_bus = displayio.I2CDisplay(i2c, device_address=0x3c)
display = adafruit_displayio_sh1106.SH1106(display_bus, width=WIDTH, height=HEIGHT) # Create the SH1106 OLED class.

pixel_pin = board.IO12    # Specify the pin that the neopixel is connected to (GPIO 12)
num_pixels = 1  # Set number of neopixels
pixel = neopixel.NeoPixel(pixel_pin, num_pixels, brightness=0.6)   # Create neopixel and set brightness to 30%

def SetAll(color):   # Define function with one input (color we want to set)
    for i in range(0, num_pixels):   # Addressing all 11 neopixels in a loop
        pixel[i] = (color)   # Set all neopixels a color

def NugEyes(IMAGE):
    bitmap = displayio.OnDiskBitmap(IMAGE) # Setup the file as the bitmap data source
    tile_grid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader) # Create a TileGrid to hold the bitmap
    group = displayio.Group() # Create a Group to hold the TileGrid
    group.append(tile_grid) # Add the TileGrid to the Group
    display.show(group) # Add the Group to the Display

def DeauthCheck(newPacket):    
    if subt_names[fd["subt"]] == "Deauthentication":
        NugEyes("/faces/spooky-nugg-inv.bmp")
        SetAll([159, 43, 104])
    else:
        NugEyes("/faces/jack-o-nugg-left-inv.bmp")
        SetAll([255,127,0])

PARSE_HEADER = True
PARSE_BODY = True  # if True, PARSE_HEADER must be True
PARSE_IES = False  # if True, PARSE_BODY must be True

type_names = ("mgmt", "ctrl", "data", "extn")

subt_names = ("Association Req.", "Association Resp.", "ReAssociation Req.", "ReAssociation Resp.",
              "Probe Request", "Probe Request", "Timing", "Reserved",
              "Beacon Frame", "ATIM", "Dissassociation", "Auth",
              "Deauthentication", "Action", "ActionN", "ReservedF",)

fixed = (4,6,10,6,
         0,12,0,0,
         12,0,2,6,
         2,0,0,0,)

ie_names = {0: "0_SSID",
            1: "1_Rates",
            2: "2_FH",
            3: "3_DS",
            4: "4_CF",
            5: "5_TIM",
            6: "6_IBSS",
            7: "7_Country",
            8: "8_HopParam",
            9: "9_HopTable",
            10: "10_Req",
            16: "16_Challenge",
            32: "32_PowConst",
            33: "33_PowCapab",
            34: "34_TPCReq",
            35: "35_TPCRep",
            36: "36_Chans",
            37: "37_ChSwitch",
            38: "38_MeasReq",
            39: "39_MeasRep",
            40: "40_Quiet",
            41: "41_IBSSDFS",
            42: "42_ERP",
            48: "48_Robust",
            50: "50_XRates",
            221: "221_WPA",}

def check_type(mac):
    # determine MAC type
    mactype = ""
    try:
        # mac_int = int('0x' + mac[1], base=16)  # not supported in CP
        mac_int = int("".join(("0x", mac[0:2])))
        if (mac_int & 0b0011) == 0b0011:    # 3,7,B,F LOCAL MULTICAST
            mactype = "L_M"
        elif (mac_int & 0b0010) == 0b0010:  # 2,3,6,7,A,B,E,F LOCAL
            mactype = "LOC"
        elif (mac_int & 0b0001) == 0b0001:  # 1,3,5,7,9,B,D,F MULTICAST
            mactype = "MUL"
        else:  # 0,4,8,C VENDOR (or unassigned)
            mactype = "VEN"
    except (ValueError, IndexError) as e:
        pass
    return mactype

def parse_header(fd, buf):
    fd["type"]     = (buf[0] & 0b00001100) >> 2
    fd["typename"] = type_names[fd["type"]]
    fd["subt"]     = (buf[0] & 0b11110000) >> 4
    fd["subtname"] = subt_names[fd["subt"]]
    fd["fc0"]       = buf[0]
    fd["fc1"]       = buf[1]
    fd["dur"]      = (buf[3] << 8) + buf[2]
    fd["a1"]   = ":".join("%02X" % _ for _ in buf[4:10])
    fd["a2"]   = ":".join("%02X" % _ for _ in buf[10:16])
    fd["a3"]   = ":".join("%02X" % _ for _ in buf[16:22])
    fd["a1_type"]  = check_type(fd["a1"])
    fd["a2_type"]  = check_type(fd["a2"])
    fd["a3_type"]  = check_type(fd["a3"])
    fd["seq"]      = ((buf[22] & 0b00001111) << 8) + buf[23]
    fd["frag"]     = (buf[22] & 0b11110000) >> 4
    return fd

def parse_body(fd, buf):
    ies = {}
    fd["ssid"] = ""
    pos = 24 + fixed[fd["subt"]]
    while pos < fd["len"] - 1:
        try:
            ie_id  = buf[pos]
            ie_len = buf[pos + 1]
            ie_start = pos + 2
            ie_end = ie_start + ie_len

            if (ie_id == 0):
                if (ie_len > 0):
                    # if fd["subt"] in (1, 4, 5, 8):
                    ssid = ""
                    for _ in range(ie_start, ie_end):
                        ssid = ssid + chr(buf[_])
                    fd["ssid"] = ssid

            # if SSID wasn't in the first IE, too bad...
            if not PARSE_IES:
                break;

            ie_body = "".join("%02X" % _ for _ in buf[ie_start : ie_end])
            if ie_id in ie_names:
                ies[ie_names[ie_id]] = ie_body
            else:
                ies[ie_id] = ie_body
        except IndexError as e:  # 32   32      33
            print("IndexError", e, pos, ie_end, fd["len"])
        pos = ie_end
    fd["ies"] = ies
    return fd

def get_packet():
    fd = {}
    fd["qlen"] = monitor.queued()
    fd["lost"] = monitor.lost()
    received = monitor.packet()
    if received != {}:
        fd["len"] = received[wifi.Packet.LEN]
        fd["ch"] = received[wifi.Packet.CH]
        fd["rssi"] = received[wifi.Packet.RSSI]
        
        if PARSE_HEADER:
            fd = parse_header(fd, received[wifi.Packet.RAW])
        if PARSE_BODY:
            fd = parse_body(fd, received[wifi.Packet.RAW])
        print("CH:{} RSSI:{} TYPE:{} SSID:{}".format(fd["ch"],fd["rssi"],fd["subtname"],fd["ssid"]))
    return fd

print("-"*49)
print("Starting Monitor...")
monitor = wifi.Monitor()
print("-"*49)

while True:
    try:
        monitor.channel = random.randrange(1, 12)
        fd = get_packet()
        if len(fd) > 2:
            if PARSE_HEADER:
                DeauthCheck(subt_names[fd["subt"]])
    except RuntimeError as e:
        print("RuntimeError", e)
