import asyncio
import os
import uuid
from flask import Flask, request, jsonify
from temporalio.client import Client

from props import TEMPORAL_QUEUE
from workflow import CrcErrorWorkflow
from activities import WorkflowInput

app = Flask(__name__)

# Temporal client (initialized lazily)
_client = None


async def get_client():
    global _client
    if _client is None:
        temporal_host = os.environ.get("TEMPORAL_HOST", "localhost:7233")
        _client = await Client.connect(temporal_host)
    return _client


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})


@app.route("/workflow/start", methods=["POST"])
def start_workflow():
    """
    Start a new CRC Error workflow.

    Request body:
    {
        "ip": "192.168.1.1",
        "protocol": "http",  // optional, defaults to "https"
        "workflow_id": "optional-custom-id"
    }
    """
    data = request.get_json()

    if not data or "ip" not in data:
        return jsonify({"error": "Missing 'ip' in request body"}), 400

    ip = data["ip"]
    protocol = data.get("protocol", "https")
    workflow_id = data.get("workflow_id", f"crc-error-{uuid.uuid4()}")

    async def _start():
        client = await get_client()
        handle = await client.start_workflow(
            CrcErrorWorkflow.run,
            WorkflowInput(ip=ip, protocol=protocol),
            id=workflow_id,
            task_queue=TEMPORAL_QUEUE,
        )
        return handle.id

    try:
        wf_id = asyncio.run(_start())
        return jsonify({
            "message": "Workflow started",
            "workflow_id": wf_id,
            "input": {"ip": ip, "protocol": protocol}
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/workflow/<workflow_id>/status", methods=["GET"])
def get_workflow_status(workflow_id):
    """Get the status of a workflow."""
    async def _get_status():
        client = await get_client()
        handle = client.get_workflow_handle(workflow_id)
        desc = await handle.describe()
        return {
            "workflow_id": workflow_id,
            "status": desc.status.name,
            "start_time": desc.start_time.isoformat() if desc.start_time else None,
            "close_time": desc.close_time.isoformat() if desc.close_time else None,
        }

    try:
        status = asyncio.run(_get_status())
        return jsonify(status)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/workflow/<workflow_id>/result", methods=["GET"])
def get_workflow_result(workflow_id):
    """Get the result of a completed workflow."""
    async def _get_result():
        client = await get_client()
        handle = client.get_workflow_handle(workflow_id)
        result = await handle.result()
        return result

    try:
        result = asyncio.run(_get_result())
        return jsonify({
            "workflow_id": workflow_id,
            "result": result
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/workflow/<workflow_id>/cancel", methods=["POST"])
def cancel_workflow(workflow_id):
    """Cancel a running workflow."""
    async def _cancel():
        client = await get_client()
        handle = client.get_workflow_handle(workflow_id)
        await handle.cancel()

    try:
        asyncio.run(_cancel())
        return jsonify({
            "message": "Workflow cancelled",
            "workflow_id": workflow_id
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("API_PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
