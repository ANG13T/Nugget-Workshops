import board
import neopixel

from adafruit_led_animation.animation.sparklepulse import SparklePulse
from adafruit_led_animation.animation.blink import Blink
from adafruit_led_animation.animation.rainbow import Rainbow
from adafruit_led_animation.animation.rainbowchase import RainbowChase
from adafruit_led_animation.animation.rainbowcomet import RainbowComet

from adafruit_led_animation.sequence import AnimationSequence

from adafruit_led_animation.color import *

# Update to match the pin connected to your NeoPixels
pixel_pin = board.IO12
# Update to match the number of NeoPixels you have connected
pixel_num = 11

pixels = neopixel.NeoPixel(pixel_pin, pixel_num, brightness=0.5, auto_write=False)

sparkle_pulse = SparklePulse(pixels, speed=0.05, period=3, color=JADE)
rainbow = Rainbow(pixels, speed=0.1, period=2)
rainbow_chase = RainbowChase(pixels, speed=0.1, size=5, spacing=3, step=50)
rainbow_comet = RainbowComet(pixels, speed=0.1, tail_length=7, bounce=True)

animations = AnimationSequence(
    rainbow_comet, rainbow_chase,sparkle_pulse, advance_interval=5, auto_clear=True, random_order=True
)

while True:
    #rainbow_chase.animate()
    #rainbow_comet.animate()
    #sparkle_pulse.animate()
    #rainbow.animate()
    
    #String together animations
    animations.animate()

    
