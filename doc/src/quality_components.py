# /home/administrator/cobol-analyzer/src/cobol_analyzer/analysis/quality/quality_components.py
# このコードは品質分析に必要な以下の主要機能を提供します：
# 1. 命名規則の分析
# 2. コード構造の評価
# 3. ドキュメント品質の評価
# 4. モジュール性の分析
# 5. 依存関係の分析
# 6. コンポーネントの評価
# 7. 改善推奨事項の生成

from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict
import statistics
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from abc import ABC, abstractmethod

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

class CodeQualityAnalyzer:
    """コード品質の分析"""
    def __init__(self, ast_accessor: ASTAccessor, benchmark_data: Dict[str, Any]):
        self.ast_accessor = ast_accessor
        self.benchmark_data = benchmark_data
        self.metrics: Dict[str, QualityMetric] = {}
        self.issues: List[Dict[str, Any]] = []
        self.recommendations: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def analyze(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """品質分析の実行"""
        try:
            # 並列処理による各種分析の実行
            analysis_tasks = [
                self._analyze_naming_conventions(ast_data),
                self._analyze_code_structure(ast_data),
                self._analyze_documentation(ast_data),
                self._analyze_modularity(ast_data)
            ]
            
            results = await asyncio.gather(*analysis_tasks)
            
            naming_quality = results[0]
            structure_quality = results[1]
            documentation_quality = results[2]
            modularity = results[3]

            # 総合評価の生成
            overall_quality = self._calculate_overall_quality([
                naming_quality,
                structure_quality,
                documentation_quality,
                modularity
            ])

            return {
                "metrics": self.metrics,
                "issues": self.issues,
                "recommendations": self.recommendations,
                "summary": self._create_quality_summary(overall_quality)
            }

        except Exception as e:
            self.logger.error(f"Quality analysis failed: {str(e)}")
            raise

    async def _analyze_naming_conventions(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """命名規則の分析"""
        naming_patterns = {
            'data_items': r'^[A-Z][A-Z0-9-]*$',
            'procedures': r'^[A-Z][A-Z0-9-]*$',
            'variables': r'^[A-Z][A-Z0-9-]*$'
        }

        violations = defaultdict(list)
        total_items = 0

        # データ項目の分析
        for item in ast_data.get('data_items', []):
            total_items += 1
            item_name = item.get('name', '')
            if not re.match(naming_patterns['data_items'], item_name):
                violations['data_items'].append({
                    'name': item_name,
                    'location': item.get('location'),
                    'recommended': self._suggest_name_correction(item_name)
                })

        # プロシージャの分析
        for proc in ast_data.get('procedures', []):
            total_items += 1
            proc_name = proc.get('name', '')
            if not re.match(naming_patterns['procedures'], proc_name):
                violations['procedures'].append({
                    'name': proc_name,
                    'location': proc.get('location'),
                    'recommended': self._suggest_name_correction(proc_name)
                })

        # スコアの計算
        compliance_rate = 1.0 - (sum(len(v) for v in violations.values()) / total_items if total_items > 0 else 0)
        level = self._determine_quality_level(compliance_rate)

        return {
            "compliance_rate": compliance_rate,
            "violations": dict(violations),
            "level": level,
            "details": {
                "total_items": total_items,
                "violation_count": sum(len(v) for v in violations.values())
            }
        }

    def _suggest_name_correction(self, original_name: str) -> str:
        """命名規則に従った名前の提案"""
        corrected = re.sub(r'[^A-Z0-9-]', '', original_name.upper())
        if not corrected:
            corrected = 'ITEM'
        if not corrected[0].isalpha():
            corrected = 'X' + corrected
        return corrected

    async def _analyze_code_structure(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """コード構造の分析"""
        structure_metrics = {}
        
        # DIVISION構造の分析
        divisions = ast_data.get('divisions', [])
        division_analysis = self._analyze_divisions(divisions)
        structure_metrics['divisions'] = division_analysis

        # SECTION構造の分析
        sections = ast_data.get('sections', [])
        section_analysis = self._analyze_sections(sections)
        structure_metrics['sections'] = section_analysis

        # パラグラフ構造の分析
        paragraphs = ast_data.get('paragraphs', [])
        paragraph_analysis = self._analyze_paragraphs(paragraphs)
        structure_metrics['paragraphs'] = paragraph_analysis

        # 全体的な構造スコアの計算
        structure_score = self._calculate_structure_score(
            division_analysis,
            section_analysis,
            paragraph_analysis
        )

        return {
            "metrics": structure_metrics,
            "score": structure_score,
            "level": self._determine_quality_level(structure_score),
            "suggestions": self._generate_structure_suggestions(structure_metrics)
        }

    def _analyze_divisions(self, divisions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """DIVISION構造の分析"""
        expected_divisions = {'IDENTIFICATION', 'ENVIRONMENT', 'DATA', 'PROCEDURE'}
        found_divisions = {div['name'] for div in divisions}
        missing_divisions = expected_divisions - found_divisions
        extra_divisions = found_divisions - expected_divisions

        return {
            "completeness": len(found_divisions & expected_divisions) / len(expected_divisions),
            "correctness": 1.0 - len(extra_divisions) / len(expected_divisions) if expected_divisions else 1.0,
            "missing": list(missing_divisions),
            "extra": list(extra_divisions)
        }

    def _analyze_sections(self, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
        """SECTION構造の分析"""
        section_sizes = [len(section.get('statements', [])) for section in sections]
        
        return {
            "count": len(sections),
            "average_size": statistics.mean(section_sizes) if section_sizes else 0,
            "max_size": max(section_sizes) if section_sizes else 0,
            "size_distribution": self._calculate_distribution(section_sizes),
            "oversized_sections": [
                section['name'] for section in sections
                if len(section.get('statements', [])) > 100
            ]
        }

    def _analyze_paragraphs(self, paragraphs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """パラグラフ構造の分析"""
        paragraph_sizes = [len(para.get('statements', [])) for para in paragraphs]
        paragraph_depths = [para.get('nesting_level', 0) for para in paragraphs]

        return {
            "count": len(paragraphs),
            "average_size": statistics.mean(paragraph_sizes) if paragraph_sizes else 0,
            "max_size": max(paragraph_sizes) if paragraph_sizes else 0,
            "average_depth": statistics.mean(paragraph_depths) if paragraph_depths else 0,
            "max_depth": max(paragraph_depths) if paragraph_depths else 0,
            "complex_paragraphs": [
                para['name'] for para in paragraphs
                if len(para.get('statements', [])) > 50 or para.get('nesting_level', 0) > 3
            ]
        }

    def _calculate_structure_score(self,
                                division_analysis: Dict[str, Any],
                                section_analysis: Dict[str, Any],
                                paragraph_analysis: Dict[str, Any]) -> float:
        """構造スコアの計算"""
        division_score = (
            division_analysis['completeness'] * 0.6 +
            division_analysis['correctness'] * 0.4
        )

        section_score = max(0.0, min(1.0, 1.0 - (
            len(section_analysis['oversized_sections']) / section_analysis['count']
            if section_analysis['count'] > 0 else 0
        )))

        paragraph_score = max(0.0, min(1.0, 1.0 - (
            len(paragraph_analysis['complex_paragraphs']) / paragraph_analysis['count']
            if paragraph_analysis['count'] > 0 else 0
        )))

        return (
            division_score * 0.4 +
            section_score * 0.3 +
            paragraph_score * 0.3
        ) * 100

    async def _analyze_documentation(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """ドキュメントの分析"""
        # コメント解析
        comments = ast_data.get('comments', [])
        total_lines = ast_data.get('total_lines', 0)
        code_lines = ast_data.get('code_lines', 0)

        comment_analysis = await self._analyze_comments(comments)
        comment_ratio = len(comments) / total_lines if total_lines > 0 else 0

        # ドキュメンテーションレベルの評価
        doc_level = self._evaluate_documentation_level(
            comment_analysis,
            comment_ratio
        )

        return {
            "metrics": {
                "comment_ratio": comment_ratio,
                "meaningful_comments": comment_analysis['meaningful_ratio'],
                "documentation_coverage": comment_analysis['coverage'],
            },
            "level": doc_level,
            "issues": comment_analysis['issues'],
            "suggestions": self._generate_documentation_suggestions(comment_analysis)
        }

    async def _analyze_comments(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """コメントの詳細分析"""
        meaningful_comments = 0
        issues = []
        coverage_areas = defaultdict(int)

        for comment in comments:
            # コメントの意味性評価
            if len(comment['text']) > 10 and not self._is_trivial_comment(comment['text']):
                meaningful_comments += 1
            else:
                issues.append({
                    'type': 'trivial_comment',
                    'location': comment['location'],
                    'text': comment['text']
                })

            # カバレッジ領域の分析
            area = self._determine_comment_area(comment)
            coverage_areas[area] += 1

        return {
            "meaningful_ratio": meaningful_comments / len(comments) if comments else 0,
            "coverage": self._calculate_coverage_score(coverage_areas),
            "issues": issues,
            "coverage_areas": dict(coverage_areas)
        }

    def _is_trivial_comment(self, comment_text: str) -> bool:
        """無意味なコメントの判定"""
        trivial_patterns = [
            r'^\s*end\s*$',
            r'^\s*begin\s*$',
            r'^\s*[A-Za-z]+\s*$',
            r'^\s*[0-9]+\s*$'
        ]
        return any(re.match(pattern, comment_text.lower()) for pattern in trivial_patterns)

    def _determine_comment_area(self, comment: Dict[str, Any]) -> str:
        """コメントのカバレッジ領域判定"""
        text = comment['text'].lower()
        location = comment.get('location', {})

        if location.get('division') == 'IDENTIFICATION':
            return 'program_documentation'
        elif location.get('division') == 'DATA':
            return 'data_documentation'
        elif 'error' in text or 'exception' in text:
            return 'error_handling'
        elif 'todo' in text or 'fixme' in text:
            return 'maintenance'
        else:
            return 'logic_documentation'

    def _calculate_coverage_score(self, coverage_areas: Dict[str, int]) -> float:
        """カバレッジスコアの計算"""
        expected_areas = {
            'program_documentation': 1,
            'data_documentation': 1,
            'error_handling': 1,
            'logic_documentation': 1
        }

        covered_areas = sum(1 for area in expected_areas if coverage_areas.get(area, 0) > 0)
        return covered_areas / len(expected_areas)

    async def _analyze_modularity(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """モジュール性の分析"""
        # 依存関係の分析
        dependencies = await self._analyze_dependencies(ast_data)
        
        # コンポーネント分析
        components = await self._analyze_components(ast_data)
        
        # 凝集度分析
        cohesion = await self._analyze_cohesion(ast_data)
        
        # 結合度分析
        coupling = await self._analyze_coupling(dependencies)

        modularity_score = self._calculate_modularity_score(
            dependencies,
            components,
            cohesion,
            coupling
        )

        return {
            "score": modularity_score,
            "level": self._determine_quality_level(modularity_score),
            "metrics": {
                "dependencies": dependencies,
                "components": components,
                "cohesion": cohesion,
                "coupling": coupling
            },
            "recommendations": self._generate_modularity_recommendations(
                dependencies,
                components,
                cohesion,
                coupling
            )
        }

    async def _analyze_dependencies(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """依存関係の分析"""
        # CALLステートメントの分析
        calls = [node for node in ast_data.get('statements', [])
                if node.get('type') == 'CALL']
        
        # データ依存関係の分析
        data_dependencies = self._analyze_data_dependencies(ast_data)
        
        # 外部依存関係の分析
        external_dependencies = [
            call['target'] for call in calls
            if not self._is_internal_module(call['target'])
        ]

        # 依存関係グラフの構築
        dependency_graph = self._build_dependency_graph(
            calls,
            data_dependencies
        )

        return {
            "internal_calls": len(calls) - len(external_dependencies),
            "external_calls": len(external_dependencies),
            "data_dependencies": len(data_dependencies),
            "dependency_graph": dependency_graph,
            "cyclic_dependencies": self._find_cyclic_dependencies(dependency_graph)
        }

    def _analyze_data_dependencies(self, ast_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """データ依存関係の分析"""
        dependencies = []
        data_items = ast_data.get('data_items', [])
        
        for item in data_items:
            if 'redefines' in item:
                dependencies.append({
                    'type': 'redefines',
                    'source': item['name'],
                    'target': item['redefines'],
                    'location': item.get('location')
                })
            
            if 'depends_on' in item:
                dependencies.append({
                    'type': 'depends_on',
                    'source': item['name'],
                    'target': item['depends_on'],
                    'location': item.get('location')
                })

        return dependencies

    def _is_internal_module(self, module_name: str) -> bool:
        """内部モジュールかどうかの判定"""
        internal_prefixes = ['INT-', 'LOC-', 'SELF-']
        return any(module_name.startswith(prefix) for prefix in internal_prefixes)

    def _build_dependency_graph(self,
                              calls: List[Dict[str, Any]],
                              data_dependencies: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
        """依存関係グラフの構築"""
        graph = defaultdict(set)
        
        for call in calls:
            graph[call['source']].add(call['target'])
        
        for dep in data_dependencies:
            graph[dep['source']].add(dep['target'])
        
        return dict(graph)

    def _find_cyclic_dependencies(self, graph: Dict[str, Set[str]]) -> List[List[str]]:
        """循環依存関係の検出"""
        cycles = []
        visited = set()
        path = []
        
        def dfs(node: str):
            if node in path:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:])
                return
            
            if node in visited:
                return
            
            visited.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                dfs(neighbor)
            
            path.pop()
        
        for node in graph:
            if node not in visited:
                dfs(node)
        
        return cycles

    async def _analyze_components(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """コンポーネント分析"""
        paragraphs = ast_data.get('paragraphs', [])
        sections = ast_data.get('sections', [])
        
        # コンポーネントサイズの分析
        component_sizes = {
            'large_paragraphs': [p for p in paragraphs if len(p.get('statements', [])) > 50],
            'large_sections': [s for s in sections if len(s.get('paragraphs', [])) > 10]
        }
        
        # コンポーネント結合度の分析
        coupling_analysis = await self._analyze_component_coupling(paragraphs)
        
        return {
            "component_count": len(paragraphs) + len(sections),
            "oversized_components": {
                "paragraphs": len(component_sizes['large_paragraphs']),
                "sections": len(component_sizes['large_sections'])
            },
            "coupling_metrics": coupling_analysis,
            "recommendations": self._generate_component_recommendations(
                component_sizes,
                coupling_analysis
            )
        }

    async def _analyze_component_coupling(self,
                                       paragraphs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """コンポーネント結合度の分析"""
        coupling_metrics = {
            'data_coupling': 0,
            'control_coupling': 0,
            'temporal_coupling': 0
        }
        
        for para in paragraphs:
            # データ結合のチェック
            data_refs = self._find_data_references(para)
            coupling_metrics['data_coupling'] += len(data_refs)
            
            # 制御結合のチェック
            control_deps = self._find_control_dependencies(para)
            coupling_metrics['control_coupling'] += len(control_deps)
            
            # 時間的結合のチェック
            temporal_deps = self._find_temporal_dependencies(para)
            coupling_metrics['temporal_coupling'] += len(temporal_deps)
        
        return coupling_metrics

    def _find_data_references(self, paragraph: Dict[str, Any]) -> List[str]:
        """データ参照の検出"""
        refs = set()
        for stmt in paragraph.get('statements', []):
            if 'references' in stmt:
                refs.update(stmt['references'])
        return list(refs)

    def _find_control_dependencies(self, paragraph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """制御依存関係の検出"""
        control_deps = []
        for stmt in paragraph.get('statements', []):
            if stmt.get('type') in ['IF', 'EVALUATE', 'PERFORM']:
                control_deps.append({
                    'type': stmt['type'],
                    'target': stmt.get('target'),
                    'location': stmt.get('location')
                })
        return control_deps

    def _find_temporal_dependencies(self, paragraph: Dict[str, Any]) -> List[Dict[str, Any]]:
        """時間的依存関係の検出"""
        temporal_deps = []
        statement_sequence = paragraph.get('statements', [])
        
        for i in range(len(statement_sequence) - 1):
            curr_stmt = statement_sequence[i]
            next_stmt = statement_sequence[i + 1]
            
            if self._has_temporal_dependency(curr_stmt, next_stmt):
                temporal_deps.append({
                    'source': curr_stmt.get('label'),
                    'target': next_stmt.get('label'),
                    'type': 'sequence_dependency'
                })
        
        return temporal_deps

    def _has_temporal_dependency(self,
                               stmt1: Dict[str, Any],
                               stmt2: Dict[str, Any]) -> bool:
        """時間的依存関係の判定"""
        # 特定のステートメントパターンをチェック
        if stmt1.get('type') in ['OPEN', 'READ'] and stmt2.get('type') in ['WRITE', 'CLOSE']:
            return True
        if stmt1.get('type') == 'MOVE' and stmt2.get('type') in ['DISPLAY', 'COMPUTE']:
            return True
        return False

    def _calculate_modularity_score(self,
                                  dependencies: Dict[str, Any],
                                  components: Dict[str, Any],
                                  cohesion: Dict[str, Any],
                                  coupling: Dict[str, Any]) -> float:
        """モジュール性スコアの計算"""
        # 依存関係スコア（0-1）
        dep_score = 1.0 - min(1.0, len(dependencies['cyclic_dependencies']) / 10.0)
        
        # コンポーネントスコア（0-1）
        comp_score = 1.0 - (
            components['oversized_components']['paragraphs'] +
            components['oversized_components']['sections']
        ) / max(1, components['component_count'])
        
        # 凝集度スコア（0-1）
        cohesion_score = cohesion.get('score', 0.0)
        
        # 結合度スコア（0-1）、低いほど良い
        coupling_score = 1.0 - min(1.0, (
            coupling['data_coupling'] +
            coupling['control_coupling'] * 2 +
            coupling['temporal_coupling'] * 3
        ) / (100.0 * 4))
        
        # 重み付けされた合計スコア（0-100）
        return (
            dep_score * 0.3 +
            comp_score * 0.2 +
            cohesion_score * 0.3 +
            coupling_score * 0.2
        ) * 100.0

    def _generate_modularity_recommendations(self,
                                          dependencies: Dict[str, Any],
                                          components: Dict[str, Any],
                                          cohesion: Dict[str, Any],
                                          coupling: Dict[str, Any]) -> List[Dict[str, Any]]:
        """モジュール性の改善推奨事項生成"""
        recommendations = []
        
        # 循環依存関係の改善提案
        if dependencies['cyclic_dependencies']:
            recommendations.append({
                'type': 'cyclic_dependency',
                'severity': 'high',
                'description': '循環依存関係を解消してください',
                'details': dependencies['cyclic_dependencies'],
                'remedy': '依存関係の方向を一方向に整理し、必要に応じてモジュールを分割してください'
            })
        
        # 大きなコンポーネントの分割提案
        if components['oversized_components']['paragraphs'] > 0:
            recommendations.append({
                'type': 'large_component',
                'severity': 'medium',
                'description': '大きすぎるパラグラフを分割してください',
                'count': components['oversized_components']['paragraphs'],
                'remedy': '機能単位で小さなパラグラフに分割し、関連する処理をグループ化してください'
            })
        
        # 結合度の改善提案
        high_coupling_types = []
        if coupling['data_coupling'] > 20:
            high_coupling_types.append('データ結合')
        if coupling['control_coupling'] > 10:
            high_coupling_types.append('制御結合')
        if coupling['temporal_coupling'] > 5:
            high_coupling_types.append('時間的結合')
        
        if high_coupling_types:
            recommendations.append({
                'type': 'high_coupling',
                'severity': 'medium',
                'description': f'以下の結合を減らしてください: {", ".join(high_coupling_types)}',
                'coupling_metrics': coupling,
                'remedy': 'インターフェースを明確にし、不要な依存関係を削除してください'
            })
        
        return recommendations

    def __del__(self):
        """リソースのクリーンアップ"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)
