from repositories.analytics import AnalyticsRepository
from api.analytics_schema import AnalyticsSummary, StatItem

class AnalyticsService:
    def __init__(self, repository: AnalyticsRepository):
        self.repository = repository

    async def get_summary(self) -> AnalyticsSummary:
        revenue = await self.repository.get_total_revenue()
        patients = await self.repository.get_total_patients()
        appointments = await self.repository.get_total_appointments()
        
        sources_raw = await self.repository.get_patients_by_source()
        sources = [
            StatItem(
                label=str(s[0]).replace("_", " ").title() if s[0] else "Unknown", 
                value=s[1]
            ) 
            for s in sources_raw
        ]

        services_raw = await self.repository.get_top_services()
        services = [
            StatItem(
                label=str(s[0]).title(), 
                value=s[1]
            ) 
            for s in services_raw
        ]
        
        status_raw = await self.repository.get_appointments_by_status()
        statuses = [
            StatItem(
                label=str(s[0]).replace("_", " ").title(), 
                value=s[1]
            ) 
            for s in status_raw
        ]

        # New Metrics
        revenue_raw = await self.repository.get_monthly_revenue()
        revenue_trend = [
            {"date": r[0] or "Unknown", "value": (r[1] or 0) / 100.0} # Convert cents to dollars
            for r in revenue_raw
        ]

        demographics_raw = await self.repository.get_patient_demographics()
        genders = [StatItem(label=str(g[0]).title() if g[0] else "Unknown", value=g[1]) for g in demographics_raw["gender"]]
        
        # Format age buckets (0 -> "0-10", 1 -> "10-20")
        ages = []
        for bucket, count in demographics_raw["age"]:
            if bucket is None: continue
            start = (bucket - 1) * 10
            end = bucket * 10
            ages.append(StatItem(label=f"{start}-{end}", value=count))

        patterns_raw = await self.repository.get_appointment_patterns()
        
        day_mapping = {
            "Monday": 0, "Tuesday": 1, "Wednesday": 2, "Thursday": 3,
            "Friday": 4, "Saturday": 5, "Sunday": 6
        }
        
        days = [StatItem(label=str(p[0]).strip(), value=p[1]) for p in patterns_raw]
        days.sort(key=lambda x: day_mapping.get(x.label, 99))

        provider_rev_raw = await self.repository.get_provider_revenue()
        prov_rev = [
            StatItem(label=str(p[0]), value=(p[1] or 0) / 100.0) # Convert cents to dollars
            for p in provider_rev_raw
        ]

        provider_serv_raw = await self.repository.get_provider_services()
        prov_serv = [
            StatItem(label=str(p[0]), value=p[1])
            for p in provider_serv_raw
        ]

        return AnalyticsSummary(
            total_revenue=revenue,
            total_patients=patients,
            total_appointments=appointments,
            patients_by_source=sources,
            top_services=services,
            appointments_by_status=statuses,
            demographics={
                "by_gender": genders,
                "by_age": ages
            },
            revenue_trend=revenue_trend,
            patterns={
                "busiest_days": days
            },
            provider_performance={
                "revenue_by_provider": prov_rev,
                "services_by_provider": prov_serv
            },
            top_patients=await self.repository.get_top_patients(),
            retention_opportunities=await self.repository.get_retention_opportunities()
        )

