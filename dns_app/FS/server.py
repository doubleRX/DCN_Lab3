import socket
from flask import Flask, request, jsonify

app = Flask(__name__)
PORT = 9090


def fibonacci(number):
    a, b = 0, 1

    for _ in range(number):
        a, b = b, a + b

    return a


@app.route("/register", methods=["PUT"])
def register():
    data = request.get_json(silent=True) or {}

    required = ["hostname", "ip", "as_ip", "as_port"]

    if any(field not in data for field in required):
        return jsonify({"error": "missing parameter"}), 400

    try:
        as_port = int(data["as_port"])
    except (TypeError, ValueError):
        return jsonify({"error": "invalid AS port"}), 400

    message = (
        "TYPE=A\n"
        f"NAME={data['hostname']} "
        f"VALUE={data['ip']} TTL=10\n"
    )

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)
        sock.sendto(message.encode(), (data["as_ip"], as_port))
        response, _ = sock.recvfrom(4096)
        sock.close()
    except Exception as error:
        return jsonify({"error": str(error)}), 500

    if not response.decode().startswith("TYPE=A"):
        return jsonify({"error": "AS registration failed"}), 500

    return jsonify({"status": "registered"}), 201


@app.route("/fibonacci", methods=["GET"])
def get_fibonacci():
    try:
        number = int(request.args["number"])

        if number < 0:
            raise ValueError

    except (KeyError, ValueError):
        return jsonify({"error": "number must be a non-negative integer"}), 400

    return str(fibonacci(number)), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
