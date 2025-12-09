import asyncio

from hilo import Hilo


async def main():
    # Replace with your actual Hilo username and password
    username = "your_hilo_username"
    password = "your_hilo_password"

    try:
        # Initialize the Hilo object
        hilo = Hilo(username, password)

        # Authenticate and retrieve data
        await hilo.authenticate()
        await hilo.get_data()

        # Accessing some data (e.g., devices)
        if hilo.devices:
            print("Hilo Devices:")
            for device_id, device in hilo.devices.items():
                print(f"  ID: {device_id}, Name: {device.name}, Type: {device.device_type}")
                # You can access other attributes like device.state, device.attributes, etc.
        else:
            print("No Hilo devices found.")

        # Example of interacting with a specific device (if applicable)
        # This part will depend on the type of device and what actions it supports
        # For instance, if you have a thermostat and want to change its setpoint:
        # if 'your_thermostat_id' in hilo.devices:
        #     thermostat = hilo.devices['your_thermostat_id']
        #     if thermostat.device_type == 'thermostat':
        #         await hilo.set_thermostat_setpoint(thermostat.id, 20.0) # Set to 20 degrees Celsius
        #         print(f"Thermostat '{thermostat.name}' setpoint changed to 20.0°C")

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    asyncio.run(main())
