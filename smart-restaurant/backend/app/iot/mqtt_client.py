"""MQTT connection helpers for restaurant devices (Mosquitto -> delivery robot)."""
import json
import logging
import os
import threading

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("mqtt")

# Audit Req 4: default to the LAN broker IP so the ESP32 on the network can
# reach the same broker the backend publishes to. Override via environment.
MQTT_BROKER_HOST = os.getenv("MQTT_BROKER_HOST", "10.66.49.162")
MQTT_BROKER_PORT = int(os.getenv("MQTT_BROKER_PORT", "1883"))
# Audit Req 2: must match the robot subscription character-for-character.
MQTT_ROBOT_COMMAND_TOPIC = os.getenv("MQTT_ROBOT_COMMAND_TOPIC", "restaurant/robot/command")

# How long publish/connect waits for the broker CONNACK before giving up.
MQTT_CONNECT_TIMEOUT = float(os.getenv("MQTT_CONNECT_TIMEOUT", "5"))
# How long publish waits for the QoS1 PUBACK before healing + retrying once.
MQTT_PUBLISH_TIMEOUT = float(os.getenv("MQTT_PUBLISH_TIMEOUT", "5"))

_client = None
_client_connected = False
_lock = threading.Lock()
_connected_event = threading.Event()

try:
    import paho.mqtt.client as mqtt
except ImportError:  # pragma: no cover - handled gracefully at publish time
    mqtt = None
    logger.warning("paho-mqtt is not installed. Run: pip install paho-mqtt")


def _on_connect(client, userdata, flags, rc, properties=None):
    global _client_connected
    _client_connected = (rc == 0)
    if rc == 0:
        _connected_event.set()
        logger.info("Connected to Mosquitto broker at %s:%s", MQTT_BROKER_HOST, MQTT_BROKER_PORT)
    else:
        _connected_event.clear()
        logger.error("Failed to connect to Mosquitto broker (rc=%s)", rc)


def _on_disconnect(client, userdata, flags, rc, properties=None):
    global _client_connected
    _client_connected = False
    _connected_event.clear()
    logger.warning("Disconnected from Mosquitto broker (rc=%s)", rc)


def _build_client():
    """Creates a paho client compatible with both v1.x and v2.x APIs."""
    if mqtt is None:
        raise RuntimeError("paho-mqtt is not installed. Run: pip install paho-mqtt")
    try:
        # paho-mqtt >= 2.0 requires an explicit callback API version.
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1)
    except (TypeError, AttributeError):
        client = mqtt.Client()
    client.on_connect = _on_connect
    client.on_disconnect = _on_disconnect
    # Auto-reconnect with backoff so a broker restart heals itself.
    try:
        client.reconnect_delay_set(min_delay=1, max_delay=30)
    except Exception:  # pragma: no cover - old paho without backoff API
        pass
    return client


def _new_connected_client():
    """Builds, connects and starts the network loop for a fresh client.

    Must be called with ``_lock`` held (see :func:`get_mqtt_client` and
    :func:`_force_reconnect`). Clears the CONNACK event first so no other
    thread can publish on the half-open socket this replaces.
    """
    global _client
    # Drop any dead instance before rebuilding.
    old = _client
    _client = None
    if old is not None:
        try:
            old.loop_stop()
        except Exception:
            pass
        try:
            old.disconnect()
        except Exception:
            pass
    _connected_event.clear()
    client = _build_client()
    # connect() is async once the loop runs; loop_start() performs CONNACK.
    client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, keepalive=60)
    client.loop_start()
    _client = client
    return client


def _is_live(client) -> bool:
    """True only if paho reports connected AND we saw a CONNACK (rc=0)."""
    try:
        return bool(client.is_connected()) and _connected_event.is_set()
    except Exception:
        return False


def _force_reconnect(wait_sec: float | None = None) -> object:
    """Drops the stale singleton, rebuilds it, and waits for CONNACK.

    Used when publish returns MQTT_ERR_NO_CONN (rc=4) or the socket looks
    half-open. Raises ConnectionError if the broker stays unreachable.
    """
    if wait_sec is None:
        wait_sec = MQTT_CONNECT_TIMEOUT
    with _lock:
        _new_connected_client()
        client = _client
    if not _connected_event.wait(timeout=wait_sec):
        try:
            if client is not None and client.is_connected():
                return client
        except Exception:
            pass
        raise ConnectionError(
            f"MQTT broker unreachable at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT} "
            f"(no CONNACK within {wait_sec}s)"
        )
    return client


def get_mqtt_client(wait_sec: float | None = None):
    """Returns a connected singleton client (10.66.49.162:1883 by default).

    Blocks up to ``wait_sec`` for the CONNACK so callers never publish on a
    half-open socket (the old "client is not currently connected" race).
    Heals a stale singleton: reconnects or rebuilds if the socket dropped.
    Raises the last connection error if the broker stays unreachable.
    """
    if wait_sec is None:
        wait_sec = MQTT_CONNECT_TIMEOUT
    with _lock:
        if _client is not None:
            try:
                if _client.is_connected() and _connected_event.is_set():
                    return _client
                # Socket dropped but object alive: try a clean reconnect first.
                try:
                    _client.reconnect()
                except Exception:
                    _new_connected_client()
            except Exception:
                # Reconnect path failed -> rebuild from scratch (may raise).
                _new_connected_client()
        else:
            _new_connected_client()
        client = _client
    # Wait for CONNACK outside the lock so requests don't serialize.
    if not _connected_event.wait(timeout=wait_sec):
        try:
            if client.is_connected():
                return client
        except Exception:
            pass
        raise ConnectionError(
            f"MQTT broker unreachable at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT} "
            f"(no CONNACK within {wait_sec}s)"
        )
    return client


def connect_mqtt(wait_sec: float | None = None) -> bool:
    """Eagerly connects the singleton. Safe to call on FastAPI startup."""
    try:
        get_mqtt_client(wait_sec=wait_sec)
        return True
    except Exception as exc:
        logger.error("MQTT pre-connect failed (%s:%s): %s", MQTT_BROKER_HOST, MQTT_BROKER_PORT, exc)
        return False


def disconnect_mqtt() -> None:
    """Stops the network loop and disconnects (FastAPI shutdown)."""
    global _client
    with _lock:
        client, _client = _client, None
    _connected_event.clear()
    if client is not None:
        try:
            client.loop_stop()
        except Exception:
            pass
        try:
            client.disconnect()
        except Exception:
            pass


def publish_robot_command(table_number: int, order_id: int | None = None) -> bool:
    """Publishes NAVIGATE_TO_TABLE to 'restaurant/robot/command'.

    Audit Req 3: payload is exactly:
        {"action": "NAVIGATE_TO_TABLE", "tableNumber": <int>}
    `order_id` is accepted only for log correlation and is NEVER published,
    so strict ESP32 parsers expecting 2 keys keep working.

    Self-healing: if the singleton socket is stale (publish rc=4
    MQTT_ERR_NO_CONN, half-open socket, or QoS1 PUBACK timeout) the client
    is rebuilt, CONNACK awaited, and the publish retried exactly once.

    Fail-open: returns False (logs only) if the broker is unreachable so an
    order update never fails because of MQTT.
    """
    try:
        table_int = int(table_number)
    except (TypeError, ValueError):
        logger.error("Refusing robot publish: invalid table_number=%r order_id=%r", table_number, order_id)
        return False
    if table_int <= 0:
        logger.error("Refusing robot publish: table_number must be > 0, got %r", table_number)
        return False
    payload = {
        "action": "NAVIGATE_TO_TABLE",
        "tableNumber": table_int,
    }
    message = json.dumps(payload)

    def _try_publish(client, attempt: int) -> str | None:
        """One publish attempt. Returns None on success, else reason string."""
        # Belt-and-braces: never publish on a half-open socket.
        # BOTH checks are required: paho state AND the CONNACK event. The old
        # code only checked is_connected() when the event was clear, so a
        # stale set() event let publish run on a dead socket -> rc=4.
        if not _is_live(client):
            return "not-connected"
        try:
            result = client.publish(MQTT_ROBOT_COMMAND_TOPIC, message, qos=1)
        except Exception as exc:
            return f"publish-raised: {exc}"
        # paho returns MQTTMessageInfo with .rc; non-success means not queued.
        rc = getattr(result, "rc", mqtt.MQTT_ERR_SUCCESS if mqtt else 0)
        if mqtt is not None and rc != mqtt.MQTT_ERR_SUCCESS:
            return f"publish rc={rc}"
        try:
            result.wait_for_publish(timeout=MQTT_PUBLISH_TIMEOUT)
        except Exception as exc:
            return f"wait_for_publish raised: {exc}"
        try:
            published = result.is_published()
        except Exception:
            published = True  # old paho without is_published(); rc==0 is enough
        if not published:
            return "timed out waiting for PUBACK"
        return None

    try:
        client = get_mqtt_client()
        reason = _try_publish(client, attempt=1)
        if reason is not None:
            # rc=4 / not-connected / PUBACK timeout -> heal + retry once.
            logger.warning(
                "Robot publish attempt 1 failed (%s); reconnecting %s:%s and retrying (order_id=%s)",
                reason,
                MQTT_BROKER_HOST,
                MQTT_BROKER_PORT,
                order_id,
            )
            client = _force_reconnect()
            reason = _try_publish(client, attempt=2)
        if reason is not None:
            logger.error(
                "Failed to publish robot command %s after retry (%s) (order_id=%s)",
                payload,
                reason,
                order_id,
            )
            return False
        logger.info(
            "Published robot command to %s: %s (order_id=%s)",
            MQTT_ROBOT_COMMAND_TOPIC,
            message,
            order_id,
        )
        return True
    except Exception as exc:  # pragma: no cover - broker-down path
        logger.error(
            "Failed to publish robot command %s: %s (broker %s:%s, order_id=%s)",
            payload,
            exc,
            MQTT_BROKER_HOST,
            MQTT_BROKER_PORT,
            order_id,
        )
        return False


def mqtt_status() -> dict:
    """Snapshot for GET /health/mqtt: effective broker config + live state."""
    client = _client
    try:
        paho_connected = bool(client.is_connected()) if client is not None else False
    except Exception:
        paho_connected = False
    live = bool(paho_connected and _connected_event.is_set())
    return {
        "host": MQTT_BROKER_HOST,
        "port": MQTT_BROKER_PORT,
        "topic": MQTT_ROBOT_COMMAND_TOPIC,
        "connected": live,
        "paho_connected": paho_connected,
        "conack_received": _connected_event.is_set(),
        "publish_timeout_sec": MQTT_PUBLISH_TIMEOUT,
        "connect_timeout_sec": MQTT_CONNECT_TIMEOUT,
    }

