#!/usr/bin/env python3
#
# ledctrl
#
# min python version: 3.5
#
# dependencies:
#  - python-systemd
#
# © 2016 Björn Busse (see also: LICENSE)
# bbusse@baerlin.eu

import logging
import math
import os
import random
import socket
import subprocess
import signal
import sys
import termios
import time
from systemd import journal

server_ip = "127.0.0.1"
server_port = 4223
server_proto = "udp"
client_ip = "10.64.64.88"
client_port = 2342
client_proto = "udp"
# number of pixels in the x dimension
dim_x = 32
# number of pixels in the y dimension
dim_y = 8
# effect to execute
payload = "fade-colours"

# info / warning / debug
loglevel = "info"

f2c = lambda f: int(f * 255.0) & 0xff
c2f = lambda c: float(c) / 255.0
alpha = lambda c: (c >> 24) & 0xff
red = lambda c: (c >> 16) & 0xff
green = lambda c: (c >> 8) & 0xff
blue = lambda c: c & 0xff
pack = lambda a, r, g, b: (f2c(a) << 24) | (f2c(r) << 16) | (f2c(g) << 8) | f2c(b)


class server():

    def __init__(self, server_proto, server_ip, server_port, client_ip, client_port, dim_x, dim_y):
        self.ip = server_ip
        self.port = server_port
        self.client_con = udp_client(client_ip, client_port)
        self.server_proto = server_proto
        self.serve()

        sh = handle_signals()
        self.prntr = printer()

        self.matrix = matrix(self.sock, dim_x, dim_y, self.client_con, self.prntr)
        self.matrix.reset()

    def set_payload(self, payload):
        self.payload = payload

    def get_payload(self):
        return self.payload

    def serve(self):
        self.sock = socket.socket(socket.AF_INET,
                                  socket.SOCK_DGRAM)

        self.sock.bind((self.ip, self.port))
        print("Serving on", self.ip, self.port)

    def receive(self):
        data = ""

        # non-blocking (0x40)
        try:
            data, (ip, port) = self.sock.recvfrom(1024, 0x40)
        except:
            pass

        if len(data) > 0:
            self.parse_msg(data)

    def get_port():
        return self.port

    def parse_msg(self, data):
        data = str(data).strip('b\'')
        msg = "Received message:" + data
        self.prntr.printd(msg)

        if payload == "ping":
            self.prntr.printi("pong")
            exit(0)

        elif payload == "get-payload":
            self.prntr.printi("Current payload: " + self.get_payload())
            exit(0)

        self.exec_payload(data)


class matrix(server):

    reverse_even_row = True
    status = "Reverse Pixel Order"
    frame_prev = []

    _px_layout = [0, 1, 2, 3, 4,
                 9, 8, 7, 6, 5,
                 10, 11, 12, 13, 14,
                 19, 18, 17, 16, 15,
                 20, 21, 22, 23, 24]

    px_layout = [  0,   1,   2,   3,   4,   5,   6,   7,   8,   9,  10,  11,  12,  13,  14,  15,  16,  17,  18,  19,  20,  21,  22,  23 , 24,  25,  26,  27,  28,  29 , 30,  31,
                  63,  62,  61,  60,  59,  58,  57,  56,  55,  54,  53,  52,  51,  50,  49,  48  ,47 , 46,  45,  44,  43,  42,  41,  40,  39,  38,  37,  36,  35,  34,  33,  32,
                  64,  65,  66,  67,  68,  69,  70,  71,  72,  73,  74,  75,  76,  77,  78,  79,  80,  81,  82,  83,  84,  85,  86,  87,  88,  89,  90,  91,  92,  93,  94,  95,
                 127, 126, 125, 124, 123, 122, 121, 120, 119, 118, 117, 116, 115, 114, 113, 112, 111, 110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100,  99,  98,  97,  96,
                 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159,
                 191, 190, 189, 188, 187, 186, 185, 184, 183, 182, 181, 180, 179, 178, 177, 176, 175, 174, 173, 172, 171, 170, 169, 168, 167, 166, 165, 164, 163, 162, 161, 160,
                 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223,
                 255, 254, 253, 252, 251, 250, 249, 248, 247, 246, 245, 244, 243, 242, 241, 240, 239, 238, 237, 236, 235, 234, 233, 232, 231, 230, 229, 228, 227, 226, 225, 224]

    def __init__(self, sock, dim_x, dim_y, con, prntr):
        self.con = con
        self.dim_x = dim_x
        self.dim_y = dim_y
        self.npx = dim_x * dim_y
        self.prntr = prntr
        self.sock = sock

    def exec_payload(self, payload):

        self.prntr.printi("Executing payload: " + payload)

        if payload == "set-colour":
            self.set_payload(payload)
            self.set_colour()

        elif payload == "set-random-colour":
            self.set_payload(payload)
            self.set_random_colour()

        elif payload == "grow_shrink_fade":
            self.set_payload(payload)
            self.grow_shrink_fade()

        elif payload == "kitt":
            self.set_payload(payload)
            self.kitt()

        elif payload == "fade-colours":
            self.set_payload(payload)
            self.colour_fade()

        elif payload == "show-snake":
            self.set_payload(payload)
            self.show_rainbow_snake()

        elif payload == "show-rainbow":
            self.set_payload(payload)
            self.show_rainbow()

        elif payload == "set-random-pixel":
            self.set_payload(payload)
            self.set_random_pixel()

        elif payload == "show-text":
            self.set_payload(payload)
            self.show_text("ledctrl")

        elif payload == "show-clock":
            self.set_payload(payload)
            self.show_clock()

        elif payload == "play-snake":
            self.set_payload(payload)
            snake = snake_game(self.client_con, self.matrix)

    def get_px_pos(self, px):
        return self.px_layout.index(px)

    def colour_gen_hex_code(self):
        return ''.join([random.choice('0123456789ABCDEF') for x in range(6)])

    def colour_hex_to_rgb(self, hex_str):
        if hex_str.startswith('#'):
            hex_str = hex[1:]
        if hex_str.__len__() == 3:
            hex_str = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2]
        return tuple([int(hex_str[i:i + 2], 16) for i in range(0, len(hex_str), 2)])

    def colour_rgb_to_hex(self, rgb):
        return ''.join(["%0.2X" % c for c in rgb])

    def colour_hex_to_hls(self, c_hex):
        rgb = self.colour_hex_to_rgb(c_hex)
        return rgb_to_hls(rgb[0], rgb[1], rgb[2])

    def colour_fade(self, colours=[0xffFFF5C3, 0xff0BD7D5, 0xffFF7260], speed=0.001, steps=1000):

        for x in range(colours.__len__()):
            if not type(colours[x]) is int:
                c = "0xff" + colours[x]
                colours[x] = int(c, 16)

        colours = self.colour_get_gradient(colours, steps)

        while True:
            for x in range(colours.__len__()):
                self.set_colour(colours[x])
                time.sleep(speed)

            # reverse list
            colours = colours[::-1]

    def colour_get_gradient(self, colours, steps):
        colours_per_step = steps / len(colours)
        gradient = []

        for x, colour in enumerate(colours):

                r1 = c2f(red(colour))
                g1 = c2f(green(colour))
                b1 = c2f(blue(colour))

                colour2 = colours[(x + 1) % len(colours)]

                r2 = c2f(red(colour2))
                g2 = c2f(green(colour2))
                b2 = c2f(blue(colour2))

                # generate a gradient of one step from colour to colour:
                delta = 1.0 / colours_per_step
                for y in range(int(colours_per_step)):
                        t = y * delta
                        a = 1.0
                        r = (1.0 - t) * r1 + t * r2
                        g = (1.0 - t) * g1 + t * g2
                        b = (1.0 - t) * b1 + t * b2

                        c = '0x{0:x}'.format(pack(a, r, g, b))
                        gradient.append(c[4:])

        return gradient

    def reset(self, colour="794044"):
        self.set_colour(colour)

    def set_colour(self, colour="FFFFFF"):
        frame = []

        for x in range(self.npx):
            frame.append(colour)

        self.draw(frame)

    def set_random_colour(self, t_sleep=3):

        while True:
            c = self.colour_gen_hex_code()
            self.set_colour(c)
            time.sleep(t_sleep)

    def set_random_pixel(self, t_sleep=0.5):

        while True:
            frame = []

            for x in range(self.npx):
                frame.append(self.colour_gen_hex_code())

            self.draw(frame)
            time.sleep(t_sleep)
            self.reset()

    def shift(self, list, n):
        for i in range(n):
            t = list.pop()
            list.insert(0, t)

        return list

    def grow_shrink_fade(self, colours = ["ffa500", "ff4500", "8a2be2", "0000ff", "7fffd4", "228b22", "ffff00"], speed=1):
        frame = []
        pattern = []
        pattern[0] = [0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0]
        pattern[1] = [0,0,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0,1,1,1,0,0,0,0,0,0]
        pattern[2] = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
        pattern[3] = [0,0,0,0,0,0,0,1,1,1,0,0,1,1,1,0,0,1,1,1,0,0,0,0,0,0]

        while True:

            for y in range(4):
                for x in range(self.npx):
                    if pattern[y] == 0:
                        frame.append(colours[0])
                    else:
                        frame.append(c_bg)

            self.draw(frame)
            colours = self.shift(colours)
            time.sleep(speed)

    def show_rainbow(self, colours = ["ffa500", "ff4500", "8a2be2", "0000ff", "7fffd4", "228b22", "ffff00"], speed=0.5):

        ncolours = colours.__len__()

        while True:
            frame = []

            for y in range(self.dim_y):
                for x in range(self.dim_x):
                    frame.append(colours[y])

            self.draw(frame)
            colours = self.shift(colours, 1)
            time.sleep(speed)

    def show_rainbow_snake(self, colours = ["ffa500", "ff4500", "8a2be2", "0000ff", "7fffd4", "228b22", "ffff00"], c_bg="444444", speed=1):
        frame = []

        for x in range(colours.__len__()):
            frame.append(colours[x])

        if self.npx > colours.__len__():
            for x in range(colours.__len__(), self.npx):
                frame.append(c_bg)

        while True:
            self.reverse_even_row = False
            self.draw(frame)
            frame = self.shift(frame, 1)
            time.sleep(speed)

    def set_row(self, c):
        m = ""

        for x in range(self.dim_x):
            m += c

        return m

    def show_clock(self, c_h="ff0000", c_m="ff0000", c_bg="ffffff"):

        while True:
            frame = []
            t = time.strftime("%H:%M")
            t_h = int(time.strftime("%H"))
            t_m = time.strftime("%M")
            t_m1 = int(t_m[0:1])
            t_m2 = int(t_m[1:2])

            for x in range(0, self.npx):
                if x < t_h:
                    frame.append(c_h)
                else:
                    frame.append(c_bg)

            self.draw(frame)
            time.sleep(3)
            frame = []

            for x in range(0, self.npx):

                if x < 15 and x < t_m1:
                    frame.append(c_m)
                elif x > 14 and x < (t_m2 + 15):
                    frame.append(c_m)
                else:
                    frame.append(c_bg)

            self.draw(frame)
            time.sleep(5)

    def kitt(self, c_fg = ["ff4d4d", "ff1a1a", "cc0000", "ff1a1a", "ffd4d4"], c_bg="ffffff"):
        row_fg = 3
        m = ""
        i = 0
        dir = "right"

        while True:
            for x in range(self.dim_y):
                if row_fg == x + 1:
                    for y in range(self.dim_x):
                        if dir == "right":
                            if (i == self.dim_x - 1):
                                dir = "left"
                                i = i - 1
                            else:
                                i = i + 1
                        else:
                            if (i == 0):
                                dir = "right"
                                i = i + 1
                            else:
                                i = i - 1
                        m += c_fg[i]
                else:
                    m += self.set_row(c_bg)
            self.con.send(m)
            m = ""
            time.sleep(1)

    def px_get_row(self, n):
        return math.ceil((n + 1) / dim_y)

    def px_get_column(self, n):
        nrow = self.px_get_row(n)
        if nrow == 0:
            ncol = n - dim_x
        else:
            ncol = n - (dim_x * nrow) + dim_x + 1
        return ncol

    def scroll_text(self, text, speed=0.5, c_fg="ff0000", c_bg="ffffff", dir="left"):
        nframes = text.__len__() * self.npx
        start = 0
        t=[]

        for y in range(text.__len__()):
            t.append(text[y])

        for x in range(0, nframes):
            frame = []

            if dir == "left":
                z = 0
                l = t.__len__() - 5
                for y in range(l):
                    if y == z:
                        z = z + 5
                        p = t.pop(y)
                        print("Popped", y)
                        if y >= self.npx:
                            i = y - self.npx
                            print("Inserting", i, p)
                            t.insert(i, p)

                for y in range(self.npx):
                    if t[y] == "0":
                        c = c_bg
                    else:
                        c = c_fg
                    frame.append(c)

                self.draw(frame)


            if dir == "up":
                for y in range(self.npx):
                    if text[start+y]:
                        c = c_bg
                    else:
                        c = c_fg

                    frame.append(c)

                start = start + self.dim_x

            self.draw(frame)
            time.sleep(speed)

    def show_text(self, s, scroll=True, loop=True, speed=1):
        t_sleep = speed
        text = ""

        if scroll:
            for x in range(s.__len__()):
                text += str(self.font_get_char(s[x]))
            self.scroll_text(text, speed)

        else:
            if loop:
                while True:
                    for x in range(s.__len__()):
                        self.font_show_char(s[x])
                        time.sleep(t_sleep)

            for x in range(s.__len__()):
                self.font_show_char(s[x])
                time.sleep(t_sleep)

    def font_get_char(self, c, font="f5x5"):
        f5x5 = {"A" : "0010001010011100101001010",
                "B" : "1111010001111101000111110",
                "C" : "0111110000100001000001111",
                "D" : "1111010001100011000111110",
                "E" : "1111110000111111000011111",
                "F" : "1111110000111001000010000",
                "G" : "0111110000101111000101111",
                "H" : "1000110001111111000110001",
                "I" : "0010000100001000010000100",
                "J" : "0011100001000011000101110",
                "K" : "1001010100111101000110001",
                "L" : "0100001000010000100001110",
                "N" : "1100110101101011010110011",
                "T" : "1111100100001000010000100",
                "i" : "0010000000001000010000100",
                "3" : "0111000001011100000101110",
                " " : "0000000000000000000000000",
                "<" : "0001000100010000010000010",
                ":" : "0000000100000000010000000"}

        return f5x5[c]

    def font_show_char(self, c, c_fg="ff0000", c_bg="ffffff"):
        frame = []
        p = self.font_get_char(c)

        for x in range(p.__len__()):
            px = p[x]

            if px == "0":
                px = c_bg
            else:
                px = c_fg

            frame.append(px)

        self.draw(frame)

    def draw(self, frame):
        msg_lst = []
        msg = ""

        if self.reverse_even_row:
            for x in range(0, self.npx):
                msg += frame[self.px_layout.index(x)]
        else:
            for x in range(0, self.npx):
                msg += frame[x]


        self.con.send(msg)
        super().receive()
        #self.prntr.term_print(self.status)
        #self.prntr.term_draw(msg)


class printer():

    buf = ""

    def __init__(self, loglevel="info", use_journal=True):
        self.use_journal = use_journal
        self.loglevel = loglevel

    def init_canvas(dim_x, dim_y):
        self.dim_x = dim_x
        self.dim_y = dim_y

    def print(self, msg):
        print(msg)

        if self.use_journal:
            journal.send(msg)

    # info
    def printi(self, msg):
        if self.loglevel == "info" or self.loglevel == "warning" or self.loglevel == "debug":
            self.print(msg)

    # warning
    def printw(self, msg):
        if self.loglevel == "warning" or self.loglevel == "debug":
            self.print(msg)

    # debug
    def printd(self, msg):
        if self.loglevel == "debug":
            self.print(msg)

    # exception
    def printe():
        self.print(msg)

    def term_draw(self, msg):
        start = 0
        end = 6
        len = msg.__len__()
        ntoks = int(len / 6)

        self.term_clear()

        for x in range(self.dim_y):

            if x > 0:
                start = start + (self.dim_x * 6)
                end = end + (self.dim_x * 6)

            print(msg[start:end],
                  msg[start+6:end+6],
                  msg[start+12:end+12],
                  msg[start+18:end+18],
                  msg[start+24:end+24])

        print("")
        print(self.buf)
        self.buf = ""

    def term_print(self, msg):
        self.buf += msg

    def term_clear(self):
        print(chr(27) + "[2J")


class udp_client():

    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, m):
        self.socket.sendto(bytes.fromhex(m), (self.ip, self.port))

    def sendm(self, m):
        self.socket.sendto(bytes(m, "UTF-8"), (self.ip, self.port))


class kb_input():

    old_settings = None

    def __init__(self):
       self.ch_set = []
       self.old_settings = termios.tcgetattr(sys.stdin)

       new_settings = termios.tcgetattr(sys.stdin)
       new_settings[3] = new_settings[3] & ~(termios.ECHO | termios.ICANON)
       new_settings[6][termios.VMIN] = 0
       new_settings[6][termios.VTIME] = 0
       termios.tcsetattr(sys.stdin, termios.TCSADRAIN, new_settings)

    def get_key(self):
       self.ch = os.read(sys.stdin.fileno(), 3)

       if self.ch != None and len(self.ch) > 0:
           self.ch_set.append(self.ch)

       return self.ch;

    def get_key_parsed(self):
           self.ch = self.get_key()

           if self.ch  == bytes('\x1b[A', "utf-8"):
               return("up")
           elif self.ch == bytes('\x1b[B', "utf-8"):
               return("down")
           elif self.ch == bytes('\x1b[C', "utf-8"):
               return("right")
           elif self.ch == bytes('\x1b[D', "utf-8"):
               return("left")

    #@atexit.register
    def exit(self):
       if self.old_settings:
          termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


class snake_game():

    px_snake = []
    px_food = []
    px_snake_head = 0
    frame = []
    frame_prev = []

    def __init__(self, con, matrix, c_fg="ff0000", c_food="0000ff", c_bg="ffffff"):
        self.con = con
        self.matrix = matrix
        npx = self.set_start_px()
        self.c_fg = c_fg
        self.c_bg = c_bg
        self.c_food = c_food
        self.kb = kb_input()
        self.matrix.draw(self.get_frame())
        dirs = ["up", "down", "left", "right"]
        direction = random.choice(dirs)
        self.start_game(direction)

    def start_game(self, direction):

        cycles = 0

        while True:

            key = self.kb.get_key_parsed()

            if key != None and len(key) > 0:

                if key  == 'up':
                    direction = "up"
                elif key == 'down':
                    direction = "down"
                elif key == 'right':
                    direction = "right"
                elif key == 'left':
                    direction = "left"

            time.sleep(0.1)
            cycles = cycles + 1

            if cycles > 10:

                self.move(direction)
                self.matrix.draw(self.get_frame())

                if not self.px_food:
                    self.set_food()

                cycles = 0


    def set_start_px(self):
        px = random.randint(0, self.matrix.npx - 1)
        self.px_snake.append(px)
        self.px_snake_head = px
        return px

    def move(self, dir):
        px = 0
        ncol = self.matrix.px_get_column(self.px_snake_head)
        nrow = self.matrix.px_get_row(self.px_snake_head)
        if not dir:
            snake_add_px(random.randint())

        elif dir == "up":
            px = self.px_snake_head - dim_y

            if px < 0:
                px = self.px_snake_head + ((dim_x * dim_y) - dim_x)

        elif dir == "down":
            px = self.px_snake_head + dim_y

            if px > self.matrix.npx - 1:
                px = self.matrix.px_get_column(self.px_snake_head) - 1

        elif dir == "left":
            if self.matrix.px_get_column(self.px_snake_head) == 1:
                px = self.px_snake_head + dim_x - 1
            else:
                px = self.px_snake_head - 1
            if px < 0:
                px = dim_x - 1

        elif dir == "right":
            if self.matrix.px_get_column(self.px_snake_head) == dim_x:
                px = self.px_snake_head - dim_x -1
            else:
                px = self.px_snake_head + 1
            if px > self.matrix.npx:
                px = self.matrix.npx - dim_x - 1

        if px in self.px_snake:
            self.game_over()

        if not px in self.px_food:
            self.px_snake.pop(0)

        self.px_snake.append(px)
        self.px_snake_head = px

    def set_food(self):
        is_occupied = True

        while is_occupied:

            npx = random.randint(0, self.matrix.npx)

            if not npx in self.px_food:
                is_occupied = False

            if not npx in self.px_snake:
                is_occupied = False

        self.px_food.append(npx)

    def get_frame(self):
        frame = []

        for x in range(0, self.matrix.npx):
            if x in self.px_snake:
                frame.append(self.c_fg)
            elif x in self.px_food:
                frame.append(self.c_food)
            else:
                frame.append(self.c_bg)

        return frame

    def game_over(self):
        self.matrix.set_colour("FF0000")
        print("Game Over \:")
        quit()


class handle_signals:

    def __init__(self):
        self.original_sigint = signal.getsignal(signal.SIGINT)
        signal.signal(signal.SIGINT, self.shutdown)
        self.prntr = printer()

    def restore(self):
        signal.signal(signal.SIGINT, self.original_sigint)

    def shutdown(self):
        self.restore()
        self.prntr.printi("Exiting")
        sys.exit(1)


class service:

    def __init__(self, name, cmd_start):
        self.name = name
        self.cmd_start = cmd_start
        self.prntr = printer()

    def get_state(self):
        cmd = "systemctl --user show -p SubState " + self.name
        p = self.run_cmd(cmd)

        if hasattr(p, 'stdout'):
            r = p.stdout.strip('\n')
        else:
            return False

        if r == "Unit ledctrl.service could not be found.":
            return "not-found"

        return r[9:]

    def start_transient(self):
        self.start("transient")

    def start(self, type="transient"):
        prntr.printi("Starting service: " + service_name)
        cmd = 'systemd-run -t \
                           --user \
                           --unit=' + self.name + ' \
                           --description="ledctrl server" \
                           --remain-after-exit \
                           --no-block \
                           --send-sighup ' + self.cmd_start

        # for readability
        cmd = ' '.join(cmd.split())

        p = self.run_cmd(cmd)
        if p.stdout.strip('\n') == "Failed to start transient service unit: Unit ledctrl.service already exists.":
            self.stop()

    def restart(self):
        prntr.printi("Restarting service: " + service_name)
        cmd = 'systemctl --user restart ' + self.name
        p = self.run_cmd(cmd)

        if p.stdout.strip('\n') == "Failed to restart ledctrl.service: Unit ledctrl.service not found.":
            self.prntr.printi("Restart failed. Trying to start " + self.name)
            self.start()

    def stop(self):
        cmd = 'systemctl --user stop ' + self.name
        self.run_cmd(cmd)

    def reset_failed(self):
        cmd = 'systemctl --user reset-failed ' + self.name
        self.run_cmd(cmd)

    def run_cmd(self, cmd):
        self.prntr.printd("Executing: " + cmd)

        try:
            p = subprocess.run(cmd, shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               universal_newlines=True)

        except:
            e = sys.exc_info()[0]
            self.prntr.printe(e)

        if hasattr(p, 'stdout'):
            self.prntr.printd(p.stdout.strip('\n'))

        return p


def show_help():
    print("\n  Usage:")
    print("")
    print("    ledctrl help                            - show this dialog")
    print("    ledctrl fade-colours                    - fade colours")
    print("    ledctrl set-colour                      - set colour")
    print("    ledctrl show-text                       - show text")
    print("    ledctrl play-snake                      - start snake game")
    print("\n")


if __name__ == '__main__':

    log = logging.getLogger('custom_logger_name')
    log.propagate = False
    #log.addHandler(JournalHandler())
    #logging.root.addHandler(JournalHandler())
    #log.setLevel(logging.DEBUG)
    #JournalHandler(SYSLOG_IDENTIFIER='ledctrl')
    #log.warning("Some message: %s", 'detail')

    prntr = printer(loglevel)
    cmd = sys.argv[0]
    action = ""

    if sys.argv.__len__() > 1:
        if len(sys.argv[1]) > 0:
            action = sys.argv[1]

    sys.argv = []

    service_name = "ledctrl"
    cmd_start = cmd + " start"
    service = service(service_name, cmd_start)
    service_state = service.get_state()

    prntr.printi("ledctrl service state: " + service_state)

    if "help" == action:
        show_help()
        exit(0)

    if "start" == action:
        server = server(server_proto,
                        server_ip,
                        server_port,
                        client_ip,
                        client_port,
                        dim_x,
                        dim_y)

        server.matrix.exec_payload(payload)

    if service_state == "not-found":
        service.start_transient()

    elif service_state == "exited":
        service.start_transient()

    elif service_state == "failed":
        service.reset_failed()
        service.restart()

    elif service_state == "running":
        prntr.printi("Service is running and listening on " + str(server_port))

        if "stop" == action:
            prntr.printi("Stopping ledctrl service")
            service.stop()
            exit(0)

    if len(action) > 0:
        prntr.printd("Sending: " + action)
        c = udp_client(server_ip, server_port)
        c.sendm(action)
