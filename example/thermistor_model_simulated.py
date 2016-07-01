import threading
import time
import random
# import math
import pint

class ThermistorModelSimulated:
    def __init__(self, u=5.0, r0=3000, interval=5, ureg=None):
        self.u = u                  # Total voltage
        self.r0 = r0                # Reference resistor
        self.ux = self.u / 2        # Initial voltage on thermistor
        self.c1 = 1.40e-3
        self.c2 = 2.37e-4
        self.c3 = 9.90e-8
        self.interval = interval
        self.ureg = None
        if isinstance(ureg, pint.UnitRegistry):
            self.ureg = ureg
        else:
            self.ureg = pint.UnitRegistry()

    def run(self):
        self.th = threading.Thread(target=self.simulate)
        self.th.daemon = True
        self.th.start()

    def simulate(self):
        while True:
            # Sleep until next cycle
            time.sleep(self.interval)

            self.ux = min(
                    max(
                            self.ux + \
                                random.uniform(-0.01, 0.01) * self.interval,
                            1.5
                        ),  3.5
                )

    def get_u(self):
        return self.ureg.volt * self.u

    def get_r0(self):
        return self.ureg.ohm * self.r0

    def get_ux(self):
        return self.ureg.volt * self.ux

    def get_c1(self):
        return self.c1 / self.ureg.kelvin

    def get_c2(self):
        return self.c2 / self.ureg.kelvin

    def get_c3(self):
        return self.c3 / self.ureg.kelvin

def main():
    thermistor = ThermistorModelSimulated()
    thermistor.run()
    while True:
        print "u:       {},\nux:      {},\nr0:      {}\n---".format(
                thermistor.get_u(),
                thermistor.get_ux(),
                thermistor.get_r0()
            )
        time.sleep(5)

if __name__ == '__main__':
    main()
