"""
Grading System - Converts analysis results into standardized grades
"""

from typing import Dict, Any, Tuple

from .debug_utils import get_logger, trace_function

# Initialize logger for this module
logger = get_logger(__name__)


class GradingSystem:
    """Converts card analysis results into standardized grading scores."""
    
    # Standard grading scale weights (can be adjusted based on grading company standards)
    DEFAULT_WEIGHTS = {
        "edges": 0.25,      # 25% weight for edge quality
        "corners": 0.30,    # 30% weight for corner quality  
        "surface": 0.30,    # 30% weight for surface quality
        "centering": 0.15   # 15% weight for centering
    }
    
    # PSA Grade scale mapping with official descriptions
    GRADE_SCALE = {
        "10": {
            "min": 95, 
            "label": "Gem Mint",
            "description": "A PSA Gem Mint 10 card is a virtually perfect card. Attributes include four perfectly sharp corners, sharp focus and full original gloss. Must be free of staining of any kind, but an allowance may be made for a slight printing imperfection, if it doesn't impair the overall appeal. Image must be centered within a tolerance not to exceed approximately 55/45 percent on the front, and 75/25 percent on the reverse.",
            "centering_tolerance": {"front": 55, "back": 75}
        },
        "9": {
            "min": 87, 
            "label": "Mint",
            "description": "A PSA Mint 9 is a superb condition card that exhibits only one of the following minor flaws: a very slight wax stain on reverse, a minor printing imperfection or slightly off white borders. Centering must be approximately 60/40 or better on the front and 90/10 or better on the reverse.",
            "centering_tolerance": {"front": 60, "back": 90}
        },
        "8": {
            "min": 78, 
            "label": "Near Mint-Mint",
            "description": "A PSA NM-MT 8 is a super high-end card that appears Mint 9 at first glance, but upon closer inspection, can exhibit: a very slight wax stain on reverse, slightest fraying at one or two corners, a minor printing imperfection, and/or slightly off-white borders. Centering must be approximately 65/35 or better on the front and 90/10 or better on the reverse.",
            "centering_tolerance": {"front": 65, "back": 90}
        },
        "7": {
            "min": 68, 
            "label": "Near Mint",
            "description": "A PSA NM 7 is a card with just a slight surface wear visible upon close inspection. There may be slight fraying on some corners. Picture focus may be slightly out-of register. A minor printing blemish is acceptable. Slight wax staining is acceptable on the back only. Most original gloss is retained. Centering must be approximately 70/30 or better on the front and 90/10 or better on the back.",
            "centering_tolerance": {"front": 70, "back": 90}
        },
        "6": {
            "min": 58, 
            "label": "Excellent-Near Mint",
            "description": "A PSA 6 card may have visible surface wear or a printing defect which does not detract from its overall appeal. A very light scratch may be detected only upon close inspection. Corners may have slightly graduated fraying. Picture focus may be slightly out-of-register. May show some loss of original gloss, minor wax stain on reverse, very slight notching on edges and some off-whiteness on borders. Centering must be 80/20 or better on the front and 90/10 or better on the reverse.",
            "centering_tolerance": {"front": 80, "back": 90}
        },
        "5": {
            "min": 48, 
            "label": "Excellent",
            "description": "On PSA 5 cards, very minor rounding of the corners is becoming evident. Surface wear or printing defects are more visible. There may be minor chipping on edges. Loss of original gloss will be more apparent. Focus of picture may be slightly out-of-register. Several light scratches may be visible upon close inspection, but do not detract from the appeal. May show some off-whiteness of borders. Centering must be 85/15 or better on the front and 90/10 or better on the back.",
            "centering_tolerance": {"front": 85, "back": 90}
        },
        "4": {
            "min": 38, 
            "label": "Very Good-Excellent",
            "description": "Shows moderate corner wear and surface wear. Minor creases may be present.",
            "centering_tolerance": {"front": 90, "back": 90}
        },
        "3": {
            "min": 28, 
            "label": "Very Good",
            "description": "Shows significant wear with rounded corners and surface defects.",
            "centering_tolerance": {"front": 90, "back": 90}
        },
        "2": {
            "min": 18, 
            "label": "Good",
            "description": "Heavy wear with major surface damage and corner rounding.",
            "centering_tolerance": {"front": 90, "back": 90}
        },
        "1": {
            "min": 0, 
            "label": "Poor",
            "description": "Severe damage affecting card integrity and appeal.",
            "centering_tolerance": {"front": 90, "back": 90}
        }
    }
    
    def __init__(self, custom_weights: Dict[str, float] = None):
        """Initialize grading system with optional custom weights."""
        if custom_weights:
            # Validate weights sum to 1.0
            if abs(sum(custom_weights.values()) - 1.0) > 0.01:
                raise ValueError("Weights must sum to 1.0")
            self.weights = custom_weights
        else:
            self.weights = self.DEFAULT_WEIGHTS.copy()
    
    @trace_function
    def calculate_overall_score(self, analysis_results: Dict[str, Any]) -> float:
        """Calculate weighted overall score from analysis results."""
        total_score = 0.0
        
        for component, weight in self.weights.items():
            if component in analysis_results:
                component_score = analysis_results[component].get("score", 0)
                total_score += component_score * weight
            else:
                # If component missing, penalize heavily
                logger.warning(f"Missing component in analysis: {component}")
                total_score += 0 * weight
        
        logger.debug(f"Calculated overall score: {total_score:.2f}")
        return min(100.0, max(0.0, total_score))
    
    def score_to_grade(self, score: float) -> Tuple[str, str, str]:
        """Convert numerical score to letter grade, description, and detailed explanation."""
        for grade, criteria in self.GRADE_SCALE.items():
            if score >= criteria["min"]:
                return grade, criteria["label"], criteria.get("description", "")
        
        return "1", "Poor", self.GRADE_SCALE["1"]["description"]
    
    @trace_function
    def generate_detailed_report(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive grading report with PSA standards."""
        logger.info("Generating detailed grading report")
        overall_score = self.calculate_overall_score(analysis_results)
        grade, grade_label, grade_description = self.score_to_grade(overall_score)
        
        logger.info(f"Report generated: Grade {grade}/10 ({grade_label}), Score: {overall_score:.2f}")
        
        # Calculate component contributions
        component_contributions = {}
        for component, weight in self.weights.items():
            if component in analysis_results:
                component_score = analysis_results[component].get("score", 0)
                contribution = component_score * weight
                component_grade, component_label, _ = self.score_to_grade(component_score)
                component_contributions[component] = {
                    "score": component_score,
                    "weight": weight,
                    "contribution": contribution,
                    "grade": component_grade,
                    "grade_label": component_label
                }
        
        # Identify strengths and weaknesses
        component_scores = {k: v["score"] for k, v in component_contributions.items()}
        best_component = max(component_scores, key=component_scores.get) if component_scores else None
        worst_component = min(component_scores, key=component_scores.get) if component_scores else None
        
        # Generate PSA-specific suggestions
        suggestions = self._generate_psa_suggestions(analysis_results, component_scores, grade)
        
        # Check centering against PSA standards
        centering_evaluation = self._evaluate_centering_standards(analysis_results, grade)
        
        return {
            "overall_score": round(overall_score, 2),
            "predicted_grade": grade,
            "grade_description": grade_label,
            "detailed_description": grade_description,
            "component_breakdown": component_contributions,
            "strengths": [best_component] if best_component else [],
            "weaknesses": [worst_component] if worst_component else [],
            "improvement_suggestions": suggestions,
            "confidence_level": self._calculate_confidence(analysis_results),
            "centering_evaluation": centering_evaluation,
            "psa_compliance": self._check_psa_compliance(analysis_results, grade)
        }
    
    def _generate_psa_suggestions(self, analysis_results: Dict[str, Any], 
                                component_scores: Dict[str, float], grade: str) -> list:
        """Generate PSA-specific improvement suggestions based on analysis."""
        suggestions = []
        
        # Get PSA standards for the current grade
        if not grade.isdigit() or not (1 <= int(grade) <= 10):
            return suggestions
            
        current_grade_info = self.GRADE_SCALE.get(grade, {})
        current_grade_num = int(grade)
        next_grade = str(min(10, current_grade_num + 1)) if current_grade_num < 10 else None
        next_grade_info = self.GRADE_SCALE.get(next_grade, {}) if next_grade else None
        
        for component, score in component_scores.items():
            if component == "edges" and score < 80:
                if current_grade_num <= 7:
                    suggestions.append("Edge wear is preventing higher grade - PSA values sharp, clean edges")
                else:
                    suggestions.append("Minor edge imperfections detected - protect with quality sleeves")
                    
            elif component == "corners" and score < 85:
                if current_grade_num <= 6:
                    suggestions.append("Corner damage significantly impacts grade - PSA heavily weighs corner quality")
                elif current_grade_num <= 8:
                    suggestions.append("Slight corner fraying detected - handle with extreme care to prevent further damage")
                else:
                    suggestions.append("Corners show excellent condition - maintain with proper storage")
                    
            elif component == "surface" and score < 80:
                if current_grade_num <= 5:
                    suggestions.append("Surface defects are limiting grade potential - scratches and wear significantly impact PSA scores")
                elif current_grade_num <= 7:
                    suggestions.append("Minor surface wear detected - PSA allows slight wear at this grade level")
                else:
                    suggestions.append("Surface shows minimal wear - protect from fingerprints and scratches")
                    
            elif component == "centering" and score < 70:
                centering_tolerance = current_grade_info.get("centering_tolerance", {})
                front_tolerance = centering_tolerance.get("front", 90)
                suggestions.append(f"Centering issues detected - PSA {grade} requires {front_tolerance}/{100-front_tolerance} or better centering")
        
        if not suggestions:
            if current_grade_num >= 9:
                suggestions.append("Excellent card quality! This card meets high PSA standards.")
            elif current_grade_num >= 7:
                suggestions.append("Good card quality with only minor flaws preventing higher grade.")
            else:
                suggestions.append("Card shows wear consistent with its grade level.")
        
        # Add grade-specific advice
        if next_grade_info and current_grade_num < 10:
            suggestions.append(f"To achieve PSA {next_grade}: {next_grade_info.get('description', '')[:100]}...")
        
        return suggestions
    
    def _evaluate_centering_standards(self, analysis_results: Dict[str, Any], grade: str) -> Dict[str, Any]:
        """Evaluate centering against PSA standards for the predicted grade."""
        centering_data = analysis_results.get("centering", {})
        centering_score = centering_data.get("score", 0)
        
        grade_info = self.GRADE_SCALE.get(grade, {})
        centering_tolerance = grade_info.get("centering_tolerance", {"front": 90, "back": 90})
        
        # Simulate centering percentage based on score
        # Higher scores indicate better centering (closer to 50/50)
        if centering_score >= 90:
            estimated_centering = 55  # Very close to perfect
        elif centering_score >= 80:
            estimated_centering = 60
        elif centering_score >= 70:
            estimated_centering = 65
        elif centering_score >= 60:
            estimated_centering = 70
        elif centering_score >= 50:
            estimated_centering = 80
        else:
            estimated_centering = 85
        
        meets_standard = estimated_centering <= centering_tolerance["front"]
        
        return {
            "estimated_centering_ratio": f"{estimated_centering}/{100-estimated_centering}",
            "required_for_grade": f"{centering_tolerance['front']}/{100-centering_tolerance['front']}",
            "meets_psa_standard": meets_standard,
            "centering_score": centering_score
        }
    
    def _check_psa_compliance(self, analysis_results: Dict[str, Any], grade: str) -> Dict[str, Any]:
        """Check compliance with PSA standards for the predicted grade."""
        grade_info = self.GRADE_SCALE.get(grade, {})
        
        compliance_checks = {
            "corners": self._check_corner_compliance(analysis_results, grade),
            "edges": self._check_edge_compliance(analysis_results, grade),
            "surface": self._check_surface_compliance(analysis_results, grade),
            "centering": self._check_centering_compliance(analysis_results, grade)
        }
        
        overall_compliance = all(check["compliant"] for check in compliance_checks.values())
        
        return {
            "overall_compliant": overall_compliance,
            "component_compliance": compliance_checks,
            "grade_requirements": grade_info.get("description", ""),
            "compliance_summary": self._generate_compliance_summary(compliance_checks, grade)
        }
    
    def _check_corner_compliance(self, analysis_results: Dict[str, Any], grade: str) -> Dict[str, Any]:
        """Check corner compliance with PSA standards."""
        corner_score = analysis_results.get("corners", {}).get("score", 0)
        
        if grade == "10":
            compliant = corner_score >= 95  # Perfect corners required
            message = "Requires four perfectly sharp corners"
        elif grade == "9":
            compliant = corner_score >= 85  # Very minor flaws acceptable
            message = "Superb condition with minimal corner wear"
        elif grade == "8":
            compliant = corner_score >= 75  # Slightest fraying acceptable
            message = "Slightest fraying at one or two corners acceptable"
        elif grade == "7":
            compliant = corner_score >= 65  # Slight fraying acceptable
            message = "Slight fraying on some corners acceptable"
        else:
            compliant = True  # Lower grades have more tolerance
            message = "Meets corner requirements for this grade"
        
        return {"compliant": compliant, "message": message, "score": corner_score}
    
    def _check_edge_compliance(self, analysis_results: Dict[str, Any], grade: str) -> Dict[str, Any]:
        """Check edge compliance with PSA standards."""
        edge_score = analysis_results.get("edges", {}).get("score", 0)
        
        if grade == "10":
            compliant = edge_score >= 95  # Perfect edges required
            message = "Requires perfectly sharp edges"
        elif grade in ["9", "8"]:
            compliant = edge_score >= 80  # Minor imperfections acceptable
            message = "Minor edge imperfections acceptable"
        elif grade == "7":
            compliant = edge_score >= 70  # Slight wear acceptable
            message = "Slight edge wear acceptable"
        else:
            compliant = True
            message = "Meets edge requirements for this grade"
        
        return {"compliant": compliant, "message": message, "score": edge_score}
    
    def _check_surface_compliance(self, analysis_results: Dict[str, Any], grade: str) -> Dict[str, Any]:
        """Check surface compliance with PSA standards."""
        surface_score = analysis_results.get("surface", {}).get("score", 0)
        
        if grade == "10":
            compliant = surface_score >= 95  # Must be free of staining
            message = "Must be free of staining (slight printing imperfection allowed)"
        elif grade == "9":
            compliant = surface_score >= 85  # Very slight wax stain acceptable
            message = "Very slight wax stain on reverse acceptable"
        elif grade == "8":
            compliant = surface_score >= 75  # Minor imperfections acceptable
            message = "Minor printing imperfections acceptable"
        elif grade == "7":
            compliant = surface_score >= 65  # Slight surface wear acceptable
            message = "Slight surface wear visible upon close inspection"
        else:
            compliant = True
            message = "Meets surface requirements for this grade"
        
        return {"compliant": compliant, "message": message, "score": surface_score}
    
    def _check_centering_compliance(self, analysis_results: Dict[str, Any], grade: str) -> Dict[str, Any]:
        """Check centering compliance with PSA standards."""
        centering_eval = self._evaluate_centering_standards(analysis_results, grade)
        
        return {
            "compliant": centering_eval["meets_psa_standard"],
            "message": f"Requires {centering_eval['required_for_grade']} centering or better",
            "score": centering_eval["centering_score"],
            "estimated_ratio": centering_eval["estimated_centering_ratio"]
        }
    
    def _generate_compliance_summary(self, compliance_checks: Dict[str, Any], grade: str) -> str:
        """Generate a summary of compliance issues."""
        non_compliant = [comp for comp, check in compliance_checks.items() if not check["compliant"]]
        
        if not non_compliant:
            return f"Card meets all PSA {grade} requirements"
        else:
            return f"Card fails PSA {grade} requirements for: {', '.join(non_compliant)}"
    
    def _calculate_confidence(self, analysis_results: Dict[str, Any]) -> str:
        """Calculate confidence level in the grading prediction."""
        # Simple confidence calculation based on analysis completeness and score distribution
        num_components = len(analysis_results)
        expected_components = len(self.weights)
        
        if num_components < expected_components:
            return "Low"
        
        # Check score variance - consistent scores indicate higher confidence
        scores = [result.get("score", 0) for result in analysis_results.values()]
        if len(scores) > 1:
            mean_score = sum(scores) / len(scores)
            score_variance = sum((s - mean_score)**2 for s in scores) / len(scores)
            if score_variance < 100:  # Low variance
                return "High"
            elif score_variance < 400:  # Medium variance
                return "Medium"
            else:
                return "Low"
        
        return "Medium"
    
    def compare_to_standards(self, analysis_results: Dict[str, Any], 
                           grading_company: str = "PSA") -> Dict[str, Any]:
        """Compare results to specific grading company standards."""
        # This could be expanded with specific company criteria
        company_standards = {
            "PSA": {
                "gem_mint_threshold": 95,
                "mint_threshold": 85,
                "corner_weight": 0.30,
                "surface_weight": 0.30
            },
            "BGS": {
                "gem_mint_threshold": 96,
                "mint_threshold": 87,
                "corner_weight": 0.25,
                "surface_weight": 0.25
            }
        }
        
        standards = company_standards.get(grading_company, company_standards["PSA"])
        overall_score = self.calculate_overall_score(analysis_results)
        
        return {
            "grading_company": grading_company,
            "meets_gem_mint": overall_score >= standards["gem_mint_threshold"],
            "meets_mint": overall_score >= standards["mint_threshold"],
            "company_specific_score": overall_score,
            "standards_applied": standards
        }