import array
import time
from machine import Pin
import rp2


@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW,
             out_shiftdir=rp2.PIO.SHIFT_LEFT,
             autopull=True, pull_thresh=24)
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()


class Pixel:
    def __init__(self, num_leds, pin, mode="RGB", delay=1):
        self.pixels = array.array("I", [0 for _ in range(num_leds)])

        self.sm = rp2.StateMachine(
            0,
            ws2812,
            freq=8_000_000,
            sideset_base=Pin(pin))

        self.sm.active(1)
        self.num_leds = num_leds
        self.delay = delay
        self.brightnessvalue = 255

    def brightness(self, brightness=None):
        if brightness is None:
            return self.brightnessvalue
        else:
            if brightness < 1:
                brightness = 1
        if brightness > 255:
            brightness = 255
        self.brightnessvalue = brightness

    def set_pixel_line_gradient(self, pixel1, pixel2,
                                left_rgb, right_rgb,
                                how_bright=None):
        if pixel2 - pixel1 == 0:
            return
        right_pixel = max(pixel1, pixel2)
        left_pixel = min(pixel1, pixel2)

        for i in range(right_pixel - left_pixel + 1):
            fraction = i / (right_pixel - left_pixel)
            r = round((right_rgb[0] - left_rgb[0]) * fraction + left_rgb[0])
            g = round((right_rgb[1] - left_rgb[1]) * fraction + left_rgb[1])
            b = round((right_rgb[2] - left_rgb[2]) * fraction + left_rgb[2])
            self.set_pixel(left_pixel + i, (r, g, b), how_bright)

    def set_pixel_line(self, pixel1, pixel2, rgb, how_bright=None):
        for i in range(pixel1, pixel2 + 1):
            self.set_pixel(i, rgb, how_bright)

    def set_pixel(self, i, color, how_bright=None):
        if how_bright is None:
            how_bright = self.brightness()
        how_bright = how_bright / 255
        red = int(color[0] * how_bright)
        green = int(color[1] * how_bright)
        blue = int(color[2] * how_bright)

        self.pixels[i] = (green << 16) + (red << 8) + blue

    def rotate_left(self, num_of_pixels):
        if num_of_pixels is None:
            num_of_pixels = 1
        self.pixels = self.pixels[num_of_pixels:] + self.pixels[:num_of_pixels]

    def rotate_right(self, num_of_pixels):
        if num_of_pixels is None:
            num_of_pixels = 1
        num_of_pixels = -1 * num_of_pixels
        self.pixels = self.pixels[num_of_pixels:] + self.pixels[:num_of_pixels]

    def show(self):
        for i in range(self.num_leds):
            self.sm.put(self.pixels[i], 8)
        time.sleep_ms(self.delay)

    def fill(self, rgb, how_bright=None):
        for i in range(self.num_leds):
            self.set_pixel(i, rgb, how_bright)

    def clear(self):
        self.pixels = array.array("I", [0 for _ in range(self.num_leds)])

    def colorHSV(self, hue, sat, val):
        if hue >= 65536:
            hue %= 65536

        hue = (hue * 1530 + 32768) // 65536
        if hue < 510:
            b = 0
            if hue < 255:
                r = 255
                g = hue
            else:
                r = 510 - hue
                g = 255
        elif hue < 1020:
            r = 0
            if hue < 765:
                g = 255
                b = hue - 510
            else:
                g = 1020 - hue
                b = 255
        elif hue < 1530:
            g = 0
            if hue < 1275:
                r = hue - 1020
                b = 255
            else:
                r = 255
                b = 1530 - hue
        else:
            r = 255
            g = 0
            b = 0

        v1 = 1 + val
        s1 = 1 + sat
        s2 = 255 - sat

        r = ((((r * s1) >> 8) + s2) * v1) >> 8
        g = ((((g * s1) >> 8) + s2) * v1) >> 8
        b = ((((b * s1) >> 8) + s2) * v1) >> 8

        return r, g, b
