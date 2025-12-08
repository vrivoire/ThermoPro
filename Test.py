import matplotlib.pyplot as plt
import numpy as np


def on_click(event):
    """Callback function to handle mouse clicks."""
    if event.inaxes:  # Check if the click was within an Axes
        # Get the Axes object where the click occurred
        ax = event.inaxes

        # Check if the click is near the x-axis
        # This is a simplified check; you might need more robust logic
        # depending on your specific needs (e.g., considering tick labels, etc.)
        if ax == plt.gca() and abs(event.ydata - ax.get_ylim()[0]) < 0.1 * (ax.get_ylim()[1] - ax.get_ylim()[0]):
            print(f"Clicked on x-axis at x-coordinate: {event.xdata:.2f}")
        else:
            print(f"Clicked within Axes, but not specifically on x-axis. X: {event.xdata:.2f}, Y: {event.ydata:.2f}")
    else:
        print("Clicked outside any Axes.")


# Create a figure and axes
fig, ax = plt.subplots()

# Plot some data
x = np.linspace(0, 10, 100)
y = np.sin(x)
ax.plot(x, y)

ax.set_xlabel("X-axis Label")
ax.set_ylabel("Y-axis Label")
ax.set_title("Click on X-axis Example")

# Connect the callback function to the button_press_event
fig.canvas.mpl_connect('button_press_event', on_click)

plt.show()
