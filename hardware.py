# ============================================================
# A818SN - HARDWARE INTERFACE
# LOCAL ONLY - DO NOT PUSH TO GITHUB
# ============================================================
# Single entry point: execute(lat, lon, hob_km)
# ============================================================

import time
import threading
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional


# ============================================================
# LOGGING
# ============================================================
logger = logging.getLogger("A818SN_HARDWARE")
logger.setLevel(logging.INFO)
if not logger.handlers:
    _handler = logging.FileHandler("hardware_log.txt", encoding="utf-8")
    _handler.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    ))
    logger.addHandler(_handler)


# ============================================================
# CONFIGURATION
# ============================================================
@dataclass
class HardwareConfig:
    port: str = "COM3"
    baudrate: int = 115200
    expected_device_id: str = "A818SN-EMP-01"
    min_firmware: str = "1.0"
    read_timeout_s: float = 2.0
    connect_timeout_s: float = 5.0
    arm_timeout_s: float = 30.0
    fire_timeout_s: float = 15.0
    cooldown_s: float = 30.0
    charge_timeout_s: float = 60.0
    max_hob_km: float = 500.0
    min_hob_km: float = 30.0
    max_lat: float = 90.0
    min_lat: float = -90.0
    max_lon: float = 180.0
    min_lon: float = -180.0


# ============================================================
# STATE MACHINE
# ============================================================
class State(Enum):
    IDLE = "IDLE"
    CONNECTED = "CONNECTED"
    CHARGING = "CHARGING"
    READY = "READY"
    ARMED = "ARMED"
    FIRING = "FIRING"
    COOLDOWN = "COOLDOWN"
    FAULT = "FAULT"
    ESTOP = "ESTOP"


# ============================================================
# EXCEPTIONS
# ============================================================
class HardwareError(Exception): pass
class NotConnectedError(HardwareError): pass
class HandshakeError(HardwareError): pass
class InterlockOpenError(HardwareError): pass
class ChargeFailedError(HardwareError): pass
class FireRejectedError(HardwareError): pass
class EmergencyStopError(HardwareError): pass
class BusyError(HardwareError): pass


# ============================================================
# RESULT
# ============================================================
@dataclass
class FireResult:
    success: bool
    state_before: str
    state_after: str
    target_lat: float
    target_lon: float
    hob_km: float
    hardware_response: str
    error: Optional[str] = None
    duration_s: float = 0.0


# ============================================================
# CONTROLLER
# ============================================================
class EMPController:
    """
    Single-button hardware interface.
    GUI calls: controller.execute(lat, lon, hob_km)
    """

    def __init__(self, config: Optional[HardwareConfig] = None):
        self.config = config or HardwareConfig()
        self.serial = None
        self.state = State.IDLE
        self.device_id = None
        self.firmware = None
        self.armed_at = 0.0
        self.last_fire_at = 0.0
        self.estop_latched = False

        # Thread safety
        self._lock = threading.RLock()
        self._io_lock = threading.Lock()
        self._busy = False
        self._rx_buffer = b""
        self._shutdown = False

    # ========================================================
    # PUBLIC: SINGLE ENTRY POINT
    # ========================================================
    def execute(self, target_lat: float,
                target_lon: float,
                hob_km: float) -> FireResult:
        start = time.time()

        with self._lock:
            if self._busy:
                return self._result_fail(
                    target_lat, target_lon, hob_km,
                    "Busy: another execute() in progress",
                    start
                )
            self._busy = True
            state_before = self.state.value

        try:
            # 1. Pre-flight validation
            self._validate_inputs(target_lat, target_lon, hob_km)

            # 2. Connect (resets device_id if new connection)
            with self._lock:
                if self.state in (State.IDLE, State.FAULT):
                    self._connect()

            # 3. Handshake
            self._handshake()

            # 4. Interlocks
            self._check_interlocks()

            # 5. Charge
            self._charge()

            # 6. Arm
            self._arm()

            # 7. Fire
            response = self._fire(target_lat, target_lon, hob_km)

            # 8. Cooldown
            self._cooldown()

            with self._lock:
                state_after = self.state.value

            return FireResult(
                success=True,
                state_before=state_before,
                state_after=state_after,
                target_lat=target_lat,
                target_lon=target_lon,
                hob_km=hob_km,
                hardware_response=response,
                duration_s=time.time() - start
            )

        except EmergencyStopError as e:
            with self._lock:
                self.state = State.ESTOP
                self.estop_latched = True
            return self._result_fail(
                target_lat, target_lon, hob_km, str(e), start,
                code="ESTOP"
            )

        except HardwareError as e:
            with self._lock:
                if self.state not in (State.ESTOP, State.FAULT):
                    self.state = State.FAULT
            return self._result_fail(
                target_lat, target_lon, hob_km, str(e), start,
                code="FAULT"
            )

        except KeyboardInterrupt:
            self.emergency_stop()
            return self._result_fail(
                target_lat, target_lon, hob_km,
                "User interrupt - emergency stop", start,
                code="ESTOP"
            )

        except Exception as e:
            logger.exception("Unexpected error")
            with self._lock:
                self.state = State.FAULT
            return self._result_fail(
                target_lat, target_lon, hob_km,
                f"Unexpected: {e}", start,
                code="FAULT"
            )

        finally:
            with self._lock:
                self._busy = False

    # ========================================================
    # PUBLIC: EMERGENCY STOP (thread-safe, callable anytime)
    # ========================================================
    def emergency_stop(self):
        with self._lock:
            self.estop_latched = True
            self.state = State.ESTOP
        # Fire ESTOP to hardware outside the lock (avoid deadlock)
        if self.serial and getattr(self.serial, "is_open", False):
            try:
                with self._io_lock:
                    self.serial.write(b"ESTOP\n")
                    self.serial.flush()
            except Exception:
                pass
        logger.critical("EMERGENCY STOP LATCHED")

    # ========================================================
    # PUBLIC: RECOVER FROM FAULT
    # ========================================================
    def recover(self) -> bool:
        with self._lock:
            if self.estop_latched:
                logger.error("Cannot recover: ESTOP latched. Physical reset required.")
                return False
            if self.state != State.FAULT:
                return True
            try:
                if self.serial and getattr(self.serial, "is_open", False):
                    self._send("RESET")
                self.state = State.CONNECTED
                logger.info("Recovered from FAULT")
                return True
            except Exception as e:
                logger.error(f"Recovery failed: {e}")
                return False

    # ========================================================
    # PUBLIC: STATUS
    # ========================================================
    def status(self) -> dict:
        with self._lock:
            return {
                "state": self.state.value,
                "connected": self.serial is not None and getattr(self.serial, "is_open", False),
                "armed": self.state == State.ARMED,
                "estop_latched": self.estop_latched,
                "device_id": self.device_id,
                "firmware": self.firmware,
                "cooldown_remaining": max(
                    0.0,
                    self.config.cooldown_s - (time.time() - self.last_fire_at)
                )
            }

    # ========================================================
    # PUBLIC: CLOSE
    # ========================================================
    def close(self):
        with self._lock:
            self._shutdown = True
            if self.serial and getattr(self.serial, "is_open", False):
                try:
                    with self._io_lock:
                        self.serial.write(b"DISARM\n")
                        self.serial.flush()
                        time.sleep(0.2)
                except Exception:
                    pass
                try:
                    self.serial.close()
                except Exception:
                    pass
            self.serial = None
            self.state = State.IDLE
            self.device_id = None
            self.firmware = None
        logger.info("Controller closed")

    # ========================================================
    # INTERNAL: INPUT VALIDATION
    # ========================================================
    def _validate_inputs(self, lat, lon, hob):
        with self._lock:
            if self.estop_latched:
                raise EmergencyStopError(
                    "Emergency stop latched. Physical reset required."
                )
        if not (self.config.min_lat <= lat <= self.config.max_lat):
            raise HardwareError(f"Invalid latitude: {lat}")
        if not (self.config.min_lon <= lon <= self.config.max_lon):
            raise HardwareError(f"Invalid longitude: {lon}")
        if not (self.config.min_hob_km <= hob <= self.config.max_hob_km):
            raise HardwareError(
                f"HOB {hob} km outside legal range "
                f"[{self.config.min_hob_km}, {self.config.max_hob_km}]"
            )

    # ========================================================
    # INTERNAL: CONNECT
    # ========================================================
    def _connect(self):
        try:
            import serial
        except ImportError:
            raise HardwareError("pyserial not installed. Run: pip install pyserial")

        # Reset handshake state on every new connection
        with self._lock:
            self.device_id = None
            self.firmware = None

        try:
            self.serial = serial.Serial(
                port=self.config.port,
                baudrate=self.config.baudrate,
                timeout=self.config.read_timeout_s,
                write_timeout=self.config.read_timeout_s
            )
            time.sleep(2.0)
            self._rx_buffer = b""
            with self._lock:
                self.state = State.CONNECTED
            logger.info(f"Connected to {self.config.port}")
        except Exception as e:
            # Clean up partial connection
            if self.serial:
                try:
                    self.serial.close()
                except Exception:
                    pass
                self.serial = None
            with self._lock:
                self.state = State.FAULT
            raise HardwareError(f"Serial connect failed: {e}")

    # ========================================================
    # INTERNAL: HANDSHAKE
    # ========================================================
    def _handshake(self):
        with self._lock:
            if self.device_id is not None:
                return

        response = self._send("HELLO", timeout=self.config.connect_timeout_s)
        # Expected: "HARDWARE A818SN-EMP-01 FW:1.2 SN:12345"
        parts = response.split()
        if not parts or parts[0].upper() != "HARDWARE":
            raise HandshakeError(f"Bad handshake response: {response}")

        try:
            dev_id = parts[1]
            fw = next(
                (p.split(":", 1)[1] for p in parts if p.startswith("FW:")),
                "?"
            )
        except (IndexError, ValueError):
            raise HandshakeError(f"Malformed handshake: {response}")

        if dev_id != self.config.expected_device_id:
            raise HandshakeError(
                f"Device ID mismatch. Expected "
                f"{self.config.expected_device_id}, got {dev_id}"
            )

        # Firmware version check
        if fw != "?":
            try:
                cur = tuple(int(x) for x in fw.split("."))
                minv = tuple(int(x) for x in self.config.min_firmware.split("."))
                if cur < minv:
                    raise HandshakeError(
                        f"Firmware {fw} below minimum "
                        f"{self.config.min_firmware}"
                    )
            except ValueError:
                pass  # non-numeric firmware string, skip check

        with self._lock:
            self.device_id = dev_id
            self.firmware = fw
        logger.info(f"Handshake OK: {dev_id} FW {fw}")

    # ========================================================
    # INTERNAL: INTERLOCKS
    # ========================================================
    def _check_interlocks(self):
        response = self._send("STATUS")
        if "INTERLOCKS=CLOSED" not in response.upper():
            raise InterlockOpenError(f"Interlock open: {response}")
        logger.info(f"Interlocks OK: {response}")

    # ========================================================
    # INTERNAL: CHARGE
    # ========================================================
    def _charge(self):
        with self._lock:
            self.state = State.CHARGING
        response = self._send("CHARGE", timeout=self.config.charge_timeout_s)
        if "CHARGED" not in response.upper():
            with self._lock:
                self.state = State.FAULT
            raise ChargeFailedError(f"Charge failed: {response}")
        with self._lock:
            self.state = State.READY
        logger.info("Charged and READY")

    # ========================================================
    # INTERNAL: ARM
    # ========================================================
    def _arm(self):
        response = self._send("ARM")
        if "ARMED" not in response.upper():
            raise HardwareError(f"Arm failed: {response}")
        with self._lock:
            self.state = State.ARMED
            self.armed_at = time.time()
        logger.info("ARMED")

    # ========================================================
    # INTERNAL: FIRE
    # ========================================================
    def _fire(self, lat, lon, hob):
        with self._lock:
            armed_at = self.armed_at
            last_fire = self.last_fire_at
            state = self.state

        if state != State.ARMED:
            raise HardwareError(f"Cannot fire from state {state.value}")

        if time.time() - armed_at > self.config.arm_timeout_s:
            self._disarm_internal()
            raise HardwareError(
                f"Auto-disarm: armed longer than "
                f"{self.config.arm_timeout_s}s"
            )

        elapsed = time.time() - last_fire
        if elapsed < self.config.cooldown_s:
            wait = self.config.cooldown_s - elapsed
            raise FireRejectedError(f"Cooldown active. Wait {wait:.1f}s")

        with self._lock:
            self.state = State.FIRING

        cmd = f"FIRE {lat:.4f} {lon:.4f} {hob:.1f}"
        response = self._send(cmd, timeout=self.config.fire_timeout_s)

        if "FIRED" not in response.upper() and "OK" not in response.upper():
            with self._lock:
                self.state = State.FAULT
            raise FireRejectedError(f"Fire rejected: {response}")

        with self._lock:
            self.last_fire_at = time.time()
            self.state = State.COOLDOWN
        logger.info(f"FIRE OK: {cmd} | {response}")
        return response

    # ========================================================
    # INTERNAL: COOLDOWN
    # ========================================================
    def _cooldown(self):
        time.sleep(0.5)
        with self._lock:
            if self.state == State.COOLDOWN:
                self.state = State.CONNECTED
        logger.info("Cooldown complete")

    # ========================================================
    # INTERNAL: DISARM
    # ========================================================
    def _disarm_internal(self):
        try:
            self._send("DISARM")
        except Exception:
            pass
        with self._lock:
            if self.state != State.ESTOP:
                self.state = State.CONNECTED
        logger.info("Disarmed internally")

    # ========================================================
    # INTERNAL: SEND (with persistent RX buffer)
    # ========================================================
    def _send(self, cmd: str, timeout: Optional[float] = None) -> str:
        with self._io_lock:
            if not self.serial or not getattr(self.serial, "is_open", False):
                raise NotConnectedError("Serial not open")

            t = timeout if timeout is not None else self.config.read_timeout_s

            # Drain any stale bytes before sending
            try:
                if self.serial.in_waiting:
                    self.serial.read(self.serial.in_waiting)
                self._rx_buffer = b""
            except Exception as e:
                raise HardwareError(f"Pre-send drain failed: {e}")

            # Send
            try:
                self.serial.write((cmd + "\n").encode("ascii"))
                self.serial.flush()
            except Exception as e:
                raise HardwareError(f"Write failed: {e}")

            # Receive
            deadline = time.time() + t
            while time.time() < deadline:
                if self._shutdown:
                    raise HardwareError("Controller shutting down")
                if not getattr(self.serial, "is_open", False):
                    raise HardwareError("Serial closed during read")
                try:
                    if self.serial.in_waiting:
                        self._rx_buffer += self.serial.read(self.serial.in_waiting)
                        if b"\n" in self._rx_buffer:
                            line, self._rx_buffer = self._rx_buffer.split(b"\n", 1)
                            text = line.decode("ascii", errors="ignore").strip()
                            logger.info(f"TX: {cmd} | RX: {text}")
                            return text
                except Exception as e:
                    raise HardwareError(f"Read failed: {e}")
                time.sleep(0.05)

            logger.warning(f"TX: {cmd} | RX: TIMEOUT after {t}s")
            raise HardwareError(f"Timeout waiting for response to '{cmd}'")

    # ========================================================
    # INTERNAL: FAIL RESULT HELPER
    # ========================================================
    def _result_fail(self, lat, lon, hob, err, start, code="FAULT") -> FireResult:
        logger.error(f"{code}: {err}")
        with self._lock:
            state_after = self.state.value
        return FireResult(
            success=False,
            state_before="",
            state_after=state_after,
            target_lat=lat,
            target_lon=lon,
            hob_km=hob,
            hardware_response="",
            error=err,
            duration_s=time.time() - start
        )