import subprocess
import sense_hat

def stats(hat):
    while True:
        yield "T: %4.1f" % hat.temp
        yield "H: %4.1f" % hat.humidity
        yield "P: %4.0f" % hat.pressure
        yield "TP: %4.0f" % hat.get_temperature_from_pressure()
        yield "TH: %4.0f" % hat.pressure
        yield "P: %4.0f" % hat.pressure

def get_stats(hat):

    data = dict(
        temp = hat.temp,
        humidity = hat.humidity,
        pressure = hat.pressure,
        temperature_from_pressure = hat.get_temperature_from_pressure(),
        temperature_from_humidity = hat.get_temperature_from_humidity(),
        compass = hat.compass,
        cpu_temperature = get_cpu_temperature(),
        )
    data.update(hat.orientation)

    guess = data['temperature_from_pressure'] + data['temperature_from_humidity']
    guess = guess / 2.0

    cputemp = data['cpu_temperature']

    guess = guess - ((cputemp - guess) / 2)

    data['temperature_guess'] = guess

    return data

def get_cpu_temperature():

    result = subprocess.Popen('vcgencmd measure_temp'.split(), stdout=subprocess.PIPE)

    data = result.stdout.read()

    return float(data[5:-3])

def show_all_stats(hat, show=None):

    if show is None:
        show = hat.show_message

    while True:
        stats = get_stats(hat)

        for key, value in stats.items():
            show("%s: %04.1f\n" % (key, value))

if __name__ == '__main__':

    import datetime
    import csv
    import sys

    writer = csv.writer(sys.stdout)
    
    hat = sense_hat.SenseHat()
    stats = get_stats(hat)
    stats['timestamp'] = datetime.datetime.now()
    print(','.join(stats.keys()))
              
    while True:
        
        writer.writerow(stats.values())
        time.sleep(5)
        stats = get_stats(hat)
        stats['timestamp'] = datetime.datetime.now()

    
        

