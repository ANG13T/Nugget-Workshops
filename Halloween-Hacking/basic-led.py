import board
import neopixel
import time

# NeoPixel pin & number of NeoPixels
pixel_pin = board.IO12
pixel_num = 11

#initialize NeoPixels
pixels = neopixel.NeoPixel(pixel_pin, pixel_num, brightness=.1)

# cycle through pixels and set to solid color
for i in range(0,pixel_num):
    pixels[i] = (0,255,0)
    time.sleep(1)
