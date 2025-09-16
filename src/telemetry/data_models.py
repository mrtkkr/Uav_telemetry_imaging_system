# src/telemetry/data_models.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional






class GPSData(BaseModel):
    latitude: float = Field(..., description="Enlem")
    longitude: float = Field(..., description="Boylam")
    altitude: float = Field(..., description="Rakım (metre)")
    fix_quality: int = 1  # örnek varsayılan (1: GPS fix)
    satellites: int = 10  # BUNU EKLEYİN


class AttitudeData(BaseModel):
    roll: float  # Derece
    pitch: float  # Derece
    yaw: float  # Derece


class TelemetryPacket(BaseModel):
    timestamp: datetime
    gps: GPSData
    attitude: Optional[AttitudeData] = None
    velocity: Optional[float] = Field(None, description="m/s")
    battery_voltage: Optional[float] = Field(None, description="Volt")
    battery_percent: Optional[float] = Field(None, description="%")
    status: Optional[str] = Field(None, description="Uçuş durumu")


# Örnek kullanım
if __name__ == "__main__":
    packet = TelemetryPacket(
        timestamp=datetime.utcnow(),
        gps=GPSData(latitude=39.92077, longitude=32.85411, altitude=1200),
        velocity=15.3,
        battery_voltage=11.1,
        battery_percent=82.5,
        status="CRUISE"
    )
    print(packet.json(indent=2))
