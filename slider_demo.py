# Import libraries using import keyword
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider

# Setting Plot and Axis variables as subplots()
# function returns tuple(fig, ax)
fig, ax1 = plt.subplots()

# Set the x and y-axis to some dummy data
t = np.arange(0.0, 100.0, 0.1)
s = np.sin(2 * np.pi * t)

plt.subplots_adjust(bottom=0.25)
plt.plot(t, s)

# Set the axis and slider position in the plot
axis_position = plt.axes((0.2, 0.1, 0.65, 0.03), facecolor='White')
slider_position = Slider(axis_position, 'Pos', 0.1, 90.0)


# update() function to change the graph when the slider is in use
def update(val):
    ax1.axis([val, val + 10, -1, 1])
    fig.canvas.draw_idle()


slider_position.on_changed(update)
plt.show()
