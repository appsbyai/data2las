"""IMU: decode $IMURAW channel for orientation estimation."""

import struct
import os
import numpy as np


def decode_imu(data_files):
    """Decode raw IMU records from channel 1.

    Each IMU record contains gyro/accel/temperature readings.
    Returns list of {t, gx, gy, gz, ax, ay, az, temp}.
    """
    imu_data = []

    for df in data_files:
        with open(df, "rb") as f:
            f.seek(1024)
            off, end = 1024, os.path.getsize(df)

            while off + 8 <= end:
                hdr = f.read(8)
                cid = struct.unpack_from("<I", hdr, 0)[0]
                dlen = struct.unpack_from("<I", hdr, 4)[0]
                if dlen > 10_000_000:
                    break

                if cid == 1:
                    data = f.read(dlen)
                    if len(data) >= 32:
                        try:
                            # IMU record format: timestamp(8) + gyro_x(4) + gyro_y(4)
                            # + gyro_z(4) + accel_x(4) + accel_y(4) + accel_z(4)
                            t = struct.unpack_from("<Q", data, 0)[0]
                            gx = struct.unpack_from("<f", data, 8)[0]
                            gy = struct.unpack_from("<f", data, 12)[0]
                            gz = struct.unpack_from("<f", data, 16)[0]
                            ax = struct.unpack_from("<f", data, 20)[0]
                            ay = struct.unpack_from("<f", data, 24)[0]
                            az = struct.unpack_from("<f", data, 28)[0]

                            imu_data.append({
                                "t": t,
                                "gx": gx, "gy": gy, "gz": gz,
                                "ax": ax, "ay": ay, "az": az,
                            })
                        except struct.error:
                            pass

                off += 8 + dlen
                f.seek(off)

    return imu_data


def estimate_orientation(imu_data, alpha=0.98):
    """Estimate roll/pitch from IMU accelerometer (complementary filter).

    Returns arrays of (time, roll_deg, pitch_deg).
    Gyro yaw is integrated but will drift without magnetometer.
    """
    if not imu_data:
        return None

    n = len(imu_data)
    roll = np.zeros(n)
    pitch = np.zeros(n)
    yaw = np.zeros(n)
    times = np.zeros(n)

    roll[0] = np.degrees(np.arctan2(imu_data[0]["ay"], imu_data[0]["az"]))
    pitch[0] = np.degrees(np.arctan2(-imu_data[0]["ax"],
                         np.sqrt(imu_data[0]["ay"]**2 + imu_data[0]["az"]**2)))
    yaw[0] = 0
    times[0] = imu_data[0]["t"]

    for i in range(1, n):
        dt = (imu_data[i]["t"] - imu_data[i-1]["t"]) * 1e-6
        if dt <= 0 or dt > 0.1:
            dt = 0.01

        gx, gy, gz = imu_data[i]["gx"], imu_data[i]["gy"], imu_data[i]["gz"]
        ax, ay, az = imu_data[i]["ax"], imu_data[i]["ay"], imu_data[i]["az"]

        acc_roll = np.degrees(np.arctan2(ay, az))
        acc_pitch = np.degrees(np.arctan2(-ax, np.sqrt(ay**2 + az**2)))

        roll[i] = alpha * (roll[i-1] + gx * dt) + (1 - alpha) * acc_roll
        pitch[i] = alpha * (pitch[i-1] + gy * dt) + (1 - alpha) * acc_pitch
        yaw[i] = yaw[i-1] + gz * dt
        times[i] = imu_data[i]["t"]

    return times, roll, pitch, yaw
