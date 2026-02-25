"""
Mock ACI Server for testing Temporal workflows locally.
This simulates the Cisco ACI API responses.
"""
import os
from flask import Flask, request, jsonify
import json

app = Flask(__name__)


@app.route("/api/aaaLogin.json", methods=["POST"])
def login():
    """Mock login endpoint."""
    data = request.get_json()

    # Validate request structure
    if not data or "aaaUser" not in data:
        return jsonify({
            "imdata": [],
            "totalCount": "0"
        }), 401

    # Return successful login response
    return jsonify({
        "imdata": [
            {
                "aaaLogin": {
                    "attributes": {
                        "token": "mock-token-12345",
                        "refreshTimeoutSeconds": "600",
                        "maximumLifetimeSeconds": "86400"
                    }
                }
            }
        ],
        "totalCount": "1"
    })


@app.route("/api/node/class/l1PhysIf.json", methods=["GET"])
def get_phys_if():
    """Mock physical interfaces endpoint."""
    data = json.load(open('phy.json', 'r'))
    return jsonify(data)


@app.route("/api/class/eqptIngrTotal15min.json", methods=["GET"])
def get_ingr_total():
    """Mock ingress total stats endpoint."""
    data = json.load(open('ingr.json', 'r'))
    return jsonify(data)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "server": "mock-aci"})


if __name__ == "__main__":
    port = int(os.environ.get("MOCK_ACI_PORT", 5000))
    print(f"Starting Mock ACI Server on port {port}")
    print("Available endpoints:")
    print("  POST /api/aaaLogin.json")
    print("  GET  /api/node/class/l1PhysIf.json")
    print("  GET  /api/class/eqptIngrTotal15min.json")
    print("  GET  /health")
    app.run(host="0.0.0.0", port=port, debug=True)
