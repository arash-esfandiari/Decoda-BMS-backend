from pydantic import BaseModel
from typing import List, Dict, Any

class StatItem(BaseModel):
    label: str
    value: float

class PatientDemographics(BaseModel):
    by_age: List[StatItem]
    by_gender: List[StatItem]

class RevenueTrend(BaseModel):
    date: str # "YYYY-MM"
    value: float

class AppointmentPattern(BaseModel):
    busiest_days: List[StatItem]

class ProviderPerformance(BaseModel):
    revenue_by_provider: List[StatItem]
    services_by_provider: List[StatItem]

class AnalyticsSummary(BaseModel):
    total_revenue: int
    total_patients: int
    total_appointments: int
    patients_by_source: List[StatItem]
    top_services: List[StatItem]
    appointments_by_status: List[StatItem]
    
    # New fields
    demographics: PatientDemographics
    revenue_trend: List[RevenueTrend]
    patterns: AppointmentPattern
    provider_performance: ProviderPerformance

class PatientAnalyticsResponse(BaseModel):
    total_patients: int
    by_source: List[StatItem]
    by_gender: List[StatItem]
    average_age: float
    by_decade: List[StatItem]
