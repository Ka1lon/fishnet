#!/usr/bin/env python

"""M CLOCK 2.0."""

import sys
import time
import math
from sense_hat import SenseHat
import random

from PIL import Image, ImageDraw

RADIUS = 32

def radians(angle):
    """ Convert degrees to radians """
    return math.pi * angle / 180.
    

class MClock:

    def __init__(self, radius=200, segments=9, dim=0.8):
        self.segments = segments

        self.image = Image.new('RGB', (RADIUS * 2, RADIUS * 2))
        self.img = ImageDraw.Draw(self.image)
        
        self.display_credits =  False
        self.seconds = True
        self.hat = SenseHat()
        self.radius = RADIUS
        self.dim = dim
        self.recalc(self.radius*2, self.radius*2)


    def set_segments(self, *args):

        self.segments = max(self.segments, 2)

    def toggle_text(self, *args):
        self.showtext = not self.showtext

    def toggle_seconds(self, *args):
        self.seconds = not self.seconds

    def show_credits(self, *args):

        self.hat.show_message(self.credits)

    def quit(self, *args):
        self.running = False

    credits = ("M Clock 2.0\n"
               "by Johnny Gill\n"
               "after tkinter by Guido van Rossum\n"
               "after a design by Rob Juda")

    creditid = None
    showtext = False

    def recalc(self, width, height):

        radius = min(width, height) // 2

        self.radius = radius
        self.bigsize = radius * .975
        self.litsize = radius * .67

    def run(self):

        self.running = True
        while self.running:
            t = time.time()
            hh, mm, ss = time.localtime(t)[3:6]
            self.draw(hh, mm, ss)
            self.blit()
            time.sleep(1.0)

    def blit(self):
        """ Update the image on the sense hat

        Need to downsample from RADIUS to 8

        Let's just pick a pixel at random and see how that works
        """
        size = self.radius // 4

        for x in range(8):
            for y in range(8):
                
                xpos = size * x
                ypos = size * y

                pix = self.pixel_picker(xpos, ypos, size, size)

                self.hat.set_pixel(x, y, pix)

    def pick_pixel(self, xpos, ypos, xx, yy):

        rr = gg =bb = 0
        
        for x in range(xx):
            for y in range(yy):
                
                r, g, b = self.image.getpixel((xpos + x, ypos + y))

                rr += r
                gg += g
                bb += b

        count = xx * yy
        pix = (rr // count, gg // count, bb // count)

        return pix

    def weighted_pick_pixel(self, xpos, ypos, xx, yy):

        rr = gg =bb = 0

        weight = 0
        for x in range(xx):
            for y in range(yy):

                # Use Euclidean distance from centre as weight
                this_weight = (abs(x - xx/2)) ** 2 
                this_weight += (abs(y - yy/2)) ** 2

                this_weight = this_weight ** 0.5

                weight += this_weight
                
                r, g, b = self.image.getpixel((xpos + x, ypos + y))

                rr += this_weight * r
                gg += this_weight * g
                bb += this_weight * b

        count = weight / self.dim
        pix = (int(rr // count),
               int(gg // count),
               int(bb // count))

        return pix

    pixel_picker = weighted_pick_pixel
    
    def xpick_pixel(self, xpos, ypos, xx, yy):

        pickx = random.randint(0, xx-1)
        picky = random.randint(0, xx-1)

        pix = self.image.getpixel((xpos + pickx, ypos + picky))

        return pix

    def get_angles(self, hh, mm, ss):
        
        # Set bigd, litd to angles in degrees for big, little hands
        # 12 => 90, 3 => 0, etc.
        secd = (90 - (ss * 60) / 10) % 360
        bigd = (90 - (mm*60 + ss) / 10) % 360
        litd = (90 - (hh*3600 + mm*60 + ss) / 120) % 360

        return secd, bigd, litd

    def draw(self, hh, mm, ss, colors=(0, 1, 2)):
        radius = self.radius
        bigsize = self.bigsize
        litsize = self.litsize

        # Delete old items
        #self.hat.clear()

        secd, bigd, litd = self.get_angles(hh, mm, ss)

        # Set bigr, litr to the same values in radians
        bigr = radians(bigd)
        litr = radians(litd)

        # Draw the background colored arcs
        self.drawbg(bigd, litd, secd, colors)
        
        # Draw the hands
        self.draw_hands(bigr, litr)

    def draw_hands(self, bigr, litr, colour=(0,0,0), scale=1.0):

        # Draw the hands
        radius = self.radius
        bigsize = self.bigsize * scale
        litsize = self.litsize * scale
        img = self.img

        r, g, b = colour
        xcolour = (255-r, 255-g, 255-b)
        xcolour = (255, 0, 0)

        b = img.line([radius, radius,
                      radius + int(bigsize*math.cos(bigr)),
                      radius - int(bigsize*math.sin(bigr))],
                     width=12,
                     fill=xcolour)

        l = img.line([radius, radius,
                      radius + int(bigsize*math.cos(litr)),
                      radius - int(bigsize*math.sin(litr))],
                     width=12,
                     fill=colour)


    def drawbg(self, bigd, litd, secd, colors=(0, 1, 2)):
        # This is tricky.  We have to simulate a white background with
        # three transparent discs in front of it; one disc is
        # stationary and the other two are attached to the big and
        # little hands, respectively.  Each disc has 9 pie segments in
        # sucessive shades of pigment applied to it, ranging from
        # fully transparent to only allowing one of the three colors
        # Cyan, Magenta, Yellow through.

        if not self.seconds:
            secd = 90
        img = self.img
        N = self.segments
        table = []
        for angle, colorindex in [(bigd - 180/N, 0),
                                  (litd - 180/N, 1),
                                  (secd - 180/N, 2)]:
            angle %= 360
            for i in range(N):
                color = 255
                if colorindex in colors:
                    color = (N-1-i)*color//(N-1)
                table.append((angle, color, colorindex))
                angle += 360/N
                if angle >= 360:
                    angle -= 360
                    table.append((0, color, colorindex))
        table.sort()
        table.append((360, None))
        radius = self.radius
        fill = [0, 0, 0]
        i = 0
        for angle, color, colorindex in table[:-1]:

            fill[colorindex] = color
            if table[i+1][0] > angle:
                extent = table[i+1][0] - angle
                if extent < 1.:
                    # XXX Work around a bug in Tk for very small angles
                    # I think this bug is also present in appuifw
                    extent = 1.
                #print([0, 0, 2 * radius, 2 * radius])
                #print(type(2 * radius))
                #print(fill)
                img.pieslice([0, 0, 2 * radius, 2 * radius],
                            int(angle), int(extent+angle),
                            fill=tuple(fill))
            i+=1

def main(dim=0.5):
    MClock(dim=dim).run()

if __name__ == "__main__":
    import sys

    dim = 0.5
    if len(sys.argv) > 1:
        dim = float(sys.argv[1])

    main(dim)
        
