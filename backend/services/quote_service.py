from typing import Dict, Any
import math

class QuoteService:
    def compute_quote(self, vehicle_type: str, engine_size: int, years_no_claim: int, location: str) -> Dict[str, Any]:
        """Compute mock insurance quote based on vehicle details"""
        
        # Base premium by vehicle type
        base_rates = {
            "sedan": 90000,
            "suv": 120000,
            "hatchback": 75000,
            "pickup": 110000
        }
        
        base = base_rates.get(vehicle_type.lower(), 90000)
        
        # Engine size adjustment
        engine_adj = 25000 if engine_size > 2000 else 10000
        
        # No claims discount (max 25%)
        ncd = min(years_no_claim * 0.05, 0.25)
        
        # Location risk adjustment
        location_risk = 15000 if "kigali" in location.lower() else 10000
        
        # Calculate subtotal
        subtotal = base + engine_adj + location_risk
        after_ncd = math.floor(subtotal * (1 - ncd))
        
        # Add 18% tax
        tax = math.floor(after_ncd * 0.18)
        premium_rwf = after_ncd + tax
        
        return {
            "premium_rwf": premium_rwf,
            "breakdown": {
                "base_premium": base,
                "engine_adjustment": engine_adj,
                "location_risk": location_risk,
                "subtotal": subtotal,
                "no_claims_discount": f"{int(ncd * 100)}%",
                "after_discount": after_ncd,
                "tax_18_percent": tax
            },
            "coverage": {
                "third_party_liability": "Unlimited",
                "property_damage": "50,000,000 RWF",
                "legal_expenses": "5,000,000 RWF"
            },
            "disclaimer": "This is a demo quote. Actual rates may vary. Contact insurer for official quote."
        }