import matplotlib.pyplot as plt
import numpy as np

# Create some sample data
data = np.random.rand(10, 10)

# Display the data using the 'Reds' colormap
plt.imshow(data, cmap='Reds', interpolation='nearest')
plt.colorbar(label='Value')
plt.title("Red Gradient with Matplotlib 'Reds'")
plt.show()
