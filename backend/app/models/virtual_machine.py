from sqlalchemy import Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.enums import VirtualMachineStatus
from app.db.base import Base
from app.models.mixins import IdMixin


class VirtualMachine(Base, IdMixin):
    __tablename__ = "virtual_machines"

    vm_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(120), nullable=False)
    os_type: Mapped[str] = mapped_column(String(120), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[VirtualMachineStatus] = mapped_column(
        Enum(VirtualMachineStatus), default=VirtualMachineStatus.PROVISIONING, nullable=False
    )
    notes: Mapped[str] = mapped_column(Text, default="", nullable=False)
