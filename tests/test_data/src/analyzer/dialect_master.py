from typing import Dict, Any, List
from dataclasses import dataclass
import json
import os

@dataclass
class DialectMaster:
    """メーカー依存構文のマスタ情報"""
    vendor: str
    version: str
    statements: Dict[str, Any]
    parameters: Dict[str, Any]
    reserved_words: List[str]

class DialectMasterManager:
    """メーカー依存構文のマスタ管理"""
    
    def __init__(self, master_dir: str = "masters/dialects"):
        self._master_dir = master_dir
        self._masters: Dict[str, DialectMaster] = {}
        self._load_masters()

    def _load_masters(self):
        """マスタ情報の読み込み"""
        vendors = ['IBM', 'HITACHI', 'FUJITSU', 'NEC', 'UNISYS']
        
        for vendor in vendors:
            master_file = os.path.join(self._master_dir, f"{vendor.lower()}_dialect.json")
            if os.path.exists(master_file):
                with open(master_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._masters[vendor] = DialectMaster(
                        vendor=vendor,
                        version=data.get('version', '1.0'),
                        statements=data.get('statements', {}),
                        parameters=data.get('parameters', {}),
                        reserved_words=data.get('reserved_words', [])
                    )

    def get_master(self, vendor: str) -> DialectMaster:
        """メーカーのマスタ情報取得"""
        return self._masters.get(vendor)

    def validate_statement(self, vendor: str, statement: str) -> bool:
        """構文の妥当性検証"""
        master = self.get_master(vendor)
        if not master:
            return False
            
        return statement in master.statements

    def get_statement_info(self, vendor: str, statement: str) -> Dict[str, Any]:
        """構文情報の取得"""
        master = self.get_master(vendor)
        if not master:
            return {}
            
        return master.statements.get(statement, {})

    def get_parameter_info(self, vendor: str, parameter: str) -> Dict[str, Any]:
        """パラメータ情報の取得"""
        master = self.get_master(vendor)
        if not master:
            return {}
            
        return master.parameters.get(parameter, {}) 