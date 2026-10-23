from datetime import datetime, timezone
import logging
import time


# config for logging library
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# target ranges
BAD_RANGES = [(10, 15), (40, 45)]
GOOD_RANGES = [(0, 9), (20, 29)]


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

class WaterPump:
    """
    Class: WaterPump

    Controls the water pump and shuts it down when the flow readings
    say it should stop.

    props:
      pump_running: bool, True while the pump is on
      fault_latched: bool, True after a shutdown; blocks start() until reset

    methods:
      start() -> None
        Turns the pump on. Does nothing if a fault is latched.
        Re-raises any start failure so main() can retry.

      shutdown(reason) -> None
        Turns the pump off, then latches the fault. Logs reason.
        Re-raises any stop or latch failure.

      monitor(datapoint) -> None
        Classifies one flow reading and logs it.
          "invalid" -> raises TypeError (unrecoverable)
          "bad"     -> raises ValueError (recoverable, shut pump down)
          "unknown" -> logs a warning while the pump is running, keeps going

    TODO
      * For start/stop create Error type which can be escalated up to main upon
        failure to start or stop pump, or latch/unlatch fault
    """

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
        except Exception:
            #Ensure value of pump_running is false if it failed to start
            self.pump_running = False
            # escalate error to main
            raise

    # Shut off the water pump
    def shutdown(self, reason):
        logging.critical("ATTEMPTING PUMP SHUTDOWN: %s", reason)
        try:
            self.pump_running = False
            logging.info("Pump successfully stopped.")
        except Exception as error:
            logging.critical("Failed to stop pump: %s", error)
            logging.critical("Pump status: %s", "running" if self.pump_running else "not running")
            logging.critical("Pump may require manual interfacing")
            # escalate error to main
            raise

        try:
            logging.info("Attempting to latch fault...")
            self.fault_latched = True
            logging.info("Fault latched successfully.")
        except Exception as error:
            logging.critical("Failed to latch fault: %s", error)
            logging.critical("Fault status: %s", "latched" if self.fault_latched else "unlatched")
            logging.critical("Latch may require manual interfacing.")
            # escalate error to main
            raise

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
        if status == "invalid":
            logging.error("Sensor is giving incorrectly typed data.")
            logging.error("Make sure WaterPump.classify_flow() is being passed correct data.")
            raise TypeError
        # not fatal, warn and keep running
        elif status == "unknown" and self.pump_running:
            logging.warning("Flow is outside configured ranges")
        # recoverable, just turn off pump
        elif status == "bad":
            raise ValueError("Flow is within a bad range.")
        #return status


def main():
    pump = WaterPump()

    #allow three pump startup retries before terminating
    retries = 0
    while retries <= 2:
        try:
            pump.start()
            break
        except Exception as error:
            logging.error("Error starting pump: %s", error)
            logging.info("Retrying...")
            retries += 1
            time.sleep(2)
            continue
    # runs only if the loop ended without a break (every start attempt failed)
    else:
        logging.critical("Maximum retries reached. Shutting down.")
        return

    example_readings = [22, 23, 12, 24, 42]

    for datapoint in example_readings:
        #status = pump.monitor(flow)
        try:
            pump.monitor(datapoint)
        except TypeError:
            logging.warning("Attempting to close fault latch, and shut down pump.")
            pump.shutdown("Bug in program.")
        except ValueError as error:
            pump.shutdown(error)

        if pump.fault_latched:
            logging.error("Pump remains off until fault reset")
            break


if __name__ == "__main__":
    main()
