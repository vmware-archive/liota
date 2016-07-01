import threading
import time
import random
import math
import pint

class BikeModelSimulated:
    def __init__(self,
            wheel=26, m_bike=20, m_rider=80, m_load=0, interval=5,
            ureg=None):
        self.slope = 0.0            # rad
        self.radius_wheel = wheel   # inch
        self.weight_bike  = m_bike  # kg
        self.weight_rider = m_rider # kg
        self.weight_load  = m_load  # kg
        self.revolution = 0.0       # rpm
        self.area = 1.0             # m ** 2
        self.interval = interval
        self.ureg = None
        if isinstance(ureg, pint.UnitRegistry):
            self.ureg = ureg
        else:
            self.ureg = pint.UnitRegistry()
        self.time_last = None

    def run(self):
        self.th = threading.Thread(target=self.simulate)
        self.th.daemon = True
        self.th.start()

    def simulate(self):
        while True:
            # Sleep until next cycle
            time.sleep(self.interval)

            # Change slope
            self.slope = min(
                    max(self.slope + \
                            random.uniform(-0.01, 0.01) * self.interval,
                            -math.pi / 16
                        ), math.pi / 16
                )

            # Change revolution
            self.revolution = min(
                    max(
                        self.revolution + \
                            random.uniform(-2.0, 5.0) * self.interval,
                        0
                    ), 40
                )

            # Change load
            t = time.time()
            if self.time_last is None:
                self.time_last = t
            else:
                if t - self.time_last >= 30:
                    self.weight_load = random.randrange(0, 50)
                    self.time_last = t

    def get_slope(self):
        return self.ureg.rad * self.slope

    def get_revolution(self):
        return self.ureg.rpm * self.revolution

    def get_radius_wheel(self):
        return self.ureg.inch * self.radius_wheel

    def get_weight_bike(self):
        return self.ureg.kg * self.weight_bike

    def get_weight_rider(self):
        return self.ureg.kg * self.weight_rider

    def get_weight_load(self):
        return self.ureg.kg * self.weight_load

    def get_area(self):
        return self.ureg.m ** 2 * self.area

def main():
    bike = BikeModelSimulated()
    bike.run()
    while True:
        print "slope:   {},\nrev:     {},\nload:    {}\n---".format(
                bike.get_slope(),
                bike.get_revolution(),
                bike.get_weight_load()
            )
        time.sleep(5)

if __name__ == '__main__':
    main()
