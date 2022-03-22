from europi import *
from time import ticks_diff, ticks_ms
from math import fabs, floor
from random import choice

'''
Strange Attractor
author: Sean Bechhofer (github.com/seanbechhofer)
date: 2022-03-15
labels: gates, triggers, randomness

Strange Attractor is a source of chaotic modulation. It can use a variety of different implementations.

Outputs 1, 2 and 3 are based on the x, y and z values generated by the attractor.

Outputs 4, 5 and 6 are gates based on the values of x, y and z and relationships between them. 

digital_in: Pause motion when HIGH
analog_in: 

knob_1: Adjust speed
knob_2: Adjust threshold for triggers

button_1: Decrease output voltage range, change equation system
button_2: Increase output voltage range

output_1: x 
output_2: y
output_3: z
output_4: triggers/gates
output_5: triggers/gates
output_6: triggers/gates

'''
# Version number

VERSION="1.0"

# Overclock the Pico for improved performance.
machine.freq(250_000_000)

# Maximum voltage output. Cranking this up may cause issues with some modules. 
MAX_OUTPUT = 5

'''
Implementation of strange attractors, providing chaotic values for modulation.

* Lorenz. Well known system of equations giving chaotic behaviour. 
  See https://en.wikipedia.org/wiki/Lorenz_system
* Pan-Xu-Zhou. 
  See https://www.semanticscholar.org/paper/Controlling-a-Novel-Chaotic-Attractor-using-Linear-Pan-Xu/72f9c1b1f892b3aeea26af330d44011a20250f32
* Rikitake. Used to model the earth's geomagnetic field and explain the irregular switch in polarity. 
  See Llibre, Jaume & Messias, Marcelo. (2009). Global dynamics of the Rikitake system. Physica D: Nonlinear Phenomena. 238. 241-252. 10.1016/j.physd.2008.10.011. 
* Rossler. Use with caution. The z co-ord sits around zero for long periods. 
  See https://en.wikipedia.org/wiki/R%C3%B6ssler_attractor
'''

class Attractor:
    def __init__(self, point=(0.,1.,1.05), dt=0.01, name="Attractor"):
        self.initial_state = point
        self.x = point[0]
        self.y = point[1]
        self.z = point[2]
        self.dt = dt
        self.name = name
        self.x_min = self.x
        self.y_min = self.y
        self.z_min = self.z
        self.x_max = self.x
        self.y_max = self.y
        self.z_max = self.z
        # arbitrary initial range values    
        self.x_range = 100
        self.y_range = 100
        self.z_range = 100
        
    # The range of values produced depends on the parameters and the
    # specifics of the equations. If we know the range, we can then
    # normalise coordinates for use when generating CV. This method
    # runs through a number of iterations to estimate ranges.
    def estimate_ranges(self,steps=100000):
    
        # Execute a number of steps to get upper and lower bounds. 
        for i in range(steps):
            self.step()
            
            self.x_max = max(self.x, self.x_max)
            self.y_max = max(self.y, self.y_max)
            self.z_max = max(self.z, self.z_max)
            self.x_min = min(self.x, self.x_min)
            self.y_min = min(self.y, self.y_min)
            self.z_min = min(self.z, self.z_min)

        self.x_range = self.x_max-self.x_min
        self.y_range = self.y_max-self.y_min
        self.z_range = self.z_max-self.z_min
        
        # Reset to initial parameters
        self.x = self.initial_state[0]
        self.y = self.initial_state[1]
        self.z = self.initial_state[2]
        

    def x_scaled(self):
        return (100.0 * (self.x - self.x_min))/self.x_range

    def y_scaled(self):
        return (100.0 * (self.y - self.y_min))/self.y_range

    def z_scaled(self):
        return (100.0 * (self.z - self.z_min))/self.z_range

    def __str__(self):
        return (f"{self.name:>16} ({self.x:2.2f},{self.y:2.2f},{self.z:2.2f})({self.x_scaled():2.2f},{self.y_scaled():2.2f},{self.z_scaled():2.2f})")
    
    def step(self):
        '''
        Update the point. This needs to be implemented in subclasses. 
        '''
        pass

'''
Implementation of a simple Lorenz Attractor, see 

https://en.wikipedia.org/wiki/Lorenz_system

Default uses well known values of s=10,r=28,b=2.667. 
'''
class Lorenz(Attractor):
    def __init__(self, point=(0.,1.,1.05), params=(10,28,2.667), dt=0.01):
        super().__init__(point, dt, "Lorenz")
        self.s = params[0]
        self.r = params[1]
        self.b = params[2]

    def step(self):
        '''
        Update the point.
        '''
        x_dot = self.s*(self.y - self.x)
        y_dot = self.r*self.x - self.y - self.x*self.z
        z_dot = self.x*self.y - self.b*self.z
        self.x += x_dot * self.dt
        self.y += y_dot * self.dt
        self.z += z_dot * self.dt
        
# Pan-Xu-Zhou
'''
Implementation of Pan-Xu-Zhou
'''
class PanXuZhou(Attractor):
    def __init__(self, point=(1.,1.,1.), params=(10.0,2.667,16.0), dt=0.01):
        super().__init__(point,dt, "Pan-Xu-Zhou")
        self.a = params[0]
        self.b = params[1]
        self.c = params[2]

    def step(self):
        '''
        Update the point.
        '''
        x_dot = self.a*(self.y - self.x)
        y_dot = self.c*self.x - self.x*self.z
        z_dot = self.x*self.y - self.b*self.z
        self.x += x_dot * self.dt
        self.y += y_dot * self.dt
        self.z += z_dot * self.dt

'''
Implementation of Rossler. The z co-rd spends a lot of time around zero, so use with caution.
'''
class Rossler(Attractor):
    def __init__(self, point=(0.1,0.0,-0.1), params=(0.13,0.2,6.5), dt=0.01):
        super().__init__(point,dt, "Rossler")
        self.a = params[0]
        self.b = params[1]
        self.c = params[2]

    def step(self):
        '''
        Update the point.
        '''
        x_dot = -(self.y + self.z)
        y_dot = self.x + self.a*self.y
        z_dot = self.b + self.z*(self.x - self.c)
        self.x += x_dot * self.dt
        self.y += y_dot * self.dt
        self.z += z_dot * self.dt

'''
Implementation of Rikitake. 
'''
class Rikitake(Attractor):
    def __init__(self, point=(0.1,0.0,-0.1), params=(5.0,2.0), dt=0.01):
        super().__init__(point,dt, "Rikitake")
        self.a = params[0]
        self.mu = params[1]

    def step(self):
        '''
        Update the point.
        '''
        x_dot = -(self.mu * self.x) + (self.z*self.y)
        y_dot = -(self.mu * self.y) + self.x*(self.z - self.a)
        z_dot = 1 - (self.x * self.y)
        self.x += x_dot * self.dt
        self.y += y_dot * self.dt
        self.z += z_dot * self.dt


def get_attractors():
    return [Lorenz(), PanXuZhou(), Rikitake(), Rossler()]

class StrangeAttractor:
    def __init__(self, _attractors):
        # Initialise and calculate ranges. 
        # This will take around 30 seconds per attractor.
        self.attractors = _attractors
        for att in self.attractors:
            self.initialise_message(att.name)
            att.estimate_ranges()
            self.done_message()
        # select a random attractor
        self.selected_attractor = choice(range(0,len(self.attractors)))
        self.a = self.attractors[self.selected_attractor]
        # Initialize variables
        self.checkpoint = 0
        # time before update
        self.period = 100
        # output range.
        self.range = MAX_OUTPUT
        # initial threshold for gates
        self.threshold = 20
        # freeze motion
        self.freeze = False
        # Display details
        self.show_detail = True

        # Triggered when button 1 is released
        # Short press: decrease range
        # Long press: change equation system
        @b1.handler_falling
        def b1Pressed():
            if ticks_diff(ticks_ms(), b1.last_pressed()) >  300:
                # long press This will result in a jump in parameters
                # as each attractor has its own x,y,z
                # coordinates. Possible improvement is to share or set
                # coordinates on change.
                self.selected_attractor = (self.selected_attractor + 1) % len(self.attractors)
                self.a = self.attractors[self.selected_attractor]
            else:
                # short press
                self.range -= 1
                if self.range < 1:
                    self.range = 1

        # Triggered when button 2 is released.
        # Short press: increase range
        # Long press: toggle display
        @b2.handler_falling
        def b2Pressed():
            
            if ticks_diff(ticks_ms(), b2.last_pressed()) >  300:
                # long press
                self.show_detail = not self.show_detail
            else:
                # short press
                self.range += 1
                if self.range > MAX_OUTPUT:
                    self.range = MAX_OUTPUT

        # Freeze is triggered when din goes HIGH.
        @din.handler
        def dinTrigger():
            # Pause
            self.freeze = True

        @din.handler_falling
        def dinTriggerEnd():
            # Start agin
            self.freeze = False

    def update_values(self):
        if not self.freeze:
            self.a.step()
        
    def update_speed(self):
        # Set speed based on the knob.
        # The range is piecewise linear from fully CCW to noon and noon to fully CW.
        # TODO: allow speed adjustment via CV. 
        val = k1.read_position()
        low = 1000 # CCW
        mid = 100 # noon
        high = 10 # CW

        if val == 0:
            self.period = low
        elif val < 50:
            self.period = low - ((low-mid) * (val/50))
        else:
            self.period = mid - ((mid-high) * (val-50)/50)
        

    def update_threshold(self):
        self.threshold = k2.read_position(steps=41)        

    def update(self):
        # Change the values and output
        self.update_values()
        cv1.voltage((self.range * self.a.x_scaled()) / 100)
        cv2.voltage((self.range * self.a.y_scaled()) / 100)
        cv3.voltage((self.range * self.a.z_scaled()) / 100)
        # Calculate gates
        # gate 1 fires if x is divisible by 2 when considered an int
        self.gate4 = floor(self.a.x_scaled()) % 2 == 0
        # gates 2 and 3 look at the differences between the outputs. 
        self.gate5 = fabs(self.a.y_scaled() + self.a.z_scaled() - 2*self.a.x_scaled()) > self.threshold
        self.gate6 = fabs(self.a.z_scaled() + self.a.x_scaled() - 2*self.a.y_scaled()) > self.threshold

        # Set gates
        cv4.value(self.gate4)
        cv5.value(self.gate5)
        cv6.value(self.gate6)
        
        self.checkpoint = ticks_ms()
        self.update_screen()

    def main(self):
        while True:
            self.update_speed()
            self.update_threshold()
            if ticks_diff(ticks_ms(), self.checkpoint) > self.period:
                self.update()

    def initialise_message(self, att_name):
        oled.fill(0)
        oled.text('Strange',0,0,1)
        oled.text(f"Attractor v{VERSION}",0,8,1)
        oled.text('Initialising...',0,16,1)
        oled.text(att_name,10,24,1)
        oled.show()
        
    def done_message(self):
        oled.fill(0)
        oled.text('Done',0,0,1)
        oled.show()
        
    def update_screen(self):
        oled.fill(0)
        if self.show_detail:
            oled.text('1:' + str(int(self.a.x_scaled())),0,0,1)
            oled.text('2:' + str(int(self.a.y_scaled())),0,8,1)
            oled.text('3:' + str(int(self.a.z_scaled())),0,16,1)
            oled.text('S:' + str(int(self.period)),40,0,1)
            oled.text('T:' + str(int(self.threshold)),40,8,1)
            oled.text('R:' + str(int(self.range)),40,16,1)
        else:
            oled.text('1:',0,0,1)
            oled.fill_rect(20,0,int(0.75*self.a.x_scaled()),6,1)
            oled.rect(20,0,75,6,1)
            oled.text('2:',0,8,1)
            oled.fill_rect(20,8,int(0.75*self.a.y_scaled()/2),6,1)
            oled.rect(20,8,75,6,1)
            oled.text('3:',0,16,1)
            oled.fill_rect(20,16,int(0.75*self.a.z_scaled()/2),6,1)
            oled.rect(20,16,75,6,1)

        if self.gate4:
            oled.text('4',100,0,1)
        if self.gate5:
            oled.text('5',100,8,1)
        if self.gate6:
            oled.text('6',100,16,1)
        if self.freeze:
            oled.text('FREEZE',0,24,1)
        oled.text(self.a.name,55,24,1)
            
        oled.show()

# Reset module display state.
reset_state()
sa = StrangeAttractor(get_attractors())
sa.main()

