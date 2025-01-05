# /home/administrator/cobol-analyzer/src/cobol_analyzer/analysis/components.py

from dataclasses import dataclass
from typing import Dict, List, Optional, Set
from .base_components import BaseAnalyzer, BaseParser, AnalysisContext, SourceType

@dataclass
class COBOLDivision:
    name: str
    start_line: int
    end_line: int
    content: str
    sections: List['COBOLSection']

@dataclass
class COBOLSection:
    name: str
    start_line: int
    end_line: int
    content: str
    paragraphs: List['COBOLParagraph']

@dataclass
class COBOLParagraph:
    name: str
    start_line: int
    end_line: int
    content: str

class COBOLParser(BaseParser):
    def parse(self, content: str) -> Dict[str, Any]:
    """COBOLソースコードをパースしてAST生成"""
    try:
        # ソースのトークン化
        tokens = self._tokenize(content)
        
        # 各DIVISIONのパース
        ast = {
            "type": "program",
            "children": []
        }
        
        identification_division = self._parse_identification_division(tokens)
        if identification_division:
            ast["children"].append(identification_division)
            
        environment_division = self._parse_environment_division(tokens)
        if environment_division:
            ast["children"].append(environment_division)
            
        data_division = self._parse_data_division(tokens)
        if data_division:
            ast["children"].append(data_division)
            
        procedure_division = self._parse_procedure_division(tokens)
        if procedure_division:
            ast["children"].append(procedure_division)
        
        self.validate(ast)
        return ast
        
    except Exception as e:
        self.logger.error(f"COBOL parse error: {str(e)}")
        raise

    def validate(self, ast: Dict[str, Any]) -> List[Dict[str, Any]]:
        """ASTの妥当性を検証"""
        # COBOL特有のバリデーション実装
        validation_errors = []
    
        # 必須DIVISIONの存在チェック
        divisions = [node["name"] for node in ast["children"] 
                    if node["type"] == "division"]
    
        if "IDENTIFICATION DIVISION" not in divisions:
            validation_errors.append({
                "type": "missing_division",
                "severity": "error",
                "message": "IDENTIFICATION DIVISION is missing"
            })
    
        if "PROCEDURE DIVISION" not in divisions:
            validation_errors.append({
                "type": "missing_division",
                "severity": "error",
                "message": "PROCEDURE DIVISION is missing"
            })
    
        # 各DIVISIONの検証
        for node in ast["children"]:
            if node["type"] == "division":
                if node["name"] == "DATA DIVISION":
                    validation_errors.extend(self._validate_data_division(node))
                elif node["name"] == "PROCEDURE DIVISION":
                    validation_errors.extend(self._validate_procedure_division(node))
    
        return validation_errors

class COBOLAnalyzer(BaseAnalyzer):
    def __init__(self, context: AnalysisContext):
        super().__init__(context)
        self.parser = COBOLParser()
        self.ast: Optional[Dict[str, Any]] = None
        self._init_analyzers()

    def _init_analyzers(self) -> None:
        """各種アナライザを初期化"""
        self.structure_analyzer = COBOLStructureAnalyzer(self.context)
        self.dialect_analyzer = DialectAnalyzer(self.context)
        self.syntax_analyzer = SpecialSyntaxAnalyzer(self.context)
        self.embedded_analyzer = EmbeddedElementAnalyzer(self.context)
        self.metrics_analyzer = COBOLMetricsAnalyzer(self.context)

    def prepare(self) -> bool:
        """解析の準備を行う"""
        try:
            content = self._read_source_file()
            self.ast = self.parser.parse(content)
            return True
        except Exception as e:
            self.logger.log_error("COBOLAnalyzer", f"Preparation failed: {str(e)}")
            return False

    def analyze(self) -> bool:
        """解析を実行"""
        try:
            # 構造解析
            structure_results = self.structure_analyzer.analyze(self.ast)
            self.result_manager.add_result("structure", structure_results)

            # メーカー固有解析
            dialect_results = self.dialect_analyzer.analyze(self.ast)
            self.result_manager.add_result("dialect", dialect_results)

            # 特殊構文解析
            syntax_results = self.syntax_analyzer.analyze(self.ast)
            self.result_manager.add_result("syntax", syntax_results)

            # 内含要素解析
            embedded_results = self.embedded_analyzer.analyze(self.ast)
            self.result_manager.add_result("embedded", embedded_results)

            # メトリクス解析
            metrics_results = self.metrics_analyzer.analyze(self.ast)
            self.result_manager.add_result("metrics", metrics_results)

            return True

        except Exception as e:
            self.logger.log_error("COBOLAnalyzer", f"Analysis failed: {str(e)}")
            return False

    def post_process(self) -> bool:
        """解析後の処理を実行"""
        try:
            self.result_manager.save_to_postgresql()
            self.result_manager.save_to_mongodb()
            return True
        except Exception as e:
            self.logger.log_error("COBOLAnalyzer", f"Post-processing failed: {str(e)}")
            return False

class COBOLStructureAnalyzer:
    """COBOL構造解析"""
    def __init__(self, context: AnalysisContext):
        self.context = context

    def analyze(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        divisions = self._analyze_divisions(ast)
        sections = self._analyze_sections(ast)
        paragraphs = self._analyze_paragraphs(ast)
        return {
            "divisions": divisions,
            "sections": sections,
            "paragraphs": paragraphs
        }

    def _analyze_divisions(self, ast: Dict[str, Any]) -> List[COBOLDivision]:
    """DIVISION解析を実行"""
        divisions = []
    
        for node in ast["children"]:
            if node["type"] == "division":
                division = COBOLDivision(
                    name=node["name"],
                    start_line=node.get("source_line", 0),
                    end_line=node.get("end_line", 0),
                    content=node.get("content", ""),
                    sections=self._analyze_sections(node)
                )
                divisions.append(division)
    
        # DIVISIONの順序チェック
        required_order = [
            "IDENTIFICATION DIVISION",
            "ENVIRONMENT DIVISION",
            "DATA DIVISION",
            "PROCEDURE DIVISION"
        ]
    
        division_order = [d.name for d in divisions]
        for div1, div2 in zip(required_order[:-1], required_order[1:]):
            if div1 in division_order and div2 in division_order:
                if division_order.index(div1) > division_order.index(div2):
                    self.logger.warning(f"Invalid division order: {div1} should come before {div2}")
    
        return divisions

    def _analyze_sections(self, ast: Dict[str, Any]) -> List[COBOLSection]:
        """SECTION解析を実行"""
        sections = []
    
        for node in ast["children"]:
            if node["type"] == "section":
                section = COBOLSection(
                    name=node["name"],
                    parent_division=ast["name"],
                    start_line=node.get("source_line", 0),
                    end_line=node.get("end_line", 0),
                    paragraphs=self._analyze_paragraphs(node),
                    statements_count=self._count_statements(node),
                    complexity=self._calculate_section_complexity(node)
                )
                sections.append(section)
    
        return sections

    def _analyze_paragraphs(self, ast: Dict[str, Any]) -> List[COBOLParagraph]:
        """PARAGRAPH解析を実行"""
        paragraphs = []
    
        for node in ast["children"]:
            if node["type"] == "paragraph":
                paragraph = COBOLParagraph(
                    name=node["name"],
                    start_line=node.get("source_line", 0),
                    end_line=node.get("end_line", 0),
                    content=node.get("content", "")
                )
                paragraphs.append(paragraph)
            
                # 文の解析
                statements = []
                for stmt_node in node["children"]:
                    if stmt_node["type"] == "statement":
                    statements.append(self._analyze_statement(stmt_node))
                    
                paragraph.statements = statements
    
        return paragraphs

class DialectAnalyzer:
    """メーカー固有仕様解析"""
    def __init__(self, context: AnalysisContext):
        self.context = context
        self._init_dialect_detectors()

    def _init_dialect_detectors(self) -> None:
        self.detectors = {
            'hitachi': HitachiDialectDetector(),
            'fujitsu': FujitsuDialectDetector(),
            'ibm': IBMDialectDetector(),
            'nec': NECDialectDetector(),
            'unisys': UnisysDialectDetector()
        }

    def analyze(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        results = {}
        for name, detector in self.detectors.items():
            results[name] = detector.detect(ast)
        return results

class SpecialSyntaxAnalyzer:
    """特殊構文解析"""
    def __init__(self, context: AnalysisContext):
        self.context = context

    def analyze(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        copy_statements = self._analyze_copy_statements(ast)
        replace_statements = self._analyze_replace_statements(ast)
        exec_statements = self._analyze_exec_statements(ast)
        return {
            "copy_statements": copy_statements,
            "replace_statements": replace_statements,
            "exec_statements": exec_statements
        }

    def _analyze_copy_statements(self, ast: Dict[str, Any]) -> List[Dict[str, Any]]:
        """COPY文の解析を実行"""
        copy_statements = []
    
        def analyze_node(node: Dict[str, Any]):
            if node["type"] == "statement" and node["statement_type"] == "COPY":
                copy_info = {
                    "copybook": node["value"],
                    "line": node.get("source_line", 0),
                    "replacing": node.get("replacing", []),
                    "library": node.get("library"),
                    "references": self._collect_copybook_references(node)
                }
                copy_statements.append(copy_info)
            
            for child in node.get("children", []):
                analyze_node(child)
    
        analyze_node(ast)
        return copy_statements

    def _analyze_replace_statements(self, ast: Dict[str, Any]) -> List[Dict[str, Any]]:
        """REPLACE文の解析を実行"""
        replace_statements = []
    
        def analyze_node(node: Dict[str, Any]):
            if node["type"] == "statement" and node["statement_type"] == "REPLACE":
                replace_info = {
                    "line": node.get("source_line", 0),
                    "replacements": node.get("replacements", []),
                    "scope": self._determine_replace_scope(node),
                    "affected_lines": self._analyze_affected_lines(node)
                }
                replace_statements.append(replace_info)
            
            for child in node.get("children", []):
                analyze_node(child)
    
        analyze_node(ast)
        return replace_statements

    def _analyze_exec_statements(self, ast: Dict[str, Any]) -> List[Dict[str, Any]]:
        """EXEC文の解析を実行"""
        exec_statements = []
    
        def analyze_node(node: Dict[str, Any]):
            if node["type"] == "statement" and node["statement_type"] == "EXEC":
                exec_info = {
                    "line": node.get("source_line", 0),
                    "command_type": node.get("command_type"),
                    "content": node.get("content", ""),
                    "parameters": self._extract_exec_parameters(node),
                    "dependencies": self._analyze_exec_dependencies(node)
                }
                exec_statements.append(exec_info)
            
            for child in node.get("children", []):
                analyze_node(child)
    
        analyze_node(ast)
        return exec_statements

class COBOLMetricsAnalyzer:
    """COBOLメトリクス解析"""
    def __init__(self, context: AnalysisContext):
        self.context = context

    def analyze(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        complexity = self._analyze_complexity(ast)
        maintainability = self._analyze_maintainability(ast)
        security = self._analyze_security(ast)
        return {
            "complexity": complexity,
            "maintainability": maintainability,
            "security": security
        }

    def _analyze_complexity(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """複雑度解析を実行"""
        complexity_metrics = {
            "cyclomatic": self._calculate_cyclomatic_complexity(ast),
            "essential": self._calculate_essential_complexity(ast),
            "cognitive": self._calculate_cognitive_complexity(ast),
            "max_nesting_level": self._calculate_max_nesting_level(ast),
            "decision_density": self._calculate_decision_density(ast),
            "halstead_metrics": self._calculate_halstead_metrics(ast)
        }
    
        # スコアの計算
        complexity_score = 0
        max_score = 100
    
        # 各メトリクスの重み付け
        weights = {
            "cyclomatic": 0.3,
            "essential": 0.2,
            "cognitive": 0.2,
            "max_nesting_level": 0.15,
            "decision_density": 0.15
        }
    
        for metric, weight in weights.items():
            if metric in complexity_metrics:
                normalized_value = self._normalize_metric_value(
                    complexity_metrics[metric],
                    metric
                )
                complexity_score += normalized_value * weight
    
        complexity_metrics["overall_score"] = min(max_score, complexity_score)
    
        return complexity_metrics

    def _analyze_maintainability(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """保守性解析を実行"""
        maintainability_metrics = {
            "lines_of_code": self._count_lines_of_code(ast),
            "comment_ratio": self._calculate_comment_ratio(ast),
            "code_duplication": self._analyze_code_duplication(ast),
            "module_coupling": self._analyze_module_coupling(ast),
            "data_coupling": self._analyze_data_coupling(ast),
            "maintainability_index": self._calculate_maintainability_index(ast)
        }
    
        # 各メトリクスのしきい値チェック
        issues = []
        if maintainability_metrics["comment_ratio"] < 0.1:
            issues.append({
                "type": "low_comment_ratio",
                "severity": "warning",
                "message": "コメント率が10%未満です"
            })
    
        if maintainability_metrics["code_duplication"] > 0.2:
            issues.append({
                "type": "high_duplication",
                "severity": "warning",
                "message": "コードの重複率が20%を超えています"
            })
    
        maintainability_metrics["issues"] = issues
    
        return maintainability_metrics

    def _analyze_security(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """セキュリティ解析を実行"""
        security_metrics = {
            "data_exposure": self._analyze_data_exposure(ast),
            "input_validation": self._analyze_input_validation(ast),
            "sql_injection_risks": self._analyze_sql_injection_risks(ast),
            "error_handling": self._analyze_error_handling(ast),
            "access_control": self._analyze_access_control(ast)
        }
        
        # セキュリティ上の問題をスコア化
        risk_score = 0
        max_score = 100
    
        for category, findings in security_metrics.items():
            if findings.get("vulnerabilities"):
                risk_score += len(findings["vulnerabilities"]) * findings.get("severity_weight", 1)
    
        security_metrics["risk_score"] = min(risk_score, max_score)
        security_metrics["risk_level"] = self._determine_risk_level(risk_score)
    
        return security_metrics