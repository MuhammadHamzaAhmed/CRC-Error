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
    # Return physical interface data with full attributes matching real ACI API
    return jsonify({
        "totalCount": "1",
        "imdata": [
            {
                "l1PhysIf": {
                    "attributes": {
                        "adminSt": "up",
                        "autoNeg": "on",
                        "breakT": "nonbroken",
                        "bw": "0",
                        "childAction": "",
                        "delay": "1",
                        "descr": "",
                        "dfeDelayMs": "0",
                        "dn": "topology/pod-1/node-103/sys/phys-[eth1/33]",
                        "dot1qEtherType": "0x8100",
                        "emiRetrain": "disable",
                        "enablePoap": "no",
                        "ethpmCfgFailedBmp": "",
                        "ethpmCfgFailedTs": "00:00:00:00.000",
                        "ethpmCfgState": "0",
                        "fcotChannelNumber": "Channel32",
                        "fecMode": "inherit",
                        "id": "eth1/33",
                        "inhBw": "unspecified",
                        "isReflectiveRelayCfgSupported": "Supported",
                        "layer": "Layer2",
                        "lcOwn": "local",
                        "linkDebounce": "100",
                        "linkFlapErrorMax": "30",
                        "linkFlapErrorSeconds": "420",
                        "linkLog": "default",
                        "mdix": "auto",
                        "medium": "broadcast",
                        "modTs": "2024-08-31T03:12:10.501+03:00",
                        "mode": "trunk",
                        "monPolDn": "uni/infra/moninfra-default",
                        "mtu": "9000",
                        "name": "",
                        "pathSDescr": "",
                        "portPhyMediaType": "auto",
                        "portT": "leaf",
                        "prioFlowCtrl": "auto",
                        "reflectiveRelayEn": "off",
                        "routerMac": "not-applicable",
                        "snmpTrapSt": "enable",
                        "spanMode": "not-a-span-dest",
                        "speed": "inherit",
                        "status": "",
                        "switchingSt": "disabled",
                        "trunkLog": "default",
                        "usage": "discovery"
                    },
                    "children": [
                        {
                            "rmonEtherStats": {
                                "attributes": {
                                    "broadcastPkts": "0",
                                    "cRCAlignErrors": "0",
                                    "childAction": "",
                                    "clearTs": "2025-10-14T17:48:50.000+03:00",
                                    "collisions": "0",
                                    "dropEvents": "0",
                                    "fragments": "0",
                                    "jabbers": "0",
                                    "modTs": "never",
                                    "multicastPkts": "0",
                                    "octets": "0",
                                    "oversizePkts": "0",
                                    "pkts": "0",
                                    "pkts1024to1518Octets": "0",
                                    "pkts128to255Octets": "0",
                                    "pkts256to511Octets": "0",
                                    "pkts512to1023Octets": "0",
                                    "pkts64Octets": "0",
                                    "pkts65to127Octets": "0",
                                    "rXNoErrors": "0",
                                    "rn": "dbgEtherStats",
                                    "rxGiantPkts": "0",
                                    "rxOversizePkts": "0",
                                    "status": "",
                                    "tXNoErrors": "0",
                                    "txGiantPkts": "0",
                                    "txOversizePkts": "0",
                                    "undersizePkts": "0"
                                }
                            }
                        }
                    ]
                }
            }
        ]
    })


@app.route("/api/class/eqptIngrTotal15min.json", methods=["GET"])
def get_ingr_total():
    """Mock ingress total stats endpoint."""
    return jsonify({
        "totalCount": "2",
        "imdata": [
            {
                "eqptIngrTotal15min": {
                    "attributes": {
                        "bytesAvg": "2498437",
                        "bytesBase": "0",
                        "bytesCum": "48899803487750",
                        "bytesLast": "2935487",
                        "bytesMax": "2935487",
                        "bytesMin": "2061387",
                        "bytesPer": "4996874",
                        "bytesRate": "8328.109453",
                        "bytesRateAvg": "8328.277130",
                        "bytesRateLast": "9785.135220",
                        "bytesRateMax": "9785.135220",
                        "bytesRateMin": "6871.419039",
                        "bytesRateSpct": "0",
                        "bytesRateThr": "",
                        "bytesRateTr": "0.000000",
                        "bytesRateTrBase": "10390.215634",
                        "bytesRateTtl": "16656.554259",
                        "bytesSpct": "0",
                        "bytesThr": "",
                        "bytesTr": "0",
                        "bytesTrBase": "9435187",
                        "childAction": "",
                        "cnt": "2",
                        "dn": "topology/pod-1/node-103/sys/phys-[eth1/33]/CDeqptIngrTotal15min",
                        "lastCollOffset": "600",
                        "pktsAvg": "2674",
                        "pktsBase": "0",
                        "pktsCum": "36045395185",
                        "pktsLast": "3080",
                        "pktsMax": "3080",
                        "pktsMin": "2268",
                        "pktsPer": "5348",
                        "pktsRate": "8.913318",
                        "pktsRateAvg": "8.913427",
                        "pktsRateLast": "10.266746",
                        "pktsRateMax": "10.266746",
                        "pktsRateMin": "7.560107",
                        "pktsRateSpct": "0",
                        "pktsRateThr": "",
                        "pktsRateTr": "0.000000",
                        "pktsRateTrBase": "14.060335",
                        "pktsRateTtl": "17.826853",
                        "pktsSpct": "0",
                        "pktsThr": "",
                        "pktsTr": "0",
                        "pktsTrBase": "12695",
                        "repIntvEnd": "2026-01-21T09:09:58.735+03:00",
                        "repIntvStart": "2026-01-21T08:59:58.734+03:00",
                        "status": "",
                        "utilAvg": "0",
                        "utilLast": "0",
                        "utilMax": "0",
                        "utilMin": "0",
                        "utilSpct": "0",
                        "utilThr": "",
                        "utilTr": "0",
                        "utilTrBase": "0",
                        "utilTtl": "0"
                    }
                }
            },
            {
                "eqptIngrTotal15min": {
                    "attributes": {
                        "bytesAvg": "1500000",
                        "bytesBase": "0",
                        "bytesCum": "25000000000",
                        "bytesLast": "1600000",
                        "bytesMax": "1600000",
                        "bytesMin": "1400000",
                        "bytesPer": "3000000",
                        "bytesRate": "5000.000000",
                        "bytesRateAvg": "5000.000000",
                        "bytesRateLast": "5333.333333",
                        "bytesRateMax": "5333.333333",
                        "bytesRateMin": "4666.666667",
                        "bytesRateSpct": "0",
                        "bytesRateThr": "",
                        "bytesRateTr": "0.000000",
                        "bytesRateTrBase": "6000.000000",
                        "bytesRateTtl": "10000.000000",
                        "bytesSpct": "0",
                        "bytesThr": "",
                        "bytesTr": "0",
                        "bytesTrBase": "5000000",
                        "childAction": "",
                        "cnt": "2",
                        "dn": "topology/pod-2/node-2212/sys/aggr-[po1]/CDeqptIngrTotal15min",
                        "lastCollOffset": "600",
                        "pktsAvg": "1500",
                        "pktsBase": "0",
                        "pktsCum": "20000000000",
                        "pktsLast": "1700",
                        "pktsMax": "1700",
                        "pktsMin": "1300",
                        "pktsPer": "3000",
                        "pktsRate": "5.000000",
                        "pktsRateAvg": "5.000000",
                        "pktsRateLast": "5.666667",
                        "pktsRateMax": "5.666667",
                        "pktsRateMin": "4.333333",
                        "pktsRateSpct": "0",
                        "pktsRateThr": "",
                        "pktsRateTr": "0.000000",
                        "pktsRateTrBase": "8.000000",
                        "pktsRateTtl": "10.000000",
                        "pktsSpct": "0",
                        "pktsThr": "",
                        "pktsTr": "0",
                        "pktsTrBase": "7000",
                        "repIntvEnd": "2026-01-21T09:09:58.735+03:00",
                        "repIntvStart": "2026-01-21T08:59:58.734+03:00",
                        "status": "",
                        "utilAvg": "0",
                        "utilLast": "0",
                        "utilMax": "0",
                        "utilMin": "0",
                        "utilSpct": "0",
                        "utilThr": "",
                        "utilTr": "0",
                        "utilTrBase": "0",
                        "utilTtl": "0"
                    }
                }
            }
        ]
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
