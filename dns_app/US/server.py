import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from flask import Flask, jsonify, request

app = Flask(__name__)
PORT = 8080


def parse_dns_response(message):
    fields = {}

    for part in message.replace("\n", " ").split():
        if "=" in part:
            key, value = part.split("=", 1)
            fields[key] = value

    if fields.get("TYPE") != "A" or "VALUE" not in fields:
        raise ValueError("invalid AS response")

    return fields["VALUE"]


@app.route("/fibonacci", methods=["GET"])
def get_fibonacci():
    required = ["hostname", "fs_port", "number", "as_ip", "as_port"]

    if any(request.args.get(field) in (None, "") for field in required):
        return jsonify({"error": "missing parameter"}), 400

    hostname = request.args["hostname"]
    number = request.args["number"]

    try:
        fs_port = int(request.args["fs_port"])
        as_port = int(request.args["as_port"])
    except ValueError:
        return jsonify({"error": "invalid port"}), 400

    dns_query = f"TYPE=A\nNAME={hostname}\n"

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(3)
            sock.sendto(
                dns_query.encode(),
                (request.args["as_ip"], as_port)
            )
            data, _ = sock.recvfrom(4096)

        fs_ip = parse_dns_response(data.decode())

    except Exception as error:
        return jsonify({"error": f"AS query failed: {error}"}), 502

    fs_url = (
        f"http://{fs_ip}:{fs_port}/fibonacci?"
        f"{urlencode({'number': number})}"
    )

    try:
        with urlopen(fs_url, timeout=3) as response:
            body = response.read().decode()
            return body, response.status, {
                "Content-Type": "text/plain"
            }

    except HTTPError as error:
        body = error.read().decode()
        return body, error.code

    except URLError as error:
        return jsonify({"error": f"FS request failed: {error}"}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
