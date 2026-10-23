
# TODO

### Things to keep in mind

* Currently nothing turns the pump off when the program exits or crashes
* Extremely high readings only give warnings. For example, a 500 reading would not cause a panic.
* Sensors, especially cheaper ones, do not give very consistent readings. Spikes into the wrong
  range could cause unintended behavior.
    * Fixable by taking an average of sensor readings, or by waiting for multiple bad readings in a row.
* Nothing in the program currently stops the pump if the sensor were to die. The pump would
  continue to run unmonitored.
