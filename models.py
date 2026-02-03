from datetime import datetime
from typing import List
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    date_of_birth: Mapped[datetime] = mapped_column(DateTime)
    gender: Mapped[str] = mapped_column(
        String
    )  # Storing as string to be simple, could be Enum
    address: Mapped[str] = mapped_column(String)
    phone: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    created_date: Mapped[datetime] = mapped_column(DateTime)

    appointments: Mapped[List["Appointment"]] = relationship(back_populates="patient")


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    first_name: Mapped[str] = mapped_column(String)
    last_name: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
    phone: Mapped[str] = mapped_column(String)
    created_date: Mapped[datetime] = mapped_column(DateTime)


class Service(Base):
    __tablename__ = "services"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    price: Mapped[int] = mapped_column(Integer)  # In cents
    duration: Mapped[int] = mapped_column(Integer)  # In minutes
    created_date: Mapped[datetime] = mapped_column(DateTime)


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    status: Mapped[str] = mapped_column(String)
    created_date: Mapped[datetime] = mapped_column(DateTime)

    patient: Mapped["Patient"] = relationship(back_populates="appointments")
    services: Mapped[List["AppointmentService"]] = relationship(
        back_populates="appointment"
    )
    payments: Mapped[List["Payment"]] = relationship(back_populates="appointment")


class AppointmentService(Base):
    __tablename__ = "appointment_services"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    appointment_id: Mapped[str] = mapped_column(ForeignKey("appointments.id"))
    service_id: Mapped[str] = mapped_column(ForeignKey("services.id"))
    provider_id: Mapped[str] = mapped_column(ForeignKey("providers.id"))
    start: Mapped[datetime] = mapped_column(DateTime)
    end: Mapped[datetime] = mapped_column(DateTime)

    appointment: Mapped["Appointment"] = relationship(back_populates="services")
    service: Mapped["Service"] = relationship()
    provider: Mapped["Provider"] = relationship()


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.id"))
    amount: Mapped[int] = mapped_column(Integer)
    date: Mapped[datetime] = mapped_column(DateTime)
    method: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    provider_id: Mapped[str] = mapped_column(ForeignKey("providers.id"))
    appointment_id: Mapped[str] = mapped_column(ForeignKey("appointments.id"))
    service_id: Mapped[str] = mapped_column(ForeignKey("services.id"))
    created_date: Mapped[datetime] = mapped_column(DateTime)

    appointment: Mapped["Appointment"] = relationship(back_populates="payments")
