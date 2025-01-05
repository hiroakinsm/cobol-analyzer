from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
from dataclasses import dataclass
import json
import inspect
import os
from pathlib import Path
import markdown
import jinja2
import yaml

logger = logging.getLogger(__name__)

@dataclass
class DocumentConfig:
    """ドキュメント生成の設定"""
    output_dir: str = "docs"
    template_dir: str = "templates"
    format: str = "html"
    include_tests: bool = True
    include_metrics: bool = True
    version: str = "1.0.0"

class DocumentationGenerator:
    """ドキュメント生成を管理するクラス"""
    
    def __init__(self, config: DocumentConfig):
        self.config = config
        self._template_env = self._setup_template_env()
        self._docs_data: Dict[str, Any] = {}
        self._ensure_directories()

    def _setup_template_env(self) -> jinja2.Environment:
        """テンプレートエンジンの設定"""
        try:
            template_loader = jinja2.FileSystemLoader(self.config.template_dir)
            env = jinja2.Environment(
                loader=template_loader,
                autoescape=True
            )
            return env
        except Exception as e:
            logger.error(f"テンプレート設定でエラー: {str(e)}")
            return None

    def _ensure_directories(self):
        """必要なディレクトリの作成"""
        try:
            os.makedirs(self.config.output_dir, exist_ok=True)
            os.makedirs(self.config.template_dir, exist_ok=True)
        except Exception as e:
            logger.error(f"ディレクトリ作成でエラー: {str(e)}")

    def generate_api_docs(self, modules: List[Any]) -> str:
        """APIドキュメントの生成"""
        try:
            api_docs = []
            
            for module in modules:
                module_docs = self._generate_module_docs(module)
                api_docs.append(module_docs)
            
            # テンプレートの適用
            template = self._template_env.get_template('api_docs.html')
            output = template.render(
                api_docs=api_docs,
                version=self.config.version,
                generated_at=datetime.now().isoformat()
            )
            
            # ファイルの保存
            output_path = os.path.join(self.config.output_dir, 'api_docs.html')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output)
            
            return output_path
        except Exception as e:
            logger.error(f"APIドキュメント生成でエラー: {str(e)}")
            return ""

    def generate_test_report(self, test_results: Dict[str, Any]) -> str:
        """テストレポートの生成"""
        try:
            # テストデータの整形
            report_data = self._format_test_results(test_results)
            
            # テンプレートの適用
            template = self._template_env.get_template('test_report.html')
            output = template.render(
                test_results=report_data,
                version=self.config.version,
                generated_at=datetime.now().isoformat()
            )
            
            # ファイルの保存
            output_path = os.path.join(self.config.output_dir, 'test_report.html')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output)
            
            return output_path
        except Exception as e:
            logger.error(f"テストレポート生成でエラー: {str(e)}")
            return ""

    def generate_metrics_report(self, metrics_data: Dict[str, Any]) -> str:
        """メトリクスレポートの生成"""
        try:
            # メトリクスデータの整形
            report_data = self._format_metrics_data(metrics_data)
            
            # テンプレートの適用
            template = self._template_env.get_template('metrics_report.html')
            output = template.render(
                metrics_data=report_data,
                version=self.config.version,
                generated_at=datetime.now().isoformat()
            )
            
            # ファイルの保存
            output_path = os.path.join(self.config.output_dir, 'metrics_report.html')
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output)
            
            return output_path
        except Exception as e:
            logger.error(f"メトリクスレポート生成でエラー: {str(e)}")
            return ""

    def _generate_module_docs(self, module: Any) -> Dict[str, Any]:
        """モジュールのドキュメント生成"""
        try:
            module_info = {
                'name': module.__name__,
                'doc': inspect.getdoc(module),
                'classes': [],
                'functions': []
            }
            
            # クラスの解析
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if obj.__module__ == module.__name__:
                    class_info = self._analyze_class(obj)
                    module_info['classes'].append(class_info)
            
            # 関数の解析
            for name, obj in inspect.getmembers(module, inspect.isfunction):
                if obj.__module__ == module.__name__:
                    func_info = self._analyze_function(obj)
                    module_info['functions'].append(func_info)
            
            return module_info
        except Exception as e:
            logger.error(f"モジュールドキュメント生成でエラー: {str(e)}")
            return {}

    def _analyze_class(self, cls: Any) -> Dict[str, Any]:
        """クラスの解析"""
        try:
            return {
                'name': cls.__name__,
                'doc': inspect.getdoc(cls),
                'methods': [
                    self._analyze_function(func)
                    for name, func in inspect.getmembers(cls, inspect.isfunction)
                    if not name.startswith('_')
                ],
                'attributes': [
                    {'name': name, 'type': type(attr).__name__}
                    for name, attr in vars(cls).items()
                    if not name.startswith('_')
                ]
            }
        except Exception as e:
            logger.error(f"クラス解析でエラー: {str(e)}")
            return {}

    def _analyze_function(self, func: Any) -> Dict[str, Any]:
        """関数の解析"""
        try:
            signature = inspect.signature(func)
            return {
                'name': func.__name__,
                'doc': inspect.getdoc(func),
                'parameters': [
                    {
                        'name': name,
                        'type': param.annotation.__name__ 
                            if param.annotation != inspect.Parameter.empty 
                            else 'Any',
                        'default': str(param.default) 
                            if param.default != inspect.Parameter.empty 
                            else None
                    }
                    for name, param in signature.parameters.items()
                ],
                'return_type': signature.return_annotation.__name__
                    if signature.return_annotation != inspect.Signature.empty
                    else 'None'
            }
        except Exception as e:
            logger.error(f"関数解析でエラー: {str(e)}")
            return {}

    def _format_test_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """テスト結果の整形"""
        try:
            formatted = {
                'summary': results.get('summary', {}),
                'details': []
            }
            
            for test_type, data in results.get('results', {}).items():
                if isinstance(data, dict):
                    formatted['details'].append({
                        'type': test_type,
                        'passed': data.get('passed', 0),
                        'failed': data.get('failed', 0),
                        'details': data.get('details', [])
                    })
            
            return formatted
        except Exception as e:
            logger.error(f"テスト結果整形でエラー: {str(e)}")
            return {}

    def _format_metrics_data(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """メトリクスデータの整形"""
        try:
            return {
                'system': metrics.get('system', {}),
                'performance': metrics.get('performance', {}),
                'errors': metrics.get('errors', {}),
                'summary': {
                    'total_requests': sum(
                        metrics.get('performance', {}).get('requests', [0])
                    ),
                    'average_response_time': sum(
                        metrics.get('performance', {}).get('response_times', [0])
                    ) / len(metrics.get('performance', {}).get('response_times', [1])),
                    'error_rate': len(
                        metrics.get('errors', {})
                    ) / max(sum(
                        metrics.get('performance', {}).get('requests', [1])
                    ), 1)
                }
            }
        except Exception as e:
            logger.error(f"メトリクスデータ整形でエラー: {str(e)}")
            return {} 