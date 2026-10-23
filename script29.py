
from datetime import datetime, timezone
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

BAD_RANGES = [(10, 15), (40, 45)]
GOOD_RANGES = [(0, 9), (20, 29)]


def get_timestamp():
    return datetime.now(timezone.utc).isoformat()


def in_ranges(value, ranges):
    return any(low <= value <= high for low, high in ranges)


def classify_flow(flowsystem):
    if (
        isinstance(flowsystem, bool)
        or not isinstance(flowsystem, (int, float))
        or flowsystem < 0
    ):
        return "invalid"

    if in_ranges(flowsystem, BAD_RANGES):
        return "bad"

    if in_ranges(flowsystem, GOOD_RANGES):
        return "good"

    return "unknown"


class WaterPump:
    def __init__(self):
        self.pump_running = False
        self.fault_latched = False

    def start(self):
        if self.fault_latched:
            logging.error("Start blocked: reset the fault first")
            return

        self.pump_running = True
        logging.info("Pump start requested")

    def shutdown(self, reason):
        self.pump_running = False
        self.fault_latched = True
        logging.critical("PUMP SHUTDOWN: %s", reason)

    def monitor(self, flowsystem):
        status = classify_flow(flowsystem)

        logging.info(
            "Flow=%s | Status=%s | Pump=%s | Time=%s",
            flowsystem,
            status,
            "RUNNING" if self.pump_running else "OFF",
            get_timestamp(),
        )

        if status in ("bad", "invalid"):
            self.shutdown(f"Flow status: {status}")

        elif status == "unknown" and self.pump_running:
            logging.warning("Flow is outside configured ranges")

        return status


def main():
    pump = WaterPump()
    pump.start()

    readings = [22, 23, 12, 24, 42]

    for flow in readings:
        status = pump.monitor(flow)

        if pump.fault_latched:
            logging.error("Pump remains off until fault reset")
            break


if __name__ == "__main__":
    main()
