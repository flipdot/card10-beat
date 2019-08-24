import os
import leds
import utime
import buttons
import display
import urandom


class App:

    def __init__(self):
        # color in hsv. 0 = red, 360 = red
        self.top_hue = 0
        # 0 = min brightness, 1 = max brightness
        self.top_value = 0

        self.bottom_hue = 120
        self.bottom_value = 1

        self.button_pressed = {}
        self.button_state = 0  # assume nothing pressed
        self.recorded_beats = []
        self.tick_id = -1

        self.median_tick_delta = -1
        self.beat_start_tick = -1

        self.sync_indicator = True

        with display.open() as d:
            d.print('COLOR >', posy=40, posx=50)
            d.print('INDICATE >', posx=10)
            d.print('< SYNC BEAT', posy=60)
            d.update()

    def tick(self, tick_id):
        self.tick_id = tick_id
        self.process_inputs()
        self.update_leds()

        if self.median_tick_delta > -1 and self.beat_start_tick > -1:
            start = (tick_id - self.beat_start_tick)
            v = App.interpolate_value(start, self.median_tick_delta)
            self.top_value = v

        if tick_id % 10 == 0:
            # fade out ALL the colors
            # self.top_value = max(0, self.top_value - 0.01)
            self.bottom_value = max(0, self.bottom_value - 0.01)

    @staticmethod
    def interpolate_value(tick, tick_delta):
        d = tick_delta / 1.3
        progress = d - (tick % tick_delta)
        v = float(progress) / float(d)
        if v < 0:
            return 0
        return v

    def calculate_tick_distance(self):
        beats = self.recorded_beats
        l = [beats[i] - beats[i-1] for i in range(1, len(beats))]
        l.sort()
        self.median_tick_delta = l[len(l) // 2]
        # last button press is the starting point for
        self.beat_start_tick = self.recorded_beats[-1]

    def record_beat(self):
        if len(self.recorded_beats) > 0:
            last_beat = self.recorded_beats[-1]
            if self.tick_id - last_beat > 3000:
                # clear beats, last syncing was a while ago (1000 ticks = ?? seconds)
                self.recorded_beats = []
        self.recorded_beats.append(self.tick_id)
        if len(self.recorded_beats) >= 4:
            self.calculate_tick_distance()

    def button_down(self, button):
        ret = False
        pressed = self.button_state & button != 0
        if pressed and not self.button_pressed.get(button):
            self.button_pressed[button] = True
            ret = True
        if not pressed:
            self.button_pressed[button] = False
            ret = False
        return ret

    def process_inputs(self):
        self.button_state = buttons.read(buttons.BOTTOM_RIGHT | buttons.BOTTOM_LEFT | buttons.TOP_RIGHT)
        if self.button_down(buttons.BOTTOM_RIGHT):
            self.top_hue += 10
            self.bottom_hue += 10
            self.top_hue %= 360
            self.bottom_hue %= 360
        if self.button_down(buttons.BOTTOM_LEFT):
            self.bottom_value = 1
            self.record_beat()
        if self.button_down(buttons.TOP_RIGHT):
            self.sync_indicator = not self.sync_indicator

    def update_leds(self):
        # First 11 leds are the top leds, last 4 are the bottom ones. Generate a long list of all values
        top_colors = [(self.top_hue, 1, self.top_value)] * 11
        if self.sync_indicator:
            bottom_colors = [(self.bottom_hue, 1, self.bottom_value)] * 4
        else:
            bottom_colors = [(self.top_hue, 1, self.top_value)] * 4
        colors = top_colors + bottom_colors
        leds.set_all_hsv(colors)


if __name__ == '__main__':
    app = App()
    i = 0
    while True:
        app.tick(i)
        i += 1
