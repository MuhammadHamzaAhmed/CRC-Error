"""
Mock ACI Server for testing Temporal workflows locally.
This simulates the Cisco ACI API responses.
"""
import os
from flask import Flask, request, jsonify

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
    # Return dummy physical interface data with CRC errors
    return jsonify({
        "imdata": [
            {
                "l1PhysIf": {
                    "attributes": {
                        "dn": "topology/pod-1/node-101/sys/phys-[eth1/1]",
                        "id": "eth1/1",
                        "adminSt": "up",
                        "operSt": "up"
                    },
                    "children": [
                        {
                            "rmonEtherStats": {
                                "attributes": {
                                    "cRCAlignErrors": "150",
                                    "collisions": "0"
                                }
                            }
                        }
                    ]
                }
            },
            {
                "l1PhysIf": {
                    "attributes": {
                        "dn": "topology/pod-1/node-101/sys/phys-[eth1/2]",
                        "id": "eth1/2",
                        "adminSt": "up",
                        "operSt": "up"
                    },
                    "children": [
                        {
                            "rmonEtherStats": {
                                "attributes": {
                                    "cRCAlignErrors": "0",
                                    "collisions": "0"
                                }
                            }
                        }
                    ]
                }
            },
            {
                "l1PhysIf": {
                    "attributes": {
                        "dn": "topology/pod-1/node-101/sys/phys-[eth1/3]",
                        "id": "eth1/3",
                        "adminSt": "up",
                        "operSt": "down"
                    },
                    "children": [
                        {
                            "rmonEtherStats": {
                                "attributes": {
                                    "cRCAlignErrors": "500",
                                    "collisions": "10"
                                }
                            }
                        }
                    ]
                }
            }
        ],
        "totalCount": "3"
    })


@app.route("/api/class/eqptIngrTotal15min.json", methods=["GET"])
def get_ingr_total():
    """Mock ingress total stats endpoint."""
    return jsonify({
        "imdata": [
            {
                "eqptIngrTotal15min": {
                    "attributes": {
                        "dn": "topology/pod-1/node-101/sys/phys-[eth1/1]/HDeqptIngrTotal15min",
                        "pktsRateMin": "1000",
                        "pktsRateMax": "5000",
                        "pktsRateAvg": "2500"
                    }
                }
            },
            {
                "eqptIngrTotal15min": {
                    "attributes": {
                        "dn": "topology/pod-1/node-101/sys/phys-[eth1/2]/HDeqptIngrTotal15min",
                        "pktsRateMin": "500",
                        "pktsRateMax": "3000",
                        "pktsRateAvg": "1500"
                    }
                }
            },
            {
                "eqptIngrTotal15min": {
                    "attributes": {
                        "dn": "topology/pod-1/node-101/sys/phys-[eth1/3]/HDeqptIngrTotal15min",
                        "pktsRateMin": "0",
                        "pktsRateMax": "100",
                        "pktsRateAvg": "50"
                    }
                }
            }
        ],
        "totalCount": "3"
    })


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "server": "mock-aci"})


if __name__ == "__main__":
    port = int(os.environ.get("MOCK_ACI_PORT", 8080))
    print(f"Starting Mock ACI Server on port {port}")
    print("Available endpoints:")
    print("  POST /api/aaaLogin.json")
    print("  GET  /api/node/class/l1PhysIf.json")
    print("  GET  /api/class/eqptIngrTotal15min.json")
    print("  GET  /health")
    app.run(host="0.0.0.0", port=port, debug=True)
