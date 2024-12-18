```python
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

class QualityLevel(Enum):
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"

@dataclass
class QualityMetric:
    name: str
    value: float
    level: QualityLevel
    benchmark: float
    description: str

@dataclass
class ComplexityMetric:
    name: str
    value: float
    threshold: float
    location: Optional[Tuple[int, int]] = None
    details: Optional[Dict[str, Any]] = None

class CodeQualityAnalyzer(ASTAnalyzer):
    """コード品質の分析"""
    def __init__(self, ast_accessor: ASTAccessor, benchmark_data: Dict[str, Any]):
        super().__init__(ast_accessor)
        self.benchmark_data = benchmark_data
        self.metrics: Dict[str, QualityMetric] = {}
        self.issues: List[Dict[str, Any]] = []
        self.recommendations: List[Dict[str, Any]] = []

    def analyze(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        self._analyze_naming_conventions(ast)
        self._analyze_code_structure(ast)
        self._analyze_documentation(ast)
        self._generate_recommendations()
        
        return {
            "metrics": self.metrics,
            "issues": self.issues,
            "recommendations": self.recommendations,
            "summary": self._create_quality_summary()
        }

    def _analyze_naming_conventions(self, ast: Dict[str, Any]) -> None:
        """命名規則の分析"""
        for node in self.ast_accessor.get_node_by_type(ast, ASTNodeType.DATA_ITEM):
            self._check_naming_convention(node)
            
        for node in self.ast_accessor.get_node_by_type(ast, ASTNodeType.PARAGRAPH):
            self._check_naming_convention(node)

    def _analyze_code_structure(self, ast: Dict[str, Any]) -> None:
        """コード構造の分析"""
        self._analyze_division_structure(ast)
        self._analyze_section_organization(ast)
        self._analyze_paragraph_structure(ast)

    def _create_quality_summary(self) -> Dict[str, Any]:
        """品質サマリーの作成"""
        return {
            "overall_quality": self._calculate_overall_quality(),
            "major_issues": self._summarize_major_issues(),
            "improvement_priorities": self._identify_improvement_priorities()
        }

class ComplexityAnalyzer(ASTAnalyzer):
    """複雑度の分析"""
    def __init__(self, ast_accessor: ASTAccessor):
        super().__init__(ast_accessor)
        self.complexity_metrics: Dict[str, ComplexityMetric] = {}
        self.hotspots: List[Dict[str, Any]] = []

    def analyze(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        self._analyze_cyclomatic_complexity(ast)
        self._analyze_cognitive_complexity(ast)
        self._analyze_halstead_metrics(ast)
        self._identify_complexity_hotspots()
        
        return {
            "complexity_metrics": self.complexity_metrics,
            "hotspots": self.hotspots,
            "summary": self._create_complexity_summary()
        }

    def _analyze_cyclomatic_complexity(self, ast: Dict[str, Any]) -> None:
        """循環的複雑度の分析"""
        for node in self.ast_accessor.get_node_by_type(ast, ASTNodeType.PARAGRAPH):
            complexity = self._calculate_cyclomatic_complexity(node)
            self.complexity_metrics[f"cyclomatic_{node['name']}"] = ComplexityMetric(
                name="Cyclomatic Complexity",
                value=complexity,
                threshold=10.0,
                location=(node.get("line", 0), node.get("column", 0))
            )

    def _analyze_cognitive_complexity(self, ast: Dict[str, Any]) -> None:
        """認知的複雑度の分析"""
        for node in self.ast_accessor.get_node_by_type(ast, ASTNodeType.PARAGRAPH):
            complexity = self._calculate_cognitive_complexity(node)
            self.complexity_metrics[f"cognitive_{node['name']}"] = ComplexityMetric(
                name="Cognitive Complexity",
                value=complexity,
                threshold=15.0,
                location=(node.get("line", 0), node.get("column", 0))
            )

    def _identify_complexity_hotspots(self) -> None:
        """複雑度の高い箇所の特定"""
        for metric_name, metric in self.complexity_metrics.items():
            if metric.value > metric.threshold:
                self.hotspots.append({
                    "metric_name": metric_name,
                    "value": metric.value,
                    "threshold": metric.threshold,
                    "location": metric.location,
                    "details": metric.details
                })

class MaintainabilityAnalyzer(ASTAnalyzer):
    """保守性の分析"""
    def __init__(self, ast_accessor: ASTAccessor):
        super().__init__(ast_accessor)
        self.maintainability_index: Dict[str, float] = {}
        self.maintainability_factors: Dict[str, List[Dict[str, Any]]] = {}
        self.improvement_suggestions: List[Dict[str, Any]] = []

    def analyze(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        self._calculate_maintainability_index(ast)
        self._analyze_change_impact(ast)
        self._analyze_modularity(ast)
        self._generate_improvement_suggestions()
        
        return {
            "maintainability_index": self.maintainability_index,
            "factors": self.maintainability_factors,
            "suggestions": self.improvement_suggestions,
            "summary": self._create_maintainability_summary()
        }

    def _calculate_maintainability_index(self, ast: Dict[str, Any]) -> None:
        """保守性指標の計算"""
        for node in self.ast_accessor.get_node_by_type(ast, ASTNodeType.PARAGRAPH):
            self.maintainability_index[node["name"]] = self._calculate_mi_for_node(node)

    def _analyze_change_impact(self, ast: Dict[str, Any]) -> None:
        """変更影響度の分析"""
        self._analyze_data_dependencies(ast)
        self._analyze_control_dependencies(ast)
        self._analyze_module_coupling(ast)

    def _analyze_modularity(self, ast: Dict[str, Any]) -> None:
        """モジュール性の分析"""
        self._analyze_cohesion(ast)
        self._analyze_coupling(ast)
        self._analyze_information_hiding(ast)

class TechnicalDebtAnalyzer(ASTAnalyzer):
    """技術的負債の分析"""
    def __init__(self, ast_accessor: ASTAccessor):
        super().__init__(ast_accessor)
        self.debt_items: List[Dict[str, Any]] = []
        self.debt_metrics: Dict[str, float] = {}

    def analyze(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        self._analyze_code_smells(ast)
        self._analyze_architectural_debt(ast)
        self._analyze_documentation_debt(ast)
        self._calculate_debt_metrics()
        
        return {
            "debt_items": self.debt_items,
            "metrics": self.debt_metrics,
            "summary": self._create_debt_summary(),
            "remediation": self._generate_remediation_plan()
        }

    def _analyze_code_smells(self, ast: Dict[str, Any]) -> None:
        """コードの臭いの分析"""
        self._detect_duplicated_code(ast)
        self._detect_long_methods(ast)
        self._detect_complex_conditionals(ast)

    def _calculate_debt_metrics(self) -> None:
        """技術的負債メトリクスの計算"""
        self.debt_metrics = {
            "debt_ratio": self._calculate_debt_ratio(),
            "remediation_cost": self._calculate_remediation_cost(),
            "debt_probability": self._calculate_debt_probability()
        }

    def _generate_remediation_plan(self) -> Dict[str, Any]:
        """改善計画の生成"""
        return {
            "priorities": self._prioritize_debt_items(),
            "estimated_effort": self._estimate_remediation_effort(),
            "recommended_steps": self._generate_remediation_steps()
        }
```