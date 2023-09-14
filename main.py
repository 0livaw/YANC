import time
from ws2812b_m import Pixel
from DS1302 import DS1302
from machine import Pin
from random import randint, randrange


def calc_brightness(brightness_val):
    return int((brightness_val / 2) / 100 * 255)


def read_config():

    output_settings = []

    with open('settings.txt') as settings_file:
        file_lines = settings_file.readlines()
        for line in file_lines:
            line = line.replace('\n', '')
            output_settings.append(line)

    eff_number = output_settings[0]
    led_bright = output_settings[1]
    led_pal = output_settings[2]

    return int(eff_number), int(led_bright), int(led_pal)


def write_config(eff_number, led_bright, led_pal):
    lines = []
    params = [eff_number, led_bright, led_pal]

    for num in params:
        num = str(num) + '\n'
        lines.append(num)

    with open('settings.txt', 'w') as settings_file:
        for line in lines:
            settings_file.write(line)


# setting anode outputs for nixie tubes
anode_1 = Pin(21, Pin.OUT)
anode_2 = Pin(20, Pin.OUT)
anode_3 = Pin(19, Pin.OUT)
anode_4 = Pin(18, Pin.OUT)
anode_1.off()
anode_2.off()
anode_3.off()
anode_4.off()

# setting kathode outputs for nixie tubes
kat_0 = Pin(6, Pin.OUT)
kat_1 = Pin(8, Pin.OUT)
kat_2 = Pin(9, Pin.OUT)
kat_3 = Pin(7, Pin.OUT)


LED_EFFECT, LED_BRIGHTNESS, PALETTE = read_config()
# LED_EFFECT = 5
# LED_BRIGHTNESS = 50
# PALETTE = 2

# setting ws2812b leds
led_pin = 0
led_count = 30
strip = Pixel(led_count, led_pin, delay=0)
strip.brightness(calc_brightness(LED_BRIGHTNESS))

# setting RTC I2C bus
# CLK-GPIO2 DAT-GPIO3 RST-GPIO4
ds = DS1302(Pin(2), Pin(3), Pin(4))

# setting input buttons
BTN_select = Pin(13, Pin.IN)
BTN_down = Pin(12, Pin.IN)
BTN_up = Pin(11, Pin.IN)
BTN_store = Pin(10, Pin.IN)

# variables for storing button events
SELECT_MODE = 0
# 0 show time
# 1 hour settings
# 2 minute settings
# 3 led settings
# 4 set led brightness
# 5 set led palette

# creating color palettes for leds effects
# palettes = {0: (((192, 76, 47), (254, 180, 180),
#                  (254, 203, 63), (35, 111, 181),
#                  (120, 255, 208))),
#             1: (((119, 119, 255), (138, 233, 203),
#                  (124, 40, 126), (255, 74, 92),
#                  (130, 230, 247))),
#             2: (((255, 0, 157), (255, 0, 106),
#                  (59, 0, 255), (255, 0, 221),
#                  (0, 217, 255))),
#             3: (((255, 206, 0), (255, 86, 11),
#                  (255, 26, 130), (95, 62, 255),
#                  (34, 135, 255))),
#             4: (((0, 151, 198), (2, 186, 159),
#                  (0, 226, 172), (75, 239, 98),
#                  (155, 255, 90))),
#             5: (((45, 0, 247), (137, 0, 242),
#                  (188, 0, 221), (219, 0, 182),
#                  (242, 0, 137))),
#             6: (((0, 207, 255), (0, 255, 188),
#                  (0, 255, 121), (24, 232, 44),
#                  (157, 255, 29))),
#             7: (((31, 0, 255), (136, 0, 255),
#                  (242, 0, 255), (255, 0, 177),
#                  (255, 0, 104)))}


palettes = {0: (((0, 85, 255),
                 (105, 0, 255),
                 (0, 243, 255),
                 (0, 255, 170))),
            1: (((0, 207, 255),
                 (0, 255, 188),
                 (24, 232, 44),
                 (200, 255, 0))),
            2: (((230, 0, 255),
                 (226, 6, 141),
                 (255, 36, 0),
                 (255, 188, 10))),
            3: (((255, 0, 0),
                 (255, 25, 0),
                 (255, 50, 0))),
            4: (((255, 188, 10),
                 (255, 103, 0),
                 (99, 0, 255),
                 (205, 0, 255)))}


# (r, g, b), bright
pixels_dict = {k: [(0, 0, 0), 0] for k in range(led_count)}

# variables for led effects
RAN_PIX = randint(0, led_count - 1)
RAN_PIX_ON = randint(0, led_count - 1)
RAN_PIX_OFF = randint(0, led_count - 1)
RAN_COL = palettes[PALETTE][randint(0, len(palettes[PALETTE]) - 1)]
RAN_BR = randint(0, 255)
RAN_PIX_EFF_i = 0
RAN_PIX_EFF_j = pixels_dict[RAN_PIX_OFF][1]
RAN_PIX_EFF_DIR_FLAG = False
R_CH_ON_FLAG = False
R_CH_OFF_FLAG = False
BURST_EFF_CNT = 0


def BTN_select_pressed(pin):
    global SELECT_MODE

    SELECT_MODE += 1
    if SELECT_MODE > 5:
        SELECT_MODE = 0


def BTN_down_pressed(pin):
    global SELECT_MODE
    global cur_time
    global LED_BRIGHTNESS
    global LED_EFFECT
    global PALETTE

    # set HOURS
    if SELECT_MODE == 1:
        tmp_hour = cur_time[0]
        tmp_hour -= 1
        if tmp_hour < 1:
            tmp_hour == 23
        ds.Hour(tmp_hour)

    # set MINUTES
    elif SELECT_MODE == 2:
        tmp_minute = cur_time[1]
        tmp_minute -= 1
        if tmp_minute < 1:
            tmp_minute == 59
        ds.Minute(tmp_minute)

    # set LED EFFECT
    elif SELECT_MODE == 3:
        strip.clear()
        LED_EFFECT -= 1
        if LED_EFFECT < 0:
            LED_EFFECT = 0

    # set LED BRIGHTNESS
    elif SELECT_MODE == 4:
        LED_BRIGHTNESS -= 5
        if LED_BRIGHTNESS < 0:
            LED_BRIGHTNESS = 0
        strip.brightness(calc_brightness(LED_BRIGHTNESS))

    elif SELECT_MODE == 5:
        strip.clear()
        PALETTE -= 1
        if PALETTE < 0:
            PALETTE = 0


def BTN_up_pressed(pin):
    global SELECT_MODE
    global cur_time
    global LED_BRIGHTNESS
    global LED_EFFECT
    global PALETTE

    # set HOURS
    if SELECT_MODE == 1:
        tmp_hour = cur_time[0]
        tmp_hour += 1
        if tmp_hour > 24:
            tmp_hour == 0
        ds.Hour(tmp_hour)

    # set MINUTES
    elif SELECT_MODE == 2:
        tmp_minute = cur_time[1]
        tmp_minute += 1
        if tmp_minute > 60:
            tmp_minute == 0
        ds.Minute(tmp_minute)

    # set LED EFFECT
    elif SELECT_MODE == 3:
        strip.clear()
        LED_EFFECT += 1
        if LED_EFFECT > 3:
            LED_EFFECT = 0

    # set LED BRIGHTNESS
    elif SELECT_MODE == 4:
        LED_BRIGHTNESS += 5
        if LED_BRIGHTNESS > 95:
            LED_BRIGHTNESS = 95
        strip.brightness(calc_brightness(LED_BRIGHTNESS))

    elif SELECT_MODE == 5:
        strip.clear()
        PALETTE += 1
        if PALETTE > (len(palettes) - 1):
            PALETTE = 0


def BTN_store_pressed(pin):
    global SELECT_MODE
    global LED_EFFECT
    global LED_BRIGHTNESS
    global PALETTE

    write_config(LED_EFFECT, LED_BRIGHTNESS, PALETTE)
    wrap_digits()
    SELECT_MODE = 0


# functions for k155id1 kathode combiations
def show_0():
    kat_0.value(1)
    kat_1.value(0)
    kat_2.value(0)
    kat_3.value(1)


def show_1():
    kat_0.value(0)
    kat_1.value(0)
    kat_2.value(0)
    kat_3.value(0)


def show_2():
    kat_0.value(1)
    kat_1.value(0)
    kat_2.value(0)
    kat_3.value(0)


def show_3():
    kat_0.value(0)
    kat_1.value(1)
    kat_2.value(0)
    kat_3.value(0)


def show_4():
    kat_0.value(1)
    kat_1.value(1)
    kat_2.value(0)
    kat_3.value(0)


def show_5():
    kat_0.value(0)
    kat_1.value(0)
    kat_2.value(1)
    kat_3.value(0)


def show_6():
    kat_0.value(1)
    kat_1.value(0)
    kat_2.value(1)
    kat_3.value(0)


def show_7():
    kat_0.value(0)
    kat_1.value(1)
    kat_2.value(1)
    kat_3.value(0)


def show_8():
    kat_0.value(1)
    kat_1.value(1)
    kat_2.value(1)
    kat_3.value(0)


def show_9():
    kat_0.value(0)
    kat_1.value(0)
    kat_2.value(0)
    kat_3.value(1)


digits_func = {0: show_0,
               1: show_1,
               2: show_2,
               3: show_3,
               4: show_4,
               5: show_5,
               6: show_6,
               7: show_7,
               8: show_8,
               9: show_9}


# dynamic indication for nixie tubes
def show_digits(hour,
                minute,
                show_h=True,
                show_m=True,
                show_tmr=2000,
                anode_delay=1000):

    digits = []
    digits.append(hour // 10)
    digits.append(hour % 10)
    digits.append(minute // 10)
    digits.append(minute % 10)

    for d in digits:
        if d > 9:
            return None

    if show_h is True:
        anode_1.on()
        digits_func[digits[0]]()
        time.sleep_us(show_tmr)
        anode_1.off()

        time.sleep_us(anode_delay)

        anode_2.on()
        digits_func[digits[1]]()
        time.sleep_us(show_tmr)
        anode_2.off()

        time.sleep_us(anode_delay)

    if show_m is True:
        anode_3.on()
        digits_func[digits[2]]()
        time.sleep_us(show_tmr)
        anode_3.off()

        time.sleep_us(anode_delay)

        anode_4.on()
        digits_func[digits[3]]()
        time.sleep_us(show_tmr)
        anode_4.off()

        # time.sleep_us(anode_delay)


def wrap_digits():
    anode_1.on()
    anode_2.on()
    anode_3.on()
    anode_4.on()

    for f in digits_func:
        digits_func[f]()
        time.sleep_ms(100)

    anode_1.off()
    anode_2.off()
    anode_3.off()
    anode_4.off()


def startup_wrap_digits():

    anode_1.on()
    for f in digits_func:
        digits_func[f]()
        time.sleep_ms(50)
    anode_1.off()

    anode_2.on()
    for f in digits_func:
        digits_func[f]()
        time.sleep_ms(50)
    anode_2.off()

    anode_3.on()
    for f in digits_func:
        digits_func[f]()
        time.sleep_ms(50)
    anode_3.off()

    anode_4.on()
    for f in digits_func:
        digits_func[f]()
        time.sleep_ms(50)
    anode_4.off()
    time.sleep_ms(100)


# def get_rand_color(down_limit=0, upper_limit=255):
#     r = randint(down_limit, upper_limit)
#     g = randint(down_limit, upper_limit)
#     b = randint(down_limit, upper_limit)
#     return r, g, b


def get_rand_hue(down_limit=0, upper_limit=65536, step=1000):
    return randrange(down_limit, upper_limit, step)


# def fill_by_one(led_number, color):
#     for i in range(led_number):
#         strip.set_pixel(i, color)
#     strip.show()

def startup_hue_rainbow():
    hue = 0

    for i in range(0, 255):

        color = strip.colorHSV(hue, 255, i)
        strip.fill(color)
        strip.show()
        hue += 10


# def sec_arrow_snake_eff(second, color_HSV):
#     H, S, V = color_HSV
#     led_number = second // 2

#     if second % 2 == 0:

#         strip.set_pixel(led_number, strip.colorHSV(H, S, V))
#         strip.set_pixel(led_number - 1, strip.colorHSV(H, S, V - 50))
#         strip.set_pixel((led_number - 2), (0, 0, 0))
#     else:
#         strip.set_pixel(led_number, strip.colorHSV(H, S, V))
#         strip.set_pixel(led_number - 1, strip.colorHSV(H - 1000, S, V - 100))
#         strip.set_pixel((led_number - 2), (0, 0, 0))

#     strip.show()


def sec_arrow_snake_eff(second):

    led_number = second // 2

    if second % 2 == 0:

        strip.set_pixel(led_number, palettes[PALETTE][0])

        strip.set_pixel(
            led_number - 1,
            palettes[PALETTE][1],
            calc_brightness(LED_BRIGHTNESS - (LED_BRIGHTNESS // 2)))

        strip.set_pixel((led_number - 2), (0, 0, 0))

    else:
        strip.set_pixel(led_number, palettes[PALETTE][0])

        strip.set_pixel(
            led_number - 1,
            palettes[PALETTE][2],
            calc_brightness(LED_BRIGHTNESS - (LED_BRIGHTNESS // 3)))

        strip.set_pixel((led_number - 2), (0, 0, 0))

    strip.show()


def sec_arrow_rainbow_eff():
    global ranibow_effect_HUE

    color = strip.colorHSV(ranibow_effect_HUE, 255, 255)
    strip.fill(color)
    strip.show()

    if ranibow_effect_HUE >= 65535:
        ranibow_effect_HUE = 0
    ranibow_effect_HUE += 50


def sec_arrow_double_rainbow_eff():
    global ranibow_effect_HUE
    global ranibow_effect_HUE_double

    color_right = strip.colorHSV(ranibow_effect_HUE, 255, 255)
    color_left = strip.colorHSV(ranibow_effect_HUE_double, 255, 255)

    for i in range(0, 16):
        strip.set_pixel(i, color_right)
    for j in range(16, 30):
        strip.set_pixel(j, color_left)
    strip.show()

    ranibow_effect_HUE += 50
    if ranibow_effect_HUE >= 65500:
        ranibow_effect_HUE = 0

    ranibow_effect_HUE_double -= 100
    if ranibow_effect_HUE_double <= 0:
        ranibow_effect_HUE_double = 65500


def random_pixel_eff():
    global EFF_TICKS_MS

    if time.ticks_diff(time.ticks_ms(), EFF_TICKS_MS) > 500:

        strip.set_pixel(randint(0, led_count - 1),
                        palettes[PALETTE][randint(0,
                                                  len(palettes[PALETTE]) - 1)])

        strip.set_pixel(randint(0, led_count - 1), off_led)
        strip.show()
        EFF_TICKS_MS = time.ticks_ms()


def sin_wave_eff(color_hue, delay=30):

    for i in range(0, led_count):
        strip.set_pixel(i, strip.colorHSV(color_hue, 255, 255))
        strip.show()
        time.sleep_ms(delay)


def random_burst_eff():
    global BURST_EFF_CNT
    global PALETTE

    BURST_EFF_CNT += 1

    if BURST_EFF_CNT % 10 == 0:

        strip.clear()
        idex = randint(0, led_count - 1)
        color = palettes[PALETTE][randint(0, len(palettes[PALETTE]) - 1)]
        strip.set_pixel(idex, color)
        strip.show()
        BURST_EFF_CNT = 0

    else:
        pass


def blinking_pix_eff():
    global RAN_PIX
    global RAN_COL
    global RAN_BR
    global RAN_PIX_EFF_i
    global RAN_PIX_EFF_DIR_FLAG

    if RAN_PIX_EFF_i < RAN_BR and RAN_PIX_EFF_DIR_FLAG is False:
        strip.set_pixel(RAN_PIX, RAN_COL, RAN_PIX_EFF_i)
        strip.show()
        RAN_PIX_EFF_i += 1

    if RAN_PIX_EFF_i >= RAN_BR:
        RAN_PIX_EFF_DIR_FLAG = True

    if RAN_PIX_EFF_DIR_FLAG is True:
        strip.set_pixel(RAN_PIX, RAN_COL, RAN_PIX_EFF_i)
        strip.show()
        RAN_PIX_EFF_i -= 1

    if RAN_PIX_EFF_i <= 0:
        RAN_PIX_EFF_DIR_FLAG = False
        RAN_PIX = randint(0, led_count - 1)
        RAN_COL = palettes[PALETTE][randint(0, len(palettes[PALETTE]) - 1)]
        RAN_BR = randint(0, 255)
        strip.clear()


def random_change_eff():
    global PALETTE
    global RAN_PIX_ON
    global RAN_PIX_OFF
    global RAN_COL
    global RAN_BR
    global RAN_PIX_EFF_i
    global RAN_PIX_EFF_j
    global R_CH_ON_FLAG
    global R_CH_OFF_FLAG
    global RAN_PIX_EFF_DIR_FLAG

    if pixels_dict[RAN_PIX_ON][1] == 0 or R_CH_ON_FLAG is True:
        if R_CH_ON_FLAG is False:
            R_CH_ON_FLAG = True

        strip.set_pixel(RAN_PIX_ON,
                        RAN_COL,
                        RAN_PIX_EFF_i)
        strip.show()
        RAN_PIX_EFF_i += 1

    else:
        RAN_PIX_ON = randint(0, led_count - 1)
        RAN_BR = randint(0, 255)
        RAN_COL = palettes[2][randint(0, len(palettes[2]) - 1)]

    if RAN_PIX_EFF_i >= RAN_BR:
        R_CH_ON_FLAG = False
        RAN_PIX_EFF_i = 0
        pixels_dict[RAN_PIX_ON] = RAN_COL, RAN_BR
        RAN_PIX_ON = randint(0, led_count - 1)
        RAN_COL = palettes[PALETTE][randint(0, len(palettes[PALETTE]) - 1)]
        RAN_BR = randint(0, 255)

    if pixels_dict[RAN_PIX_OFF][1] != 0 or R_CH_OFF_FLAG is True:
        if R_CH_OFF_FLAG is False:
            R_CH_OFF_FLAG = True

        strip.set_pixel(RAN_PIX_OFF,
                        pixels_dict[RAN_PIX_OFF][0],
                        RAN_PIX_EFF_j)
        strip.show()
        RAN_PIX_EFF_j -= 1
    else:
        RAN_PIX_OFF = randint(0, led_count - 1)

    if RAN_PIX_EFF_j <= 0:
        R_CH_OFF_FLAG = False
        pixels_dict[RAN_PIX_OFF] = (0, 0, 0), 0
        RAN_PIX_OFF = randint(0, led_count - 1)
        RAN_PIX_EFF_j = pixels_dict[RAN_PIX_OFF][1]


# pin interruptions for buttons
BTN_select.irq(trigger=Pin.IRQ_RISING, handler=BTN_select_pressed)
BTN_down.irq(trigger=Pin.IRQ_RISING, handler=BTN_down_pressed)
BTN_up.irq(trigger=Pin.IRQ_RISING, handler=BTN_up_pressed)
BTN_store.irq(trigger=Pin.IRQ_RISING, handler=BTN_store_pressed)


TIME_TICKS_MS = time.ticks_ms()
EFF_TICKS_MS = time.ticks_ms()
BLINK_TICKS_MS = time.ticks_ms()


orange_color_HSV = (728, 236, 255)
off_led = (0, 0, 0)
ranibow_effect_HUE = 0
ranibow_effect_HUE_double = 65500

ds.Second(0)

cur_time = ds.Hour(), ds.Minute(), ds.Second()
# startup_hue_rainbow()

for i in range(0, 3):
    sin_wave_eff(get_rand_hue(), 30)

strip.clear()
strip.show()

startup_wrap_digits()

while True:

    # updating time
    if time.ticks_diff(time.ticks_ms(), TIME_TICKS_MS) >= 499:
        cur_time = ds.Hour(), ds.Minute(), ds.Second()
        TIME_TICKS_MS = time.ticks_ms()

    # show time
    if SELECT_MODE == 0:
        show_digits(cur_time[0],
                    cur_time[1])

    else:
        blink_diff = time.ticks_diff(time.ticks_ms(), BLINK_TICKS_MS)

        if blink_diff in range(250, 500):

            # hours change
            if SELECT_MODE == 1:
                show_digits(cur_time[0],
                            cur_time[1],
                            show_m=False)
                strip.clear()
                strip.show()

            # minutes change
            elif SELECT_MODE == 2:
                show_digits(cur_time[0],
                            cur_time[1],
                            show_h=False)
                strip.clear()
                strip.show()

            # change led effect
            elif SELECT_MODE == 3:
                show_digits(SELECT_MODE,
                            LED_EFFECT)

            # change led brightness
            elif SELECT_MODE == 4:
                show_digits(SELECT_MODE,
                            LED_BRIGHTNESS)

            # change led pallete
            elif SELECT_MODE == 5:
                show_digits(SELECT_MODE,
                            PALETTE)

        if blink_diff > 500:
            BLINK_TICKS_MS = time.ticks_ms()

    # change led
    if SELECT_MODE not in range(1, 3):

        if LED_EFFECT == 0:
            sec_arrow_rainbow_eff()

        elif LED_EFFECT == 1:
            sec_arrow_snake_eff(cur_time[2])

        # elif LED_EFFECT == 2:
        #     random_pixel_eff()

        elif LED_EFFECT == 2:
            blinking_pix_eff()

        elif LED_EFFECT == 3:
            random_change_eff()

        # elif LED_EFFECT == 5:
        #     random_burst_eff()

    if cur_time[2] == 0 and SELECT_MODE == 0:
        wrap_digits()
