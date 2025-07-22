import re
import struct
from datetime import datetime


def decode_response(response_text):
    lines = response_text.split('\n')

    # 1. station info
    station_match = re.search(r'([^*]+)\*STATION', response_text)
    station_name = station_match.group(1) if station_match else "Unknown"

    # 2. schedule times
    schedule_pattern = r'(\d{2})(\d{10,})R'
    schedules = []

    for match in re.finditer(schedule_pattern, response_text):
        hour = int(match.group(1))
        minutes_string = match.group(2)

        # parse minutes: every 2 digits represent a departure time
        minutes = []
        for i in range(0, len(minutes_string), 2):
            if i + 1 < len(minutes_string):
                minute = int(minutes_string[i:i+2])
                if minute < 60: # valid minute
                    minutes.append(f'{hour:02d}:{minute:02d}')

        schedules.extend(minutes)

    # 3. bus positions (real-time)
    bus_pattern = rb'(.{8})F@(.{8}):@"BUS"' # coordinates + F@ + coordinates + :@ + "BUS"

    buses = []
    response_bytes = response_text.encode('latin1', errors='ignore')

    for match in re.finditer(bus_pattern, response_bytes):
        try:
            lat_bytes = match.group(1)
            lng_bytes = match.group(2)

            # decode as IEEE 754 double precision
            lat = struct.unpack('<d', lat_bytes)[0]
            lng = struct.unpack('<d', lng_bytes)[0]

            buses.append({
                'latitude': lat,
                'longitude': lng,
                'timestamp': datetime.utcnow().isoformat()
            })

        except struct.error:
            continue

    return {
        'station_name': station_name.strip(),
        'collection_time': datetime.utcnow().isoformat(),
        'scheduled_departures': schedules,
        'real_time_buses': buses,
        'total_active_buses': len(buses)
    }


with open('bus_data.txt', 'r') as f:
    response = f.read()

result = decode_response(response)
print(result)
