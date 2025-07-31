"""
EGSA Calculator Library - Object-Oriented Utility Management System
A custom library for Electricity, Gas, Steam, and Air Conditioning calculations
"""

from decimal import Decimal
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import math


class UtilityCalculator:
    """Base class for utility calculations"""
    
    def __init__(self, rate_per_unit: float = 0.0):
        self.rate_per_unit = Decimal(str(rate_per_unit))
        self.calculation_history = []
    
    def calculate_cost(self, usage: float) -> Decimal:
        """Calculate cost based on usage"""
        cost = Decimal(str(usage)) * self.rate_per_unit
        self.calculation_history.append({
            'usage': usage,
            'rate': float(self.rate_per_unit),
            'cost': float(cost),
            'timestamp': datetime.now()
        })
        return cost
    
    def get_efficiency_rating(self, usage: float, benchmark: float) -> str:
        """Get efficiency rating compared to benchmark"""
        ratio = usage / benchmark if benchmark > 0 else 1
        if ratio <= 0.8:
            return "Excellent"
        elif ratio <= 1.0:
            return "Good"
        elif ratio <= 1.2:
            return "Average"
        else:
            return "Poor"


class ElectricityCalculator(UtilityCalculator):
    """Specialized calculator for electricity consumption"""
    
    def __init__(self, rate_per_kwh: float = 0.12):
        super().__init__(rate_per_kwh)
        self.peak_hours = (17, 21)  # 5 PM to 9 PM
        self.peak_rate_multiplier = 1.5
    
    def calculate_peak_cost(self, usage: float, hour: int) -> Decimal:
        """Calculate cost considering peak hour rates"""
        base_cost = self.calculate_cost(usage)
        if self.peak_hours[0] <= hour <= self.peak_hours[1]:
            return base_cost * Decimal(str(self.peak_rate_multiplier))
        return base_cost
    
    def estimate_carbon_footprint(self, kwh_usage: float) -> float:
        """Estimate CO2 emissions in kg"""
        # Average emission factor: 0.5 kg CO2 per kWh
        return kwh_usage * 0.5
    
    def recommend_savings(self, monthly_usage: float) -> Dict[str, str]:
        """Provide energy saving recommendations"""
        recommendations = {}
        if monthly_usage > 500:
            recommendations['high_usage'] = "Consider LED lighting and energy-efficient appliances"
        if monthly_usage > 300:
            recommendations['moderate_usage'] = "Use programmable thermostats"
        recommendations['general'] = "Unplug devices when not in use"
        return recommendations


class GasCalculator(UtilityCalculator):
    """Specialized calculator for gas consumption"""
    
    def __init__(self, rate_per_cubic_meter: float = 0.45):
        super().__init__(rate_per_cubic_meter)
        self.heating_efficiency = 0.85  # 85% efficiency
    
    def calculate_heating_cost(self, cubic_meters: float, outdoor_temp: float) -> Decimal:
        """Calculate heating cost adjusted for outdoor temperature"""
        base_cost = self.calculate_cost(cubic_meters)
        # Increase cost for colder temperatures
        temp_factor = max(0.5, (20 - outdoor_temp) / 20)
        return base_cost * Decimal(str(temp_factor))
    
    def estimate_btu_output(self, cubic_meters: float) -> float:
        """Estimate BTU output from gas consumption"""
        # 1 cubic meter ≈ 35,300 BTU
        return cubic_meters * 35300 * self.heating_efficiency


class SteamCalculator(UtilityCalculator):
    """Specialized calculator for steam systems"""
    
    def __init__(self, rate_per_pound: float = 0.025):
        super().__init__(rate_per_pound)
        self.steam_pressure = 15  # PSI
        self.efficiency_factor = 0.9
    
    def calculate_condensate_return(self, steam_usage: float) -> float:
        """Calculate condensate return percentage"""
        # Typical condensate return is 80-95%
        return steam_usage * 0.85
    
    def estimate_heat_transfer(self, pounds_steam: float) -> float:
        """Estimate heat transfer in BTU"""
        # Steam latent heat ≈ 970 BTU/lb at 15 PSI
        return pounds_steam * 970 * self.efficiency_factor


class AirConditioningCalculator(UtilityCalculator):
    """Specialized calculator for air conditioning systems"""
    
    def __init__(self, rate_per_kwh: float = 0.15):
        super().__init__(rate_per_kwh)
        self.cop_rating = 3.5  # Coefficient of Performance
        self.seasonal_factor = 1.0
    
    def calculate_cooling_cost(self, kwh_usage: float, outdoor_temp: float) -> Decimal:
        """Calculate cooling cost adjusted for outdoor temperature"""
        base_cost = self.calculate_cost(kwh_usage)
        # Increase cost for hotter temperatures
        temp_factor = max(0.8, (outdoor_temp - 70) / 30 + 1)
        return base_cost * Decimal(str(temp_factor))
    
    def estimate_cooling_capacity(self, kwh_consumption: float) -> float:
        """Estimate cooling capacity in tons"""
        # 1 ton = 12,000 BTU/hr, 1 kWh ≈ 3,412 BTU
        btu_output = kwh_consumption * 3412 * self.cop_rating
        return btu_output / 12000
    
    def recommend_temperature_settings(self, outdoor_temp: float) -> Dict[str, int]:
        """Recommend optimal temperature settings"""
        if outdoor_temp > 90:
            return {'cooling': 76, 'heating': 68}
        elif outdoor_temp > 80:
            return {'cooling': 74, 'heating': 70}
        else:
            return {'cooling': 72, 'heating': 72}


class EGSAAnalyzer:
    """Main analyzer class for comprehensive EGSA management"""
    
    def __init__(self):
        self.electricity = ElectricityCalculator()
        self.gas = GasCalculator()
        self.steam = SteamCalculator()
        self.air_conditioning = AirConditioningCalculator()
        self.analysis_history = []
    
    def comprehensive_analysis(self, utility_data: Dict) -> Dict:
        """Perform comprehensive analysis of all utilities"""
        analysis = {
            'timestamp': datetime.now(),
            'total_cost': Decimal('0'),
            'efficiency_scores': {},
            'recommendations': [],
            'environmental_impact': {}
        }
        
        total_cost = Decimal('0')
        efficiency_scores = {}
        recommendations = []
        environmental_impact = {}
        
        # Electricity analysis
        if 'electricity' in utility_data:
            elec_data = utility_data['electricity']
            cost = self.electricity.calculate_cost(elec_data['usage'])
            total_cost += cost
            efficiency_scores['electricity'] = self.electricity.get_efficiency_rating(
                elec_data['usage'], elec_data.get('benchmark', 400)
            )
            environmental_impact['co2_kg'] = self.electricity.estimate_carbon_footprint(
                elec_data['usage']
            )
            recommendations.extend(
                list(self.electricity.recommend_savings(elec_data['usage']).values())
            )
        
        # Gas analysis
        if 'gas' in utility_data:
            gas_data = utility_data['gas']
            cost = self.gas.calculate_heating_cost(
                gas_data['usage'], 
                gas_data.get('outdoor_temp', 20)
            )
            total_cost += cost
            efficiency_scores['gas'] = self.gas.get_efficiency_rating(
                gas_data['usage'], gas_data.get('benchmark', 100)
            )
        
        # Steam analysis
        if 'steam' in utility_data:
            steam_data = utility_data['steam']
            cost = self.steam.calculate_cost(steam_data['usage'])
            total_cost += cost
            efficiency_scores['steam'] = self.steam.get_efficiency_rating(
                steam_data['usage'], steam_data.get('benchmark', 50)
            )
        
        # Air conditioning analysis
        if 'air_conditioning' in utility_data:
            ac_data = utility_data['air_conditioning']
            cost = self.air_conditioning.calculate_cooling_cost(
                ac_data['usage'], 
                ac_data.get('outdoor_temp', 75)
            )
            total_cost += cost
            efficiency_scores['air_conditioning'] = self.air_conditioning.get_efficiency_rating(
                ac_data['usage'], ac_data.get('benchmark', 200)
            )
        
        # Update analysis dict
        analysis['total_cost'] = total_cost
        analysis['efficiency_scores'] = efficiency_scores
        analysis['recommendations'] = recommendations
        analysis['environmental_impact'] = environmental_impact
        
        self.analysis_history.append(analysis)
        return analysis
    
    def generate_monthly_report(self, start_date: datetime, end_date: datetime) -> Dict:
        """Generate comprehensive monthly report"""
        relevant_analyses = [
            analysis for analysis in self.analysis_history
            if start_date <= analysis['timestamp'] <= end_date
        ]
        
        if not relevant_analyses:
            return {'error': 'No data available for the specified period'}
        
        total_cost = sum(analysis['total_cost'] for analysis in relevant_analyses)
        avg_efficiency = self._calculate_average_efficiency(relevant_analyses)
        
        return {
            'period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            'total_cost': float(total_cost),
            'average_efficiency': avg_efficiency,
            'total_analyses': len(relevant_analyses),
            'cost_trend': self._calculate_cost_trend(relevant_analyses)
        }
    
    def _calculate_average_efficiency(self, analyses: List[Dict]) -> Dict:
        """Calculate average efficiency scores"""
        efficiency_totals = {}
        efficiency_counts = {}
        
        for analysis in analyses:
            for utility, score in analysis['efficiency_scores'].items():
                if utility not in efficiency_totals:
                    efficiency_totals[utility] = 0
                    efficiency_counts[utility] = 0
                
                score_value = {'Excellent': 4, 'Good': 3, 'Average': 2, 'Poor': 1}[score]
                efficiency_totals[utility] += score_value
                efficiency_counts[utility] += 1
        
        avg_scores = {}
        for utility in efficiency_totals:
            avg_value = efficiency_totals[utility] / efficiency_counts[utility]
            avg_scores[utility] = {4: 'Excellent', 3: 'Good', 2: 'Average', 1: 'Poor'}[round(avg_value)]
        
        return avg_scores
    
    def _calculate_cost_trend(self, analyses: List[Dict]) -> str:
        """Calculate cost trend (increasing/decreasing/stable)"""
        if len(analyses) < 2:
            return "Insufficient data"
        
        recent_cost = float(analyses[-1]['total_cost'])
        older_cost = float(analyses[0]['total_cost'])
        
        if recent_cost > older_cost * 1.1:
            return "Increasing"
        elif recent_cost < older_cost * 0.9:
            return "Decreasing"
        else:
            return "Stable"


# Factory class for creating appropriate calculators
class UtilityCalculatorFactory:
    """Factory for creating utility calculators"""
    
    @staticmethod
    def create_calculator(utility_type: str, **kwargs):
        """Create appropriate calculator based on utility type"""
        calculators = {
            'electricity': ElectricityCalculator,
            'gas': GasCalculator,
            'steam': SteamCalculator,
            'air_conditioning': AirConditioningCalculator
        }
        
        if utility_type not in calculators:
            raise ValueError(f"Unknown utility type: {utility_type}")
        
        return calculators[utility_type](**kwargs)


# Global analyzer instance
_global_analyzer = None

def get_analyzer():
    """Get global analyzer instance"""
    global _global_analyzer
    if _global_analyzer is None:
        _global_analyzer = EGSAAnalyzer()
    return _global_analyzer


# Export main classes for easy import
__all__ = [
    'UtilityCalculator',
    'ElectricityCalculator', 
    'GasCalculator',
    'SteamCalculator',
    'AirConditioningCalculator',
    'EGSAAnalyzer',
    'UtilityCalculatorFactory',
    'get_analyzer'
]
