from typing import Dict, Any, List, Optional
import aiohttp
import logging
import json
from datetime import datetime
from .analysis_engine import AnalysisResult

logger = logging.getLogger(__name__)

class AIAnalyzer:
    """AI/RAG連携による解析機能"""
    
    def __init__(self, ai_server_url: str = "http://172.16.0.19:8000"):
        self.ai_server_url = ai_server_url
        self.prompt_endpoint = f"{ai_server_url}/api/v1/prompt"
        self.analysis_endpoint = f"{ai_server_url}/api/v1/analyze"

    async def analyze_with_ai(self, analysis_results: List[AnalysisResult]) -> Dict[str, Any]:
        """AI解析の実行"""
        try:
            # 解析データの準備
            analysis_data = self._prepare_analysis_data(analysis_results)
            
            # AI/RAGサーバーへのリクエスト
            async with aiohttp.ClientSession() as session:
                # プロンプトの生成
                prompt = await self._generate_prompt(session, analysis_data)
                
                # AI解析の実行
                ai_analysis = await self._execute_analysis(session, prompt, analysis_data)
                
                return ai_analysis
        except Exception as e:
            logger.error(f"AI解析でエラー: {str(e)}")
            return {}

    def _prepare_analysis_data(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """解析データの準備"""
        return {
            'timestamp': datetime.now().isoformat(),
            'analysis_count': len(results),
            'metrics_summary': self._summarize_metrics(results),
            'quality_metrics': self._summarize_quality_metrics(results),
            'patterns': self._extract_patterns(results),
            'dependencies': self._extract_dependencies(results)
        }

    def _summarize_metrics(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """メトリクスのサマリ作成"""
        summary = {
            'total_lines': 0,
            'total_code_lines': 0,
            'total_comment_lines': 0,
            'complexity_scores': [],
            'division_stats': {
                'IDENTIFICATION': {'total': 0},
                'ENVIRONMENT': {'total': 0},
                'DATA': {'total': 0},
                'PROCEDURE': {'total': 0}
            }
        }
        
        for result in results:
            metrics = result.metrics
            summary['total_lines'] += metrics.get('total_lines', 0)
            summary['total_code_lines'] += metrics.get('code_lines', 0)
            summary['total_comment_lines'] += metrics.get('comment_lines', 0)
            
            if complexity := metrics.get('complexity_metrics', {}).get('cyclomatic_complexity'):
                summary['complexity_scores'].append(complexity)
            
            for div_name, stats in metrics.get('division_stats', {}).items():
                summary['division_stats'][div_name]['total'] += stats.get('total_lines', 0)
        
        return summary

    def _summarize_quality_metrics(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """品質メトリクスのサマリ作成"""
        quality_summary = {
            'maintainability_scores': [],
            'reliability_scores': [],
            'documentation_scores': [],
            'common_issues': {}
        }
        
        for result in results:
            quality = result.details.get('quality_metrics', {})
            
            if maintainability := quality.get('maintainability', {}).get('complexity_score', {}).get('value'):
                quality_summary['maintainability_scores'].append(maintainability)
            
            if reliability := quality.get('reliability', {}).get('error_handling', {}).get('coverage'):
                quality_summary['reliability_scores'].append(reliability)
            
            if documentation := quality.get('maintainability', {}).get('documentation', {}).get('comment_ratio'):
                quality_summary['documentation_scores'].append(documentation)
            
            # 共通の問題点を集計
            for issue in quality.get('potential_issues', {}).values():
                issue_type = issue.get('type')
                if issue_type:
                    quality_summary['common_issues'][issue_type] = \
                        quality_summary['common_issues'].get(issue_type, 0) + 1
        
        return quality_summary

    def _extract_patterns(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """パターンの抽出"""
        patterns = {
            'code_patterns': {},
            'structure_patterns': {},
            'naming_patterns': {}
        }
        
        for result in results:
            details = result.details
            if common_patterns := details.get('common_patterns'):
                for category, category_patterns in common_patterns.items():
                    if category in patterns:
                        for pattern_type, pattern_data in category_patterns.items():
                            if pattern_type not in patterns[category]:
                                patterns[category][pattern_type] = {}
                            for pattern, count in pattern_data.items():
                                patterns[category][pattern_type][pattern] = \
                                    patterns[category][pattern_type].get(pattern, 0) + count
        
        return patterns

    def _extract_dependencies(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """依存関係の抽出"""
        dependencies = {
            'program_calls': {},
            'data_dependencies': {},
            'file_dependencies': {}
        }
        
        for result in results:
            details = result.details
            if cross_refs := details.get('cross_references'):
                # プログラム呼び出し
                for program, calls in cross_refs.get('program_calls', {}).items():
                    if program not in dependencies['program_calls']:
                        dependencies['program_calls'][program] = {
                            'calls': set(),
                            'called_by': set()
                        }
                    dependencies['program_calls'][program]['calls'].update(calls.get('calls', []))
                    dependencies['program_calls'][program]['called_by'].update(calls.get('called_by', []))
                
                # データ依存関係
                for data_item, refs in cross_refs.get('data_dependencies', {}).items():
                    if data_item not in dependencies['data_dependencies']:
                        dependencies['data_dependencies'][data_item] = set()
                    dependencies['data_dependencies'][data_item].update(refs.get('referenced_by', []))
                
                # ファイル依存関係
                for file_name, access in cross_refs.get('file_dependencies', {}).items():
                    if file_name not in dependencies['file_dependencies']:
                        dependencies['file_dependencies'][file_name] = set()
                    dependencies['file_dependencies'][file_name].update(access.get('accessed_by', []))
        
        # setをリストに変換（JSON化のため）
        for program in dependencies['program_calls'].values():
            program['calls'] = list(program['calls'])
            program['called_by'] = list(program['called_by'])
        
        for data_item in dependencies['data_dependencies']:
            dependencies['data_dependencies'][data_item] = \
                list(dependencies['data_dependencies'][data_item])
        
        for file_name in dependencies['file_dependencies']:
            dependencies['file_dependencies'][file_name] = \
                list(dependencies['file_dependencies'][file_name])
        
        return dependencies

    async def _generate_prompt(self, 
                             session: aiohttp.ClientSession, 
                             analysis_data: Dict[str, Any]) -> str:
        """プロンプトの生成"""
        try:
            async with session.post(
                self.prompt_endpoint,
                json={
                    'template_name': 'cobol_analysis',
                    'parameters': analysis_data,
                    'prompt_type': 'ANALYSIS'
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('prompt', '')
                else:
                    logger.error(f"プロンプト生成でエラー: {response.status}")
                    return ''
        except Exception as e:
            logger.error(f"プロンプト生成でエラー: {str(e)}")
            return ''

    async def _execute_analysis(self, 
                              session: aiohttp.ClientSession,
                              prompt: str,
                              analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """AI解析の実行"""
        try:
            async with session.post(
                self.analysis_endpoint,
                json={
                    'prompt': prompt,
                    'analysis_data': analysis_data
                }
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"AI解析でエラー: {response.status}")
                    return {}
        except Exception as e:
            logger.error(f"AI解析でエラー: {str(e)}")
            return {} 