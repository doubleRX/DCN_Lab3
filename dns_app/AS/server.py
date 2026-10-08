import json
import os
import socket
import threading

HOST = "0.0.0.0"
PORT = 53533
DB_FILE = os.path.join(os.path.dirname(__file__), "records.json")

lock = threading.Lock()


def load_records():
    try:
        with open(DB_FILE, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_records(records):
    with open(DB_FILE, "w") as file:
        json.dump(records, file, indent=2)


def make_response(name, record):
    return (
        "TYPE=A\n"
        f"NAME={name} VALUE={record['value']} TTL={record['ttl']}\n"
    )


records = load_records()

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((HOST, PORT))

print(f"AS is listening on UDP port {PORT}")

while True:
    data, address = sock.recvfrom(4096)
    message = data.decode().strip()

    print(f"Received from {address}:")
    print(message)

    fields = {}

    for part in message.replace("\n", " ").split():
        if "=" in part:
            key, value = part.split("=", 1)
            fields[key] = value

    if fields.get("TYPE") != "A" or "NAME" not in fields:
        sock.sendto(b"ERROR\n", address)
        continue

    name = fields["NAME"]

    # Registration request
    if "VALUE" in fields and "TTL" in fields:
        record = {
            "value": fields["VALUE"],
            "ttl": int(fields["TTL"])
        }

        with lock:
            records[name] = record
            save_records(records)

        response = make_response(name, record)
        print(f"Registered {name} -> {record['value']}")

    # DNS query
    else:
        with lock:
            record = records.get(name)

        if record is None:
            response = "ERROR\n"
        else:
            response = make_response(name, record)

    sock.sendto(response.encode(), address)
