
from datetime import datetime, timezone
import logging

from __init__ import BAD_RANGES, GOOD_RANGES


# config for logging library
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


def get_timestamp():
    return datetime.now(timezone.utc).isoformat()


def in_ranges(value, ranges):
    return any(low <= value <= high for low, high in ranges)


def classify_flow(datapoint):
    #boolean, not int or float, less than 0 -> return invalid
    if (
        isinstance(datapoint, bool)
        or not isinstance(datapoint, (int, float))
        or datapoint < 0
    ):
        return "invalid"
    
    if in_ranges(datapoint, BAD_RANGES):
        return "bad"

    if in_ranges(datapoint, GOOD_RANGES):
        return "good"

    return "unknown"

"""
Class: WaterPump

props: 
  pump_running: bool, 
  fault_latched: bool

methods:
  start() -> none
   

TODO 
  * Finish class header
  * For start/stop create Error type which can be ezcalated up to main upon
    failure to start or stop pump, or latch/unlatch fault
"""
class WaterPump:
    def __init__(self):
        self.pump_running = False
        self.fault_latched = False
    
    # Start the water pump
    def start(self):
        # early return if fault locked
        if self.fault_latched:
            logging.error("Start blocked: reset the fault first")
            return
        
        try:
            logging.info("Pump start requested")
            self.pump_running = True

        # TODO: Replace general Exception with the Error types given
        # by the hardware used
        except Exception as error:
            print(f"Issue starting pump: {error}")
            #Ensure value of pump_running is false if it failed to start
            self.pump_running = False
            # escalate error to main
            return error
    
        #Return true if no errors
        return True

    # Shut off the water pump
    def shutdown(self, reason):
        logging.critical("ATTEMPTING PUMP SHUTDOWN: %s", reason)
        try:
            self.pump_running = False
            print("Pump successfully stopped.")
        except Exception as error:
            print(f"Failed to stop pump: {error}")
            print(f"Pump status: {'running' if self.pump_running else 'not running'}")
            print("Pump may require manual interfacing")
            # escalate error to main
            return error

        try:
            print("Attempting to latch fault...")
            self.fault_latched = True
            print("Fault latched successfully.")
        except Exception as error:
            print(f"Failed to latch fault: {error}")
            print(f"Fault status: {'latched' if self.fault_latched else 'unlatched'}")
            print("Latch may require manual interfacing.")
            # escalate error to main
            return error

        return True


    def monitor(self, datapoint):
        status = classify_flow(datapoint)
        logging.info(
            "Flow=%s | Status=%s | Pump=%s | Time=%s",
            datapoint,
            status,
            "RUNNING" if self.pump_running else "OFF",
            get_timestamp(),
        )
        
        #Unrecoverable errors, terminate program
        if status is "invalid":
            print("Sensor is giving incorrectly typed data.")
            print("Make sure WaterPump.classify_flow() is being passed correct data.")
            raise TypeError
        elif status == "unknown" and self.pump_running:
            print("Flow is outside configured ranges.")
            print("Sensor is giving incorrectly typed data.")
            print("Make sure WaterPump.classify_flow() is being passed correct data.")
            raise TypeError
        # recoverable, just turn off pump
        elif status is "bad":
            raise ValueError("Flow is within a bad range.")
        #return status


def main():
    pump = WaterPump()
    pump.start()

    example_readings = [22, 23, 12, 24, 42]

    for datapoint in example_readings:
        #status = pump.monitor(flow)
        try:
            pump.monitor(datapoint)
        except TypeError:
            print("Attempting to close fault latch, and shut down pump.")
            pump.shutdown("Bug in program.")
        except ValueError as error:
            pump.shutdown(error)

        if pump.fault_latched:
            logging.error("Pump remains off until fault reset")
            break


if __name__ == "__main__":
    main()
