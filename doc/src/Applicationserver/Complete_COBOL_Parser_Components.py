# /home/administrator/cobol-analyzer/src/parser/components.py

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

# 基本的なデータ型定義
class COBOLValueType(Enum):
    NUMERIC = "numeric"
    ALPHANUMERIC = "alphanumeric"
    ALPHABETIC = "alphabetic"
    GROUP = "group"
    INDEX = "index"
    POINTER = "pointer"
    PROCEDURE_POINTER = "procedure-pointer"
    FUNCTION_POINTER = "function-pointer"
    OBJECT_REFERENCE = "object-reference"

class UsageType(Enum):
    DISPLAY = "display"
    COMP = "comp"
    COMP_1 = "comp-1"
    COMP_2 = "comp-2"
    COMP_3 = "comp-3"
    COMP_4 = "comp-4"
    COMP_5 = "comp-5"
    POINTER = "pointer"
    FUNCTION_POINTER = "function-pointer"
    PROCEDURE_POINTER = "procedure-pointer"
    OBJECT_REFERENCE = "object-reference"

class SynchronizationType(Enum):
    LEFT = "left"
    RIGHT = "right"

# IDENTIFICATION DIVISION
@dataclass
class IdentificationDivision:
    program_id: str
    author: Optional[str] = None
    installation: Optional[str] = None
    date_written: Optional[datetime] = None
    date_compiled: Optional[datetime] = None
    security: Optional[str] = None
    remarks: List[str] = field(default_factory=list)

# ENVIRONMENT DIVISION
@dataclass
class SourceComputer:
    name: str
    debug_mode: bool = False

@dataclass
class ObjectComputer:
    name: str
    memory_size: Optional[int] = None
    sequence: Optional[str] = None
    segment_limit: Optional[int] = None

@dataclass
class SpecialNames:
    currency_sign: Optional[str] = None
    decimal_point: Optional[str] = None
    symbolic_characters: Dict[str, str] = field(default_factory=dict)
    class_definitions: Dict[str, List[str]] = field(default_factory=dict)

@dataclass
class FileControlEntry:
    file_name: str
    assign_to: str
    organization: str
    access_mode: str
    record_key: Optional[str] = None
    alternate_keys: List[str] = field(default_factory=list)
    file_status: Optional[str] = None

@dataclass
class IOControlEntry:
    same_area: List[str] = field(default_factory=list)
    multiple_file_tapes: Dict[str, List[str]] = field(default_factory=dict)
    apply_write_only: List[str] = field(default_factory=list)

@dataclass
class EnvironmentDivision:
    source_computer: Optional[SourceComputer] = None
    object_computer: Optional[ObjectComputer] = None
    special_names: Optional[SpecialNames] = None
    file_control: List[FileControlEntry] = field(default_factory=list)
    io_control: Optional[IOControlEntry] = None

# DATA DIVISION
@dataclass
class PictureClause:
    picture_string: str
    character_type: str
    length: int
    decimals: Optional[int] = None
    usage: Optional[UsageType] = None
    sign_position: Optional[str] = None
    synchronized: Optional[SynchronizationType] = None
    justified: bool = False
    blank_when_zero: bool = False

@dataclass
class DataItem:
    level: int
    name: str
    picture: Optional[PictureClause] = None
    usage: Optional[UsageType] = None
    value: Optional[Any] = None
    occurs: Optional[int] = None
    occurs_depending_on: Optional[str] = None
    indexed_by: List[str] = field(default_factory=list)
    redefines: Optional[str] = None
    synchronized: Optional[SynchronizationType] = None
    justified: bool = False
    blank_when_zero: bool = False
    external: bool = False
    global_item: bool = False
    children: List['DataItem'] = field(default_factory=list)

@dataclass
class FileDescription:
    file_name: str
    record_description: List[DataItem]
    block_contains: Optional[int] = None
    record_contains: Optional[int] = None
    label_records: Optional[str] = None
    value_of: Dict[str, str] = field(default_factory=dict)
    data_records: List[str] = field(default_factory=list)
    linage: Optional[Dict[str, Any]] = None

@dataclass
class DataDivision:
    file_section: List[FileDescription] = field(default_factory=list)
    working_storage: List[DataItem] = field(default_factory=list)
    local_storage: List[DataItem] = field(default_factory=list)
    linkage_section: List[DataItem] = field(default_factory=list)
    screen_section: List[DataItem] = field(default_factory=list)
    report_section: List[Any] = field(default_factory=list)

# PROCEDURE DIVISION
class StatementType(Enum):
    ACCEPT = "accept"
    ADD = "add"
    ALTER = "alter"
    CALL = "call"
    CANCEL = "cancel"
    CLOSE = "close"
    COMPUTE = "compute"
    CONTINUE = "continue"
    DELETE = "delete"
    DISPLAY = "display"
    DIVIDE = "divide"
    ENTRY = "entry"
    EVALUATE = "evaluate"
    EXIT = "exit"
    GO = "go"
    GOBACK = "goback"
    IF = "if"
    INITIALIZE = "initialize"
    INVOKE = "invoke"
    MERGE = "merge"
    MOVE = "move"
    MULTIPLY = "multiply"
    OPEN = "open"
    PERFORM = "perform"
    READ = "read"
    RELEASE = "release"
    RETURN = "return"
    REWRITE = "rewrite"
    SEARCH = "search"
    SET = "set"
    SORT = "sort"
    START = "start"
    STOP = "stop"
    STRING = "string"
    SUBTRACT = "subtract"
    UNSTRING = "unstring"
    WRITE = "write"

@dataclass
class Condition:
    left_operand: str
    operator: str
    right_operand: str
    and_conditions: List['Condition'] = field(default_factory=list)
    or_conditions: List['Condition'] = field(default_factory=list)

@dataclass
class Statement:
    statement_type: StatementType
    line_number: int
    operands: List[str] = field(default_factory=list)
    condition: Optional[Condition] = None
    nested_statements: List['Statement'] = field(default_factory=list)

@dataclass
class Paragraph:
    name: str
    statements: List[Statement] = field(default_factory=list)

@dataclass
class Section:
    name: str
    paragraphs: List[Paragraph] = field(default_factory=list)

@dataclass
class ProcedureDivision:
    using_parameters: List[str] = field(default_factory=list)
    giving_parameters: List[str] = field(default_factory=list)
    declaratives: List[Section] = field(default_factory=list)
    sections: List[Section] = field(default_factory=list)

# 完全なCOBOLプログラム構造
@dataclass
class COBOLProgram:
    identification: IdentificationDivision
    environment: Optional[EnvironmentDivision]
    data: Optional[DataDivision]
    procedure: ProcedureDivision

# COBOLパーサー
class COBOLParser:
    def __init__(self):
        self.current_program: Optional[COBOLProgram] = None
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def parse(self, source_code: str) -> COBOLProgram:
        """COBOLソースコードを解析してプログラム構造を生成"""
        try:
            self._tokenize(source_code)
            self._parse_identification_division()
            self._parse_environment_division()
            self._parse_data_division()
            self._parse_procedure_division()
            return self.current_program
        except Exception as e:
            self.errors.append(f"Parse error: {str(e)}")
            raise

    def _tokenize(self, source_code: str) -> List[str]:
        """ソースコードをトークンに分割"""
        tokens = []
        current_pos = 0
        line_number = 1
    
        try:
            lines = source_code.splitlines()
        
            for line in lines:
                # 行番号の処理
                if len(line) >= 6:
                    # シーケンス番号領域のスキップ (1-6列)
                    content = line[6:]
                
                    # 継続行の処理
                    if line[6] == '-':
                        content = line[7:]
                
                    # コメント行のスキップ
                    if content.strip() and content[0] in ['*', '/']:
                        line_number += 1
                        continue
                
                    # トークンの抽出
                    words = content.split()
                    for word in words:
                        tokens.append({
                            'value': word.strip('.'),
                            'line': line_number,
                            'column': content.find(word) + 7
                        })
            
                line_number += 1
            
            return tokens
        
        except Exception as e:
            self.errors.append(f"Tokenization error at line {line_number}: {str(e)}")
            raise

    def _parse_identification_division(self) -> None:
        """IDENTIFICATION DIVISIONの解析"""
        try:
            # 必要なトークンが見つかるまでスキップ
            while self.current_token and not self._is_division_header('IDENTIFICATION'):
                self._next_token()
            
            if not self.current_token:
                raise ValueError("IDENTIFICATION DIVISION not found")

            # IDENTIFICATION DIVISION処理
            identification = IdentificationDivision(program_id="")  # 初期化

            # 各パラグラフの処理
            while self.current_token:
                token_value = self.current_token['value'].upper()
            
                if self._is_division_header('ENVIRONMENT'):
                    break
                
                if token_value == 'PROGRAM-ID':
                    self._next_token()  # PROGRAM-IDの次のトークンへ
                    identification.program_id = self.current_token['value']
            
                elif token_value == 'AUTHOR':
                    self._next_token()
                    identification.author = self._collect_until_next_paragraph()
            
                elif token_value == 'INSTALLATION':
                    self._next_token()
                    identification.installation = self._collect_until_next_paragraph()
            
                elif token_value == 'DATE-WRITTEN':
                    self._next_token()
                    date_str = self._collect_until_next_paragraph()
                    try:
                        identification.date_written = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        self.warnings.append(f"Invalid DATE-WRITTEN format: {date_str}")
            
                elif token_value == 'DATE-COMPILED':
                    self._next_token()
                    date_str = self._collect_until_next_paragraph()
                    try:
                        identification.date_compiled = datetime.strptime(date_str, "%Y-%m-%d")
                    except ValueError:
                        self.warnings.append(f"Invalid DATE-COMPILED format: {date_str}")
            
                elif token_value == 'SECURITY':
                    self._next_token()
                    identification.security = self._collect_until_next_paragraph()
            
                elif token_value == 'REMARKS':
                    self._next_token()
                    remarks = self._collect_until_next_paragraph()
                    identification.remarks.append(remarks)
            
                self._next_token()

            if not identification.program_id:
                raise ValueError("PROGRAM-ID is required but not found")

            self.current_program = COBOLProgram(
                identification=identification,
                environment=None,
                data=None,
                procedure=None
            )

        except Exception as e:
            self.errors.append(f"Error parsing IDENTIFICATION DIVISION: {str(e)}")
            raise

    def _is_division_header(self, division_name: str) -> bool:
        """DIVISION headerのチェック"""
        return (self.current_token and 
                self.current_token['value'].upper() == division_name and 
                self._peek_next_token()['value'].upper() == 'DIVISION')

    def _collect_until_next_paragraph(self) -> str:
        """次のパラグラフまでの内容を収集"""
        content = []
        while (self.current_token and 
               not self.current_token['value'].upper().endswith('DIVISION') and
               not self.current_token['value'].isupper()):
            content.append(self.current_token['value'])
            self._next_token()
        return ' '.join(content).strip()

    def _next_token(self) -> None:
        """次のトークンに進む"""
        if self.token_index < len(self.tokens) - 1:
            self.token_index += 1
            self.current_token = self.tokens[self.token_index]
        else:
            self.current_token = None

    def _peek_next_token(self) -> Optional[Dict[str, Any]]:
        """次のトークンを覗き見"""
        if self.token_index < len(self.tokens) - 1:
            return self.tokens[self.token_index + 1]
        return None

    def _parse_environment_division(self) -> None:
        """ENVIRONMENT DIVISIONの解析"""
        try:
            # ENVIRONMENT DIVISIONの開始を確認
            while self.current_token and not self._is_division_header('ENVIRONMENT'):
                self._next_token()
            
            if not self.current_token:
                return  # ENVIRONMENT DIVISIONは任意

            self._next_token()  # DIVISIONの次へ
        
            environment = EnvironmentDivision()
            current_section = None

            while self.current_token:
                token_value = self.current_token['value'].upper()

                # 次のDIVISIONの開始を検出
                if self._is_division_header('DATA'):
                    break

                # セクションの処理
                if token_value == 'CONFIGURATION' and self._peek_next_token()['value'].upper() == 'SECTION':
                    current_section = 'CONFIGURATION'
                    self._next_token(2)  # "CONFIGURATION SECTION"をスキップ
                    self._parse_configuration_section(environment)

                elif token_value == 'INPUT-OUTPUT' and self._peek_next_token()['value'].upper() == 'SECTION':
                    current_section = 'INPUT-OUTPUT'
                    self._next_token(2)  # "INPUT-OUTPUT SECTION"をスキップ
                    self._parse_input_output_section(environment)

                else:
                    self._next_token()

            self.current_program.environment = environment

        except Exception as e:
            self.errors.append(f"Error parsing ENVIRONMENT DIVISION: {str(e)}")
            raise

    def _parse_configuration_section(self, environment: EnvironmentDivision) -> None:
        """CONFIGURATION SECTIONの解析"""
        while self.current_token:
            token_value = self.current_token['value'].upper()

            if token_value == 'SOURCE-COMPUTER':
                self._next_token()
                name = self._collect_until('.')
                debug_mode = 'DEBUGGING' in name.upper()
                environment.source_computer = SourceComputer(
                    name=name.replace('DEBUGGING MODE', '').strip(),
                    debug_mode=debug_mode
                )

            elif token_value == 'OBJECT-COMPUTER':
                self._next_token()
                config = self._parse_object_computer()
                environment.object_computer = ObjectComputer(
                    name=config['name'],
                    memory_size=config.get('memory_size'),
                    sequence=config.get('sequence'),
                    segment_limit=config.get('segment_limit')
                )

            elif token_value == 'SPECIAL-NAMES':
                self._next_token()
                special_names = self._parse_special_names()
                environment.special_names = SpecialNames(
                    currency_sign=special_names.get('currency_sign'),
                    decimal_point=special_names.get('decimal_point'),
                    symbolic_characters=special_names.get('symbolic_characters', {}),
                    class_definitions=special_names.get('class_definitions', {})
                )

            elif token_value == 'INPUT-OUTPUT':
                break

            self._next_token()

    def _parse_input_output_section(self, environment: EnvironmentDivision) -> None:
        """INPUT-OUTPUT SECTIONの解析"""
        while self.current_token:
            token_value = self.current_token['value'].upper()

            if token_value == 'FILE-CONTROL':
                self._next_token()
                while self.current_token and not self._is_section_or_division():
                    file_control = self._parse_file_control_entry()
                    environment.file_control.append(file_control)

            elif token_value == 'I-O-CONTROL':
                self._next_token()
                io_control = self._parse_io_control()
                environment.io_control = io_control

            elif self._is_section_or_division():
                break

            self._next_token()

    def _parse_object_computer(self) -> Dict[str, Any]:
        """OBJECT-COMPUTER句の解析"""
        config = {'name': ''}
        while self.current_token and self.current_token['value'] != '.':
            token_value = self.current_token['value'].upper()
        
            if token_value == 'MEMORY':
                self._next_token()
                if self.current_token['value'].upper() == 'SIZE':
                    self._next_token()
                    config['memory_size'] = int(self.current_token['value'])

            elif token_value == 'SEQUENCE':
                self._next_token()
                config['sequence'] = self.current_token['value']

            elif token_value == 'SEGMENT-LIMIT':
                self._next_token()
                config['segment_limit'] = int(self.current_token['value'])

            else:
                if not config['name']:
                    config['name'] = token_value

            self._next_token()

        return config

    def _parse_special_names(self) -> Dict[str, Any]:
        """SPECIAL-NAMES句の解析"""
        special_names = {
            'currency_sign': None,
            'decimal_point': None,
            'symbolic_characters': {},
            'class_definitions': {}
        }

        while self.current_token and self.current_token['value'] != '.':
            token_value = self.current_token['value'].upper()

            if token_value == 'CURRENCY':
                self._next_token(2)  # "CURRENCY SIGN"をスキップ
                special_names['currency_sign'] = self.current_token['value']

            elif token_value == 'DECIMAL-POINT':
                self._next_token(2)  # "DECIMAL-POINT IS"をスキップ
                special_names['decimal_point'] = self.current_token['value']

            elif token_value == 'CLASS':
                class_name = self._next_token()['value']
                self._next_token()  # "IS"をスキップ
                values = self._collect_until('.')
                special_names['class_definitions'][class_name] = values.split()

            self._next_token()

        return special_names

    def _next_token(self, count: int = 1) -> Dict[str, Any]:
        """指定数だけトークンを進める"""
        for _ in range(count):
            if self.token_index < len(self.tokens) - 1:
                self.token_index += 1
                self.current_token = self.tokens[self.token_index]
        return self.current_token

    def _is_section_or_division(self) -> bool:
        """SECTIONまたはDIVISIONの開始をチェック"""
        return (self.current_token and 
                (self.current_token['value'].upper().endswith('SECTION') or 
                 self.current_token['value'].upper().endswith('DIVISION')))

    def _collect_until(self, terminator: str) -> str:
        """指定の終端文字までの内容を収集"""
        content = []
        while (self.current_token and 
               self.current_token['value'] != terminator):
            content.append(self.current_token['value'])
            self._next_token()
        return ' '.join(content)

    def _parse_data_division(self) -> None:
        """DATA DIVISIONの解析"""
        try:
            # DATA DIVISIONの開始を確認
            while self.current_token and not self._is_division_header('DATA'):
                self._next_token()
            
            if not self.current_token:
                return  # DATA DIVISIONは任意

            self._next_token()  # DIVISIONの次へ
        
            data_division = DataDivision()
            current_section = None

            while self.current_token:
                token_value = self.current_token['value'].upper()

                # 次のDIVISIONの開始を検出
                if self._is_division_header('PROCEDURE'):
                    break

                # セクションの処理
                if token_value == 'FILE' and self._peek_next_token()['value'].upper() == 'SECTION':
                    current_section = 'FILE'
                    self._next_token(2)  # "FILE SECTION"をスキップ
                    self._parse_file_section(data_division)

                elif token_value == 'WORKING-STORAGE' and self._peek_next_token()['value'].upper() == 'SECTION':
                    current_section = 'WORKING-STORAGE'
                    self._next_token(2)  # "WORKING-STORAGE SECTION"をスキップ
                    data_division.working_storage = self._parse_data_items()

                elif token_value == 'LOCAL-STORAGE' and self._peek_next_token()['value'].upper() == 'SECTION':
                    current_section = 'LOCAL-STORAGE'
                    self._next_token(2)  # "LOCAL-STORAGE SECTION"をスキップ
                    data_division.local_storage = self._parse_data_items()

                elif token_value == 'LINKAGE' and self._peek_next_token()['value'].upper() == 'SECTION':
                    current_section = 'LINKAGE'
                    self._next_token(2)  # "LINKAGE SECTION"をスキップ
                    data_division.linkage_section = self._parse_data_items()

                elif token_value == 'SCREEN' and self._peek_next_token()['value'].upper() == 'SECTION':
                    current_section = 'SCREEN'
                    self._next_token(2)  # "SCREEN SECTION"をスキップ
                    data_division.screen_section = self._parse_data_items()

                else:
                    self._next_token()

            self.current_program.data = data_division

        except Exception as e:
            self.errors.append(f"Error parsing DATA DIVISION: {str(e)}")
            raise

    def _parse_file_section(self, data_division: DataDivision) -> None:
        """FILE SECTIONの解析"""
        while self.current_token and not self._is_section_or_division():
            if self.current_token['value'].upper() == 'FD':
                file_description = self._parse_file_description()
                data_division.file_section.append(file_description)
            self._next_token()

    def _parse_file_description(self) -> FileDescription:
        """ファイル記述の解析"""
        self._next_token()  # FDの次へ
        file_name = self.current_token['value']
        fd = FileDescription(
            file_name=file_name,
            record_description=[],
            block_contains=None,
            record_contains=None,
            label_records=None,
            value_of={},
            data_records=[],
            linage=None
        )

        self._next_token()  # ファイル名の次へ

        while self.current_token and not self._is_data_item():
            token_value = self.current_token['value'].upper()

            if token_value == 'BLOCK':
                self._next_token(2)  # "BLOCK CONTAINS"をスキップ
                fd.block_contains = int(self.current_token['value'])

            elif token_value == 'RECORD':
                if self._peek_next_token()['value'].upper() == 'CONTAINS':
                    self._next_token(2)  # "RECORD CONTAINS"をスキップ
                    fd.record_contains = int(self.current_token['value'])

            elif token_value == 'LABEL':
                self._next_token(2)  # "LABEL RECORDS"をスキップ
                fd.label_records = self.current_token['value']

            elif token_value == 'VALUE':
                self._next_token(2)  # "VALUE OF"をスキップ
                name = self.current_token['value']
                self._next_token()  # ISをスキップ
                value = self.current_token['value']
                fd.value_of[name] = value

            elif token_value == 'DATA':
                self._next_token(2)  # "DATA RECORDS"をスキップ
                while self.current_token and self.current_token['value'] != '.':
                    fd.data_records.append(self.current_token['value'])
                    self._next_token()

            elif token_value == 'LINAGE':
                fd.linage = self._parse_linage_clause()

            self._next_token()

        # レコード記述の解析
        fd.record_description = self._parse_data_items()
        return fd

    def _parse_data_items(self) -> List[DataItem]:
        """データ項目の解析"""
        items = []
        level_stack = [(0, None)]  # (level, item)のスタック

        while self.current_token and not self._is_section_or_division():
            if not self._is_data_item():
                self._next_token()
                continue

            level = int(self.current_token['value'])
            self._next_token()

            # データ項目の作成
            item = DataItem(
                level=level,
                name=self.current_token['value'] if not self.current_token['value'].startswith('FILLER') else None,
                picture=None,
                usage=None,
                value=None,
                occurs=None,
                occurs_depending_on=None,
                indexed_by=[],
                redefines=None,
                synchronized=None,
                justified=False,
                blank_when_zero=False,
                external=False,
                global_item=False,
                children=[]
            )

            # 親子関係の設定
            while level_stack and level_stack[-1][0] >= level:
                level_stack.pop()
        
            if level_stack:
                parent = level_stack[-1][1]
                if parent:
                    parent.children.append(item)
                    item.parent = parent.name

            level_stack.append((level, item))

            # 項目の属性を解析
            self._parse_data_item_clauses(item)

            if level == 1 or not level_stack[:-1]:
                items.append(item)

            self._next_token()

        return items

    def _parse_data_item_clauses(self, item: DataItem) -> None:
        """データ項目の句の解析"""
        while self.current_token and self.current_token['value'] != '.':
            token_value = self.current_token['value'].upper()

            if token_value == 'PICTURE' or token_value == 'PIC':
                self._next_token()
                if self._peek_next_token()['value'].upper() == 'IS':
                    self._next_token()
                item.picture = self._parse_picture_clause()

            elif token_value == 'USAGE':
                self._next_token()
                if self._peek_next_token()['value'].upper() == 'IS':
                    self._next_token()
                item.usage = UsageType(self.current_token['value'].lower())

            elif token_value == 'VALUE':
                self._next_token()
                if self._peek_next_token()['value'].upper() == 'IS':
                    self._next_token()
                item.value = self._parse_value_clause()

            # 他の句の処理も同様に実装
            self._next_token()

    def _parse_picture_clause(self) -> PictureClause:
        """PICTURE句の解析"""
        picture_string = self.current_token['value']
        length = 0
        decimals = None
        char_type = ''

        # PIC文字列の解析ロジックを実装
        # 文字種の判定
        # 長さの計算
        # 小数部の判定

        return PictureClause(
            picture_string=picture_string,
            character_type=char_type,
            length=length,
            decimals=decimals,
            usage=None,
            sign_position=None,
            synchronized=None,
            justified=False,
            blank_when_zero=False
        )

    def _parse_procedure_division(self) -> None:
        """PROCEDURE DIVISIONの解析"""
        try:
            # PROCEDURE DIVISIONの開始を確認
            while self.current_token and not self._is_division_header('PROCEDURE'):
                self._next_token()
            
            if not self.current_token:
                raise ValueError("PROCEDURE DIVISION not found")

            self._next_token()  # DIVISIONの次へ
        
            procedure = ProcedureDivision()
        
            # USING句とGIVING句の解析
            if self.current_token and self.current_token['value'].upper() == 'USING':
                self._next_token()
                procedure.using_parameters = self._parse_parameters()
            
            if self.current_token and self.current_token['value'].upper() == 'GIVING':
                self._next_token()
                procedure.giving_parameters = self._parse_parameters()

            # DECLARATIVES
            if self.current_token and self.current_token['value'].upper() == 'DECLARATIVES':
                self._next_token()
                procedure.declaratives = self._parse_declaratives()

            # セクションとパラグラフの解析
            procedure.sections = self._parse_sections()
        
            self.current_program.procedure = procedure

        except Exception as e:
            self.errors.append(f"Error parsing PROCEDURE DIVISION: {str(e)}")
            raise

    def _parse_parameters(self) -> List[str]:
        """パラメータリストの解析"""
        parameters = []
        while self.current_token and self.current_token['value'] not in ['.', 'GIVING']:
            parameters.append(self.current_token['value'])
            self._next_token()
        return parameters

    def _parse_declaratives(self) -> List[Section]:
        """DECLARATIVESセクションの解析"""
        declaratives = []
    
        while self.current_token:
            if self.current_token['value'].upper() == 'END' and \
               self._peek_next_token()['value'].upper() == 'DECLARATIVES':
                self._next_token(2)  # "END DECLARATIVES"をスキップ
                break
            
            if self._is_section_header():
                section = self._parse_section()
                declaratives.append(section)
            else:
                self._next_token()
            
        return declaratives

    def _parse_sections(self) -> List[Section]:
        """セクションの解析"""
        sections = []
        current_section = None
    
        while self.current_token:
            token_value = self.current_token['value'].upper()
        
            if self._is_section_header():
                if current_section:
                    sections.append(current_section)
                current_section = Section(name=token_value, paragraphs=[])
                self._next_token(2)  # セクション名とSECTIONをスキップ
            
            elif token_value.endswith('.'):
                # パラグラフ名の検出
                paragraph = self._parse_paragraph()
                if current_section:
                    current_section.paragraphs.append(paragraph)
                elif paragraph:  # セクションに属さないパラグラフの場合
                    if not sections:
                        sections.append(Section(name="MAIN", paragraphs=[]))
                    sections[0].paragraphs.append(paragraph)
                
            else:
                self._next_token()
    
        if current_section:
            sections.append(current_section)
        
        return sections

    def _parse_paragraph(self) -> Paragraph:
        """パラグラフの解析"""
        name = self.current_token['value'].rstrip('.')
        statements = []
        self._next_token()
    
        while self.current_token and not self._is_paragraph_end():
            statement = self._parse_statement()
            if statement:
                statements.append(statement)
    
        return Paragraph(name=name, statements=statements)

    def _parse_statement(self) -> Optional[Statement]:
        """文の解析"""
        if not self.current_token:
            return None
        
        token_value = self.current_token['value'].upper()
    
        try:
            statement_type = StatementType(token_value)
        except ValueError:
            self._next_token()
            return None
    
        statement = Statement(
            statement_type=statement_type,
            line_number=self.current_token['line'],
            operands=[],
            condition=None,
            nested_statements=[]
        )
    
        self._next_token()
    
        # 条件付き文の解析
        if statement_type == StatementType.IF:
            statement.condition = self._parse_condition()
            statement.nested_statements = self._parse_if_body()
    
        # その他の文の解析
        else:
            while self.current_token and not self._is_statement_end():
                statement.operands.append(self.current_token['value'])
                self._next_token()
    
        return statement

    def _parse_condition(self) -> Condition:
        """条件式の解析"""
        condition = Condition(
            left_operand="",
            operator="",
            right_operand="",
            and_conditions=[],
            or_conditions=[]
        )
    
        # 左辺の解析
        condition.left_operand = self.current_token['value']
        self._next_token()
    
        # 演算子の解析
        condition.operator = self.current_token['value']
        self._next_token()
    
        # 右辺の解析
        condition.right_operand = self.current_token['value']
        self._next_token()
    
        # 複合条件の解析
        while self.current_token and not self._is_statement_end():
            if self.current_token['value'].upper() == 'AND':
                self._next_token()
                condition.and_conditions.append(self._parse_condition())
            elif self.current_token['value'].upper() == 'OR':
                self._next_token()
                condition.or_conditions.append(self._parse_condition())
            else:
                break
    
        return condition

    def _is_section_header(self) -> bool:
        """セクションヘッダーかどうかのチェック"""
        return (self.current_token and 
                self._peek_next_token() and 
                self._peek_next_token()['value'].upper() == 'SECTION')

    def _is_paragraph_end(self) -> bool:
        """パラグラフ終端のチェック"""
        return (not self.current_token or 
                self._is_section_header() or 
                (self.current_token['value'].endswith('.') and 
                 self._peek_next_token() and 
                 self._peek_next_token()['value'].isupper()))

    def _is_statement_end(self) -> bool:
        """文の終端のチェック"""
        return (not self.current_token or 
                self.current_token['value'].endswith('.') or 
                self._is_section_header() or 
                self._is_paragraph_end())

    def _parse_if_body(self) -> List[Statement]:
        """IF文の本体の解析"""
        statements = []
        while self.current_token and not self._is_statement_end():
            statement = self._parse_statement()
            if statement:
                statements.append(statement)
        return statements

# 構文解析器
class COBOLSyntaxAnalyzer:
    def analyze_syntax(self, program: COBOLProgram) -> List[Dict[str, Any]]:
        """プログラムの構文を解析して問題点を検出"""
        issues = []
        issues.extend(self._analyze_identification(program.identification))
        if program.environment:
            issues.extend(self._analyze_environment(program.environment))
        if program.data:
            issues.extend(self._analyze_data(program.data))
        issues.extend(self._analyze_procedure(program.procedure))
        return issues

    def _analyze_identification(self, division: IdentificationDivision) -> List[Dict[str, Any]]:
        """IDENTIFICATION DIVISIONの解析と問題点の検出"""
        issues = []
    
        try:
            # PROGRAM-IDの検証
            if not division.program_id:
                issues.append({
                    'severity': 'ERROR',
                    'type': 'IDENTIFICATION',
                    'message': 'PROGRAM-ID is required but not specified',
                    'location': None
                })
            elif not self._is_valid_program_id(division.program_id):
                issues.append({
                    'severity': 'WARNING',
                    'type': 'IDENTIFICATION',
                    'message': f'Invalid PROGRAM-ID format: {division.program_id}',
                    'location': None,
                    'recommendation': 'Program name should be 1-30 characters and follow COBOL naming rules'
                })

            # 日付フォーマットの検証
            if division.date_written:
                if not self._is_valid_date(division.date_written):
                    issues.append({
                        'severity': 'WARNING',
                        'type': 'IDENTIFICATION',
                        'message': f'Invalid DATE-WRITTEN format: {division.date_written}',
                        'location': None
                    })

            if division.date_compiled:
                if not self._is_valid_date(division.date_compiled):
                    issues.append({
                        'severity': 'WARNING',
                        'type': 'IDENTIFICATION',
                        'message': f'Invalid DATE-COMPILED format: {division.date_compiled}',
                        'location': None
                    })

            # 作者情報の検証
            if not division.author:
                issues.append({
                    'severity': 'INFO',
                    'type': 'IDENTIFICATION',
                    'message': 'AUTHOR information is not specified',
                    'location': None,
                    'recommendation': 'Consider adding author information for better maintainability'
                })

            # セキュリティレベルの検証
            if division.security:
                if not self._is_valid_security_level(division.security):
                    issues.append({
                        'severity': 'WARNING',
                        'type': 'IDENTIFICATION',
                        'message': f'Invalid or unclear security level: {division.security}',
                        'location': None,
                        'recommendation': 'Specify a clear security level (e.g., "CONFIDENTIAL", "PUBLIC")'
                    })

            # 備考の長さチェック
            for remark in division.remarks:
                if len(remark) > 1000:  # 任意の上限値
                    issues.append({
                        'severity': 'WARNING',
                        'type': 'IDENTIFICATION',
                        'message': 'REMARKS section is unusually long',
                        'location': None,
                        'recommendation': 'Consider splitting or shortening remarks for better readability'
                    })

        except Exception as e:
            issues.append({
                'severity': 'ERROR',
                'type': 'IDENTIFICATION',
                'message': f'Error analyzing IDENTIFICATION DIVISION: {str(e)}',
                'location': None
            })

        return issues

    def _is_valid_program_id(self, program_id: str) -> bool:
        """PROGRAM-IDの有効性チェック"""
        if not program_id:
            return False
        
        # プログラム名の長さチェック (COBOL標準に基づく)
        if len(program_id) > 30:
            return False
        
        # 先頭文字のチェック
        if not program_id[0].isalpha():
            return False
        
        # 使用可能文字のチェック
        valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_')
        return all(c in valid_chars for c in program_id.upper())

    def _is_valid_date(self, date_value: datetime) -> bool:
        """日付の有効性チェック"""
        try:
            # 日付範囲の妥当性チェック
            min_date = datetime(1900, 1, 1)
            max_date = datetime.now()
        
            return min_date <= date_value <= max_date
        except Exception:
            return False

    def _is_valid_security_level(self, security: str) -> bool:
        """セキュリティレベルの有効性チェック"""
        valid_levels = {
            'PUBLIC',
            'CONFIDENTIAL',
            'SECRET',
            'TOP SECRET',
            'RESTRICTED'
    }
        return security.upper() in valid_levels

    def _analyze_environment(self, division: EnvironmentDivision) -> List[Dict[str, Any]]:
        """ENVIRONMENT DIVISIONの解析と問題点の検出"""
        issues = []
    
        try:
            # SOURCE-COMPUTERセクションの解析
            if division.source_computer:
                issues.extend(self._analyze_source_computer(division.source_computer))

            # OBJECT-COMPUTERセクションの解析
            if division.object_computer:
                issues.extend(self._analyze_object_computer(division.object_computer))

            # SPECIAL-NAMESセクションの解析
            if division.special_names:
                issues.extend(self._analyze_special_names(division.special_names))

            # FILE-CONTROLエントリの解析
            for file_control in division.file_control:
                issues.extend(self._analyze_file_control(file_control))

            # I-O-CONTROLセクションの解析
            if division.io_control:
                issues.extend(self._analyze_io_control(division.io_control))

        except Exception as e:
            issues.append({
                'severity': 'ERROR',
                'type': 'ENVIRONMENT',
                'message': f'Error analyzing ENVIRONMENT DIVISION: {str(e)}',
                'location': None
            })

        return issues

    def _analyze_source_computer(self, source_computer: SourceComputer) -> List[Dict[str, Any]]:
        """SOURCE-COMPUTERセクションの解析"""
        issues = []

        # コンピュータ名の検証
        if not source_computer.name:
            issues.append({
                'severity': 'WARNING',
                'type': 'ENVIRONMENT',
                'message': 'SOURCE-COMPUTER name is not specified',
                'location': None,
                'recommendation': 'Specify a SOURCE-COMPUTER name for better documentation'
            })

        # デバッグモードの検証
        if source_computer.debug_mode:
            issues.append({
                'severity': 'INFO',
                'type': 'ENVIRONMENT',
                'message': 'Program is compiled in debugging mode',
                'location': None,
                'recommendation': 'Ensure debugging mode is intentional for production code'
            })

        return issues

    def _analyze_object_computer(self, object_computer: ObjectComputer) -> List[Dict[str, Any]]:
        """OBJECT-COMPUTERセクションの解析"""
        issues = []

        # コンピュータ名の検証
        if not object_computer.name:
            issues.append({
                'severity': 'WARNING',
                'type': 'ENVIRONMENT',
                'message': 'OBJECT-COMPUTER name is not specified',
                'location': None,
                'recommendation': 'Specify an OBJECT-COMPUTER name for better documentation'
            })

        # メモリサイズの検証
        if object_computer.memory_size is not None:
            if object_computer.memory_size < 0:
                issues.append({
                    'severity': 'ERROR',
                    'type': 'ENVIRONMENT',
                    'message': f'Invalid memory size: {object_computer.memory_size}',
                    'location': None
                })

        # セグメント制限の検証
        if object_computer.segment_limit is not None:
            if not (0 <= object_computer.segment_limit <= 49):
                issues.append({
                    'severity': 'ERROR',
                    'type': 'ENVIRONMENT',
                    'message': f'Invalid segment limit: {object_computer.segment_limit}',
                    'location': None,
                    'recommendation': 'Segment limit must be between 0 and 49'
                })

        return issues

    def _analyze_special_names(self, special_names: SpecialNames) -> List[Dict[str, Any]]:
        """SPECIAL-NAMESセクションの解析"""
        issues = []

        # 通貨記号の検証
        if special_names.currency_sign:
            if not self._is_valid_currency_sign(special_names.currency_sign):
                issues.append({
                    'severity': 'ERROR',
                    'type': 'ENVIRONMENT',
                    'message': f'Invalid currency sign: {special_names.currency_sign}',
                    'location': None,
                    'recommendation': 'Currency sign must be a single valid character'
                })

        # 小数点の検証
        if special_names.decimal_point:
            if special_names.decimal_point not in ['.', ',']:
                issues.append({
                    'severity': 'ERROR',
                    'type': 'ENVIRONMENT',
                    'message': f'Invalid decimal point: {special_names.decimal_point}',
                    'location': None,
                    'recommendation': 'Decimal point must be either . or ,'
                })

        # シンボリック文字の検証
        for char_name, char_value in special_names.symbolic_characters.items():
            if not self._is_valid_symbolic_character(char_value):
                issues.append({
                    'severity': 'ERROR',
                    'type': 'ENVIRONMENT',
                    'message': f'Invalid symbolic character {char_name}: {char_value}',
                    'location': None
                })

        # クラス定義の検証
        for class_name, values in special_names.class_definitions.items():
            if not values:
                issues.append({
                    'severity': 'WARNING',
                    'type': 'ENVIRONMENT',
                    'message': f'Empty class definition: {class_name}',
                    'location': None
                })

        return issues

    def _analyze_file_control(self, file_control: FileControlEntry) -> List[Dict[str, Any]]:
        """FILE-CONTROLエントリの解析"""
        issues = []

        # ファイル名の検証
        if not file_control.file_name:
            issues.append({
                'severity': 'ERROR',
                'type': 'ENVIRONMENT',
                'message': 'File name is required but not specified',
                'location': None
            })

        # 編成の検証
        if file_control.organization not in ['SEQUENTIAL', 'INDEXED', 'RELATIVE']:
            issues.append({
                'severity': 'ERROR',
                'type': 'ENVIRONMENT',
                'message': f'Invalid file organization: {file_control.organization}',
                'location': None,
                'recommendation': 'File organization must be SEQUENTIAL, INDEXED, or RELATIVE'
        })

        # アクセスモードの検証
        valid_access_modes = {
            'SEQUENTIAL': ['SEQUENTIAL'],
            'INDEXED': ['SEQUENTIAL', 'RANDOM', 'DYNAMIC'],
            'RELATIVE': ['SEQUENTIAL', 'RANDOM', 'DYNAMIC']
        }
        if file_control.access_mode not in valid_access_modes[file_control.organization]:
            issues.append({
                'severity': 'ERROR',
                'type': 'ENVIRONMENT',
                'message': f'Invalid access mode {file_control.access_mode} for {file_control.organization} organization',
                'location': None
            })

        return issues

    def _analyze_io_control(self, io_control: IOControlEntry) -> List[Dict[str, Any]]:
        """I-O-CONTROLセクションの解析"""
        issues = []

        # SAME AREA句の検証
        if io_control.same_area:
            for file_list in io_control.same_area:
                if len(file_list) < 2:
                    issues.append({
                        'severity': 'WARNING',
                        'type': 'ENVIRONMENT',
                        'message': 'SAME AREA clause should specify at least two files',
                        'location': None
                    })

        # Multiple File Tape句の検証
        for tape, files in io_control.multiple_file_tapes.items():
            if not files:
                issues.append({
                    'severity': 'WARNING',
                    'type': 'ENVIRONMENT',
                    'message': f'Empty MULTIPLE FILE TAPE clause for {tape}',
                    'location': None
                })

        return issues

    def _is_valid_currency_sign(self, sign: str) -> bool:
        """通貨記号の有効性チェック"""
        return len(sign) == 1 and sign not in ['0', '1', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
                                              'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V',
                                              'W', 'X', 'Y', 'Z', ' ', '+', '-', '*', '/', ',', '.', '(', ')']

    def _is_valid_symbolic_character(self, char: str) -> bool:
        """シンボリック文字の有効性チェック"""
        return len(char) == 1 and ord(char) < 256

    def _analyze_data(self, division: DataDivision) -> List[Dict[str, Any]]:
        """DATA DIVISIONの解析と問題点の検出"""
        issues = []
    
        try:
            # FILE SECTIONの解析
            for file_desc in division.file_section:
                issues.extend(self._analyze_file_description(file_desc))

            # WORKING-STORAGE SECTIONの解析
            if division.working_storage:
                issues.extend(self._analyze_data_items(
                    division.working_storage,
                    "WORKING-STORAGE"
                ))

            # LOCAL-STORAGE SECTIONの解析
            if division.local_storage:
                issues.extend(self._analyze_data_items(
                    division.local_storage,
                    "LOCAL-STORAGE"
                ))

            # LINKAGE SECTIONの解析
            if division.linkage_section:
                issues.extend(self._analyze_data_items(
                    division.linkage_section,
                    "LINKAGE"
                ))

            # データ項目間の相互参照チェック
            issues.extend(self._analyze_data_references(division))

        except Exception as e:
            issues.append({
                'severity': 'ERROR',
                'type': 'DATA',
                'message': f'Error analyzing DATA DIVISION: {str(e)}',
                'location': None
            })

        return issues

    def _analyze_file_description(self, file_desc: FileDescription) -> List[Dict[str, Any]]:
        """ファイル記述の解析"""
        issues = []

        # レコード記述のチェック
        if not file_desc.record_description:
            issues.append({
                'severity': 'ERROR',
                'type': 'DATA',
                'message': f'No record description for file {file_desc.file_name}',
                'location': None
            })

        # ブロックサイズのチェック
        if file_desc.block_contains:
            if file_desc.block_contains <= 0:
                issues.append({
                    'severity': 'ERROR',
                    'type': 'DATA',
                    'message': f'Invalid BLOCK CONTAINS value: {file_desc.block_contains}',
                    'location': None
                })

        # レコードサイズのチェック
        if file_desc.record_contains:
            if file_desc.record_contains <= 0:
                issues.append({
                    'severity': 'ERROR',
                    'type': 'DATA',
                    'message': f'Invalid RECORD CONTAINS value: {file_desc.record_contains}',
                    'location': None
                })

        # LABEL RECORDSのチェック
        if file_desc.label_records:
            if file_desc.label_records not in ['STANDARD', 'OMITTED']:
                issues.append({
                    'severity': 'WARNING',
                    'type': 'DATA',
                    'message': f'Unexpected LABEL RECORDS value: {file_desc.label_records}',
                    'location': None
                })

        # VALUE OFのチェック
        for name, value in file_desc.value_of.items():
            if not self._is_valid_value_of(name, value):
                issues.append({
                    'severity': 'WARNING',
                    'type': 'DATA',
                    'message': f'Invalid VALUE OF {name}: {value}',
                    'location': None
                })

        # レコード記述の解析
        issues.extend(self._analyze_data_items(file_desc.record_description, "FILE"))

        return issues

    def _analyze_data_items(self, items: List[DataItem], section_type: str) -> List[Dict[str, Any]]:
        """データ項目の解析"""
        issues = []
        level_stack = []

        for item in items:
            # レベル番号のチェック
            if not self._is_valid_level_number(item.level):
                issues.append({
                    'severity': 'ERROR',
                    'type': 'DATA',
                    'message': f'Invalid level number: {item.level}',
                    'location': None,
                    'recommendation': 'Level numbers must be 1-49, 66, 77, or 88'
                })

            # 項目名のチェック
            if item.name and not self._is_valid_data_name(item.name):
                issues.append({
                    'severity': 'WARNING',
                    'type': 'DATA',
                    'message': f'Invalid data name format: {item.name}',
                    'location': None,
                    'recommendation': 'Follow COBOL naming conventions'
                })

            # PICTURE句のチェック
            if item.picture:
                pic_issues = self._analyze_picture_clause(item.picture)
                issues.extend(pic_issues)

            # OCCURS句のチェック
            if item.occurs:
                if item.level == 1 or item.level == 77:
                    issues.append({
                        'severity': 'ERROR',
                        'type': 'DATA',
                        'message': f'OCCURS clause not allowed at level {item.level}',
                        'location': None
                    })

            # REDEFINES句のチェック
            if item.redefines:
                redef_issues = self._analyze_redefines(item)
                issues.extend(redef_issues)

            # 値の割り当てのチェック
            if item.value is not None:
                if not self._is_valid_value_for_type(item.value, item.picture):
                    issues.append({
                        'severity': 'ERROR',
                        'type': 'DATA',
                        'message': f'Invalid value for picture: {item.value}',
                        'location': None
                    })

            # レベル階層のチェック
            level_stack = self._update_level_stack(level_stack, item.level)
            if not level_stack:
                issues.append({
                    'severity': 'ERROR',
                    'type': 'DATA',
                    'message': 'Invalid level hierarchy',
                    'location': None
                })

            # セクション固有のチェック
            if section_type == "WORKING-STORAGE":
                if item.level == 1 and not item.external and not item.global_item:
                    issues.append({
                        'severity': 'INFO',
                        'type': 'DATA',
                        'message': f'Consider making item {item.name} EXTERNAL or GLOBAL',
                        'location': None
                    })

        return issues

    def _analyze_data_references(self, division: DataDivision) -> List[Dict[str, Any]]:
        """データ参照の整合性チェック"""
        issues = []
        all_items = {}
        redefines_map = {}

        # 全データ項目の収集
        self._collect_all_data_items(division, all_items)

        # REDEFINES参照のチェック
        for name, item in all_items.items():
            if item.redefines:
                if item.redefines not in all_items:
                    issues.append({
                        'severity': 'ERROR',
                        'type': 'DATA',
                        'message': f'REDEFINES target not found: {item.redefines}',
                        'location': None
                    })
                else:
                    redefines_map[item.name] = item.redefines

        # 循環参照のチェック
        for name in redefines_map:
            if self._has_circular_redefines(name, redefines_map, set()):
                issues.append({
                    'severity': 'ERROR',
                    'type': 'DATA',
                    'message': f'Circular REDEFINES detected starting from {name}',
                    'location': None
                })

        return issues

    def _is_valid_level_number(self, level: int) -> bool:
        """レベル番号の有効性チェック"""
        return (1 <= level <= 49) or level in [66, 77, 88]

    def _is_valid_data_name(self, name: str) -> bool:
        """データ名の有効性チェック"""
        if not name:
            return False
        if len(name) > 30:
            return False
        if not name[0].isalpha():
            return False
        return all(c.isalnum() or c == '-' for c in name)

    def _is_valid_value_for_type(self, value: Any, picture: PictureClause) -> bool:
        """値の型整合性チェック"""
        if not picture:
            return True
    
        try:
            if picture.character_type == 'numeric':
                float(str(value))
                return True
            elif picture.character_type == 'alphanumeric':
                return isinstance(value, str)
            return True
        except ValueError:
            return False

    def _has_circular_redefines(self, item: str, redefines_map: Dict[str, str], visited: Set[str]) -> bool:
        """循環参照のチェック"""
        if item in visited:
            return True
        if item not in redefines_map:
            return False
    
        visited.add(item)
        result = self._has_circular_redefines(redefines_map[item], redefines_map, visited)
        visited.remove(item)
    
        return result

    def _analyze_procedure(self, division: ProcedureDivision) -> List[Dict[str, Any]]:
        """PROCEDURE DIVISIONの解析と問題点の検出"""
        issues = []
    
        try:
            # USING/GIVING パラメータの解析
            issues.extend(self._analyze_parameters(division))
        
            # DECLARATIVESセクションの解析
            if division.declaratives:
                issues.extend(self._analyze_declaratives(division.declaratives))
        
            # セクションとパラグラフの解析
            issues.extend(self._analyze_sections(division.sections))
        
            # 制御フローの解析
            issues.extend(self._analyze_control_flow(division))
        
            # 参照整合性の解析
            issues.extend(self._analyze_references(division))

        except Exception as e:
            issues.append({
                'severity': 'ERROR',
                'type': 'PROCEDURE',
                'message': f'Error analyzing PROCEDURE DIVISION: {str(e)}',
                'location': None
            })

        return issues

    def _analyze_parameters(self, division: ProcedureDivision) -> List[Dict[str, Any]]:
        """パラメータの解析"""
        issues = []
    
        # USINGパラメータの検証
        seen_params = set()
        for param in division.using_parameters:
            if param in seen_params:
                issues.append({
                    'severity': 'ERROR',
                    'type': 'PROCEDURE',
                    'message': f'Duplicate USING parameter: {param}',
                    'location': None
                })
            seen_params.add(param)
        
            if not self._is_valid_data_reference(param):
                issues.append({
                    'severity': 'ERROR',
                    'type': 'PROCEDURE',
                    'message': f'Invalid USING parameter reference: {param}',
                    'location': None
                })
    
        # GIVINGパラメータの検証
        for param in division.giving_parameters:
            if not self._is_valid_data_reference(param):
                issues.append({
                    'severity': 'ERROR',
                    'type': 'PROCEDURE',
                    'message': f'Invalid GIVING parameter reference: {param}',
                    'location': None
                })

        return issues

    def _analyze_declaratives(self, declaratives: List[Section]) -> List[Dict[str, Any]]:
        """DECLARATIVESの解析"""
        issues = []
    
        for section in declaratives:
            # セクション名のフォーマット検証
            if not self._is_valid_section_name(section.name):
                issues.append({
                    'severity': 'ERROR',
                    'type': 'PROCEDURE',
                    'message': f'Invalid DECLARATIVES section name: {section.name}',
                    'location': None
                })
            
            # セクション内のパラグラフ検証
            issues.extend(self._analyze_paragraphs(section.paragraphs, True))

        return issues

    def _analyze_sections(self, sections: List[Section]) -> List[Dict[str, Any]]:
        """セクションの解析"""
        issues = []
        seen_sections = set()
    
        for section in sections:
            # セクション名の重複チェック
            if section.name in seen_sections:
                issues.append({
                    'severity': 'ERROR',
                    'type': 'PROCEDURE',
                    'message': f'Duplicate section name: {section.name}',
                    'location': None
                })
            seen_sections.add(section.name)
        
            # セクション名のフォーマット検証
            if not self._is_valid_section_name(section.name):
                issues.append({
                    'severity': 'WARNING',
                    'type': 'PROCEDURE',
                    'message': f'Invalid section name format: {section.name}',
                    'location': None,
                    'recommendation': 'Follow COBOL naming conventions for sections'
                })
            
            # パラグラフの解析
            issues.extend(self._analyze_paragraphs(section.paragraphs, False))

        return issues

    def _analyze_paragraphs(self, paragraphs: List[Paragraph], is_declarative: bool) -> List[Dict[str, Any]]:
        """パラグラフの解析"""
        issues = []
        seen_paragraphs = set()
    
        for paragraph in paragraphs:
            # パラグラフ名の重複チェック
            if paragraph.name in seen_paragraphs:
                issues.append({
                    'severity': 'ERROR',
                    'type': 'PROCEDURE',
                    'message': f'Duplicate paragraph name: {paragraph.name}',
                    'location': None
                })
            seen_paragraphs.add(paragraph.name)
        
            # 文の解析
            issues.extend(self._analyze_statements(paragraph.statements, is_declarative))
        
            # 複雑度の分析
            complexity = self._calculate_paragraph_complexity(paragraph)
            if complexity > 20:  # 閾値は調整可能
                issues.append({
                    'severity': 'WARNING',
                    'type': 'PROCEDURE',
                    'message': f'High complexity in paragraph {paragraph.name}: {complexity}',
                    'location': None,
                    'recommendation': 'Consider breaking down complex paragraphs'
                })

        return issues

    def _analyze_control_flow(self, division: ProcedureDivision) -> List[Dict[str, Any]]:
        """制御フローの解析"""
        issues = []
        flow_graph = self._build_control_flow_graph(division)
    
        # 到達不能コードの検出
        unreachable = self._find_unreachable_code(flow_graph)
        for code in unreachable:
            issues.append({
                'severity': 'WARNING',
                'type': 'PROCEDURE',
                'message': f'Unreachable code detected: {code}',
                'location': None
            })
    
        # 無限ループの検出
        infinite_loops = self._detect_infinite_loops(flow_graph)
        for loop in infinite_loops:
            issues.append({
                'severity': 'WARNING',
                'type': 'PROCEDURE',
                'message': f'Potential infinite loop detected: {loop}',
                'location': None
            })
        
        return issues

    def _analyze_references(self, division: ProcedureDivision) -> List[Dict[str, Any]]:
        """参照整合性の解析"""
        issues = []
        references = self._collect_all_references(division)
    
        # 未定義の参照チェック
        for ref in references:
            if not self._is_reference_defined(ref):
                issues.append({
                    'severity': 'ERROR',
                    'type': 'PROCEDURE',
                    'message': f'Undefined reference: {ref}',
                    'location': None
                })
    
        # 未使用のセクション/パラグラフの検出
        unused = self._find_unused_sections_and_paragraphs(division, references)
        for item in unused:
            issues.append({
                'severity': 'INFO',
                'type': 'PROCEDURE',
                'message': f'Unused section/paragraph: {item}',
                'location': None
            })
            
        return issues

    def _calculate_paragraph_complexity(self, paragraph: Paragraph) -> int:
        """パラグラフの複雑度計算"""
        complexity = 1  # 基本複雑度
    
        for statement in paragraph.statements:
            if statement.statement_type in [
                StatementType.IF,
                StatementType.EVALUATE,
                StatementType.PERFORM,
                StatementType.SEARCH
            ]:
                complexity += 1
            
            # ネストされた条件のチェック
            if statement.condition:
                complexity += self._count_nested_conditions(statement.condition)
            
        return complexity

    def _count_nested_conditions(self, condition: Condition) -> int:
        """ネストされた条件の数をカウント"""
        count = 1
        count += len(condition.and_conditions)
        count += len(condition.or_conditions)
    
        for subcond in condition.and_conditions + condition.or_conditions:
            count += self._count_nested_conditions(subcond)
        
        return count

# ASTジェネレーター
class COBOLASTGenerator:
    def generate_ast(self, program: COBOLProgram) -> Dict[str, Any]:
        """プログラム構造からASTを生成"""
        return {
            "type": "program",
            "identification": self._generate_identification_ast(program.identification),
            "environment": self._generate_environment_ast(program.environment) if program.environment else None,
            "data": self._generate_data_ast(program.data) if program.data else None,
            "procedure": self._generate_procedure_ast(program.procedure)
        }

    def _generate_identification_ast(self, division: IdentificationDivision) -> Dict[str, Any]:
        """IDENTIFICATION DIVISIONのAST生成"""
        try:
            identification_ast = {
                "type": "identification_division",
                "location": {
                    "start_line": 0,  # 実際の位置情報は解析時に設定
                    "start_column": 0
                },
                "program_id": {
                    "type": "program_id",
                    "name": division.program_id,
                    "location": {
                        "start_line": 0,
                        "start_column": 0
                    }
                },
                "clauses": []
            }

            # AUTHOR句のAST生成
            if division.author:
                identification_ast["clauses"].append({
                    "type": "author",
                    "value": division.author,
                    "location": {
                        "start_line": 0,
                        "start_column": 0
                    }
                })

            # INSTALLATION句のAST生成
            if division.installation:
                identification_ast["clauses"].append({
                    "type": "installation",
                    "value": division.installation,
                    "location": {
                        "start_line": 0,
                        "start_column": 0
                    }
                })

            # DATE-WRITTEN句のAST生成
            if division.date_written:
                identification_ast["clauses"].append({
                    "type": "date_written",
                    "value": division.date_written.strftime("%Y-%m-%d"),
                    "location": {
                        "start_line": 0,
                        "start_column": 0
                    }
                })

            # DATE-COMPILED句のAST生成
            if division.date_compiled:
                identification_ast["clauses"].append({
                    "type": "date_compiled",
                    "value": division.date_compiled.strftime("%Y-%m-%d"),
                    "location": {
                        "start_line": 0,
                        "start_column": 0
                    }
                })

            # SECURITY句のAST生成
            if division.security:
                identification_ast["clauses"].append({
                    "type": "security",
                    "value": division.security,
                    "location": {
                        "start_line": 0,
                        "start_column": 0
                    }
                })

            # REMARKS句のAST生成
            for remark in division.remarks:
                identification_ast["clauses"].append({
                    "type": "remarks",
                    "value": remark,
                    "location": {
                        "start_line": 0,
                        "start_column": 0
                    }
                })

            return identification_ast

        except Exception as e:
            self.logger.error(f"Error generating identification AST: {str(e)}")
            raise

    def _generate_environment_ast(self, division: EnvironmentDivision) -> Dict[str, Any]:
        """ENVIRONMENT DIVISIONのAST生成"""
        try:
            environment_ast = {
                "type": "environment_division",
                "location": {
                    "start_line": 0,  # 実際の位置情報は解析時に設定
                    "start_column": 0
                },
                "sections": []
            }

            # CONFIGURATION SECTIONのAST生成
            configuration_section = {
                "type": "configuration_section",
                "clauses": []
            }

            # SOURCE-COMPUTER句のAST生成
            if division.source_computer:
                configuration_section["clauses"].append({
                    "type": "source_computer",
                    "name": division.source_computer.name,
                    "debugging_mode": division.source_computer.debug_mode,
                    "location": {
                        "start_line": 0,
                        "start_column": 0
                    }
                })

            # OBJECT-COMPUTER句のAST生成
            if division.object_computer:
                object_computer = {
                    "type": "object_computer",
                    "name": division.object_computer.name,
                    "location": {
                        "start_line": 0,
                        "start_column": 0
                    },
                    "attributes": {}
                }
            
                if division.object_computer.memory_size:
                    object_computer["attributes"]["memory_size"] = division.object_computer.memory_size
                if division.object_computer.sequence:
                    object_computer["attributes"]["sequence"] = division.object_computer.sequence
                if division.object_computer.segment_limit:
                    object_computer["attributes"]["segment_limit"] = division.object_computer.segment_limit

                configuration_section["clauses"].append(object_computer)

            # SPECIAL-NAMES句のAST生成
            if division.special_names:
                special_names = {
                    "type": "special_names",
                    "location": {
                        "start_line": 0,
                        "start_column": 0
                    },
                    "clauses": []
                }

                if division.special_names.currency_sign:
                    special_names["clauses"].append({
                        "type": "currency_sign",
                        "value": division.special_names.currency_sign
                    })

                if division.special_names.decimal_point:
                    special_names["clauses"].append({
                        "type": "decimal_point",
                        "value": division.special_names.decimal_point
                    })

                for char_name, char_value in division.special_names.symbolic_characters.items():
                    special_names["clauses"].append({
                        "type": "symbolic_character",
                        "name": char_name,
                        "value": char_value
                    })

                for class_name, values in division.special_names.class_definitions.items():
                    special_names["clauses"].append({
                        "type": "class",
                        "name": class_name,
                        "values": values
                    })

                configuration_section["clauses"].append(special_names)

            environment_ast["sections"].append(configuration_section)

            # INPUT-OUTPUT SECTIONのAST生成
            io_section = {
                "type": "input_output_section",
                "file_control": [],
                "io_control": None
            }

            # FILE-CONTROL句のAST生成
            for file_control in division.file_control:
                fc_entry = {
                    "type": "file_control_entry",
                    "file_name": file_control.file_name,
                    "assign_to": file_control.assign_to,
                    "organization": file_control.organization,
                    "access_mode": file_control.access_mode,
                    "location": {
                        "start_line": 0,
                        "start_column": 0
                    }
                }

                if file_control.record_key:
                    fc_entry["record_key"] = file_control.record_key
                
                if file_control.alternate_keys:
                    fc_entry["alternate_keys"] = file_control.alternate_keys
                
                if file_control.file_status:
                    fc_entry["file_status"] = file_control.file_status

                io_section["file_control"].append(fc_entry)

            # I-O-CONTROL句のAST生成
            if division.io_control:
                io_control = {
                    "type": "io_control",
                    "same_area": division.io_control.same_area,
                    "multiple_file_tapes": division.io_control.multiple_file_tapes,
                    "apply_write_only": division.io_control.apply_write_only,
                    "location": {
                        "start_line": 0,
                        "start_column": 0
                    }
                }
                io_section["io_control"] = io_control

            environment_ast["sections"].append(io_section)

            return environment_ast

        except Exception as e:
            self.logger.error(f"Error generating environment AST: {str(e)}")
            raise

    def _generate_data_ast(self, division: DataDivision) -> Dict[str, Any]:
        """DATA DIVISIONのAST生成"""
        try:
            data_ast = {
                "type": "data_division",
                "location": {
                    "start_line": 0,  # 実際の位置情報は解析時に設定
                    "start_column": 0
                },
                "sections": []
            }

            # FILE SECTIONのAST生成
            if division.file_section:
                file_section = {
                    "type": "file_section",
                    "location": {"start_line": 0, "start_column": 0},
                    "file_descriptions": []
                }

                for file_desc in division.file_section:
                    fd_ast = {
                        "type": "file_description",
                        "file_name": file_desc.file_name,
                        "location": {"start_line": 0, "start_column": 0},
                        "attributes": {
                            "block_contains": file_desc.block_contains,
                            "record_contains": file_desc.record_contains,
                            "label_records": file_desc.label_records,
                            "value_of": file_desc.value_of,
                            "data_records": file_desc.data_records,
                            "linage": file_desc.linage
                        },
                        "record_description": self._generate_data_item_ast(file_desc.record_description)
                    }
                    file_section["file_descriptions"].append(fd_ast)

                data_ast["sections"].append(file_section)

            # WORKING-STORAGE SECTIONのAST生成
            if division.working_storage:
                working_storage = {
                    "type": "working_storage_section",
                    "location": {"start_line": 0, "start_column": 0},
                    "data_items": self._generate_data_item_ast(division.working_storage)
                }
                data_ast["sections"].append(working_storage)

            # LOCAL-STORAGE SECTIONのAST生成
            if division.local_storage:
                local_storage = {
                    "type": "local_storage_section",
                    "location": {"start_line": 0, "start_column": 0},
                    "data_items": self._generate_data_item_ast(division.local_storage)
                }
                data_ast["sections"].append(local_storage)

            # LINKAGE SECTIONのAST生成
            if division.linkage_section:
                linkage = {
                    "type": "linkage_section",
                    "location": {"start_line": 0, "start_column": 0},
                    "data_items": self._generate_data_item_ast(division.linkage_section)
                }
                data_ast["sections"].append(linkage)

            # SCREEN SECTIONのAST生成
            if division.screen_section:
                screen = {
                    "type": "screen_section",
                    "location": {"start_line": 0, "start_column": 0},
                    "data_items": self._generate_data_item_ast(division.screen_section)
                }
                data_ast["sections"].append(screen)

            return data_ast

        except Exception as e:
            self.logger.error(f"Error generating data AST: {str(e)}")
            raise

    def _generate_data_item_ast(self, data_items: List[DataItem]) -> List[Dict[str, Any]]:
        """データ項目のAST生成"""
        ast_items = []
    
        for item in data_items:
            ast_item = {
                "type": "data_item",
                "level": item.level,
                "name": item.name,
                "location": {"start_line": 0, "start_column": 0},
                "attributes": {}
            }

            # PICTURE句のAST生成
            if item.picture:
                ast_item["attributes"]["picture"] = {
                    "type": "picture_clause",
                    "picture_string": item.picture.picture_string,
                    "character_type": item.picture.character_type,
                    "length": item.picture.length,
                    "decimals": item.picture.decimals,
                    "usage": item.picture.usage.value if item.picture.usage else None,
                    "sign_position": item.picture.sign_position,
                    "synchronized": item.picture.synchronized.value if item.picture.synchronized else None,
                    "justified": item.picture.justified,
                    "blank_when_zero": item.picture.blank_when_zero
                }

            # その他の属性のAST生成
            if item.usage:
                ast_item["attributes"]["usage"] = item.usage.value

            if item.value is not None:
                ast_item["attributes"]["value"] = {
                    "type": "value_clause",
                    "value": item.value
                }

            if item.occurs:
                ast_item["attributes"]["occurs"] = {
                    "type": "occurs_clause",
                    "times": item.occurs,
                    "depending_on": item.occurs_depending_on,
                    "indexed_by": item.indexed_by
                }

            if item.redefines:
                ast_item["attributes"]["redefines"] = {
                    "type": "redefines_clause",
                    "target": item.redefines
                }

            if item.synchronized:
                ast_item["attributes"]["synchronized"] = item.synchronized.value

            if item.justified:
                ast_item["attributes"]["justified"] = True

            if item.blank_when_zero:
                ast_item["attributes"]["blank_when_zero"] = True

            if item.external:
                ast_item["attributes"]["external"] = True

            if item.global_item:
                ast_item["attributes"]["global"] = True

            # 子項目の再帰的な処理
            if item.children:
                ast_item["children"] = self._generate_data_item_ast(item.children)
            else:
                ast_item["children"] = []

            ast_items.append(ast_item)

        return ast_items

    def _generate_procedure_ast(self, division: ProcedureDivision) -> Dict[str, Any]:
        """PROCEDURE DIVISIONのAST生成"""
        try:
            procedure_ast = {
                "type": "procedure_division",
                "location": {
                    "start_line": 0,  # 実際の位置情報は解析時に設定
                    "start_column": 0
                },
                "header": {
                    "using_parameters": division.using_parameters,
                    "giving_parameters": division.giving_parameters
                },
                "declaratives": [],
                "sections": []
            }

            # DECLARATIVESのAST生成
            if division.declaratives:
                for section in division.declaratives:
                    declarative = self._generate_section_ast(section, True)
                    procedure_ast["declaratives"].append(declarative)

            # セクションのAST生成
            for section in division.sections:
                section_ast = self._generate_section_ast(section, False)
                procedure_ast["sections"].append(section_ast)

            return procedure_ast

        except Exception as e:
            self.logger.error(f"Error generating procedure AST: {str(e)}")
            raise

    def _generate_section_ast(self, section: Section, is_declarative: bool) -> Dict[str, Any]:
        """セクションのAST生成"""
        section_ast = {
            "type": "section",
            "name": section.name,
            "is_declarative": is_declarative,
            "location": {
                "start_line": 0,
                "start_column": 0
            },
            "paragraphs": []
        }

        # パラグラフのAST生成
        for paragraph in section.paragraphs:
            paragraph_ast = {
                "type": "paragraph",
                "name": paragraph.name,
                "location": {
                    "start_line": 0,
                    "start_column": 0
                },
                "statements": self._generate_statement_ast(paragraph.statements)
            }
            section_ast["paragraphs"].append(paragraph_ast)

        return section_ast

    def _generate_statement_ast(self, statements: List[Statement]) -> List[Dict[str, Any]]:
        """文のAST生成"""
        statement_asts = []

        for statement in statements:
            stmt_ast = {
                "type": "statement",
                "statement_type": statement.statement_type.value,
                "location": {
                    "start_line": statement.line_number,
                    "start_column": 0
                },
                "operands": statement.operands
            }

            # 条件付き文の処理
            if statement.condition:
                stmt_ast["condition"] = self._generate_condition_ast(statement.condition)

            # ネストされた文の処理
            if statement.nested_statements:
                stmt_ast["nested_statements"] = self._generate_statement_ast(statement.nested_statements)

            # 文タイプ固有の属性の処理
            stmt_ast.update(self._generate_statement_specific_ast(statement))

            statement_asts.append(stmt_ast)

        return statement_asts

    def _generate_condition_ast(self, condition: Condition) -> Dict[str, Any]:
        """条件式のAST生成"""
        condition_ast = {
            "type": "condition",
            "left_operand": condition.left_operand,
            "operator": condition.operator,
            "right_operand": condition.right_operand,
            "and_conditions": [],
            "or_conditions": []
        }

        # AND条件の処理
        for and_condition in condition.and_conditions:
            condition_ast["and_conditions"].append(
                self._generate_condition_ast(and_condition)
            )

        # OR条件の処理
        for or_condition in condition.or_conditions:
            condition_ast["or_conditions"].append(
                self._generate_condition_ast(or_condition)
            )

        return condition_ast

    def _generate_statement_specific_ast(self, statement: Statement) -> Dict[str, Any]:
        """文タイプ固有の属性のAST生成"""
        specific_ast = {}

        if statement.statement_type == StatementType.PERFORM:
            specific_ast.update(self._generate_perform_ast(statement))
        elif statement.statement_type == StatementType.IF:
            specific_ast.update(self._generate_if_ast(statement))
        elif statement.statement_type == StatementType.EVALUATE:
            specific_ast.update(self._generate_evaluate_ast(statement))
        elif statement.statement_type == StatementType.CALL:
            specific_ast.update(self._generate_call_ast(statement))

        return specific_ast

    def _generate_perform_ast(self, statement: Statement) -> Dict[str, Any]:
        """PERFORM文のAST生成"""
        return {
            "perform_type": self._determine_perform_type(statement),
            "target": statement.operands[0] if statement.operands else None,
            "times": self._extract_perform_times(statement),
            "until_condition": self._extract_perform_until(statement)
        }

    def _generate_if_ast(self, statement: Statement) -> Dict[str, Any]:
        """IF文のAST生成"""
        return {
            "then_statements": self._generate_statement_ast(statement.nested_statements),
            "else_statements": self._extract_else_statements(statement)
        }

    def _generate_evaluate_ast(self, statement: Statement) -> Dict[str, Any]:
        """EVALUATE文のAST生成"""
        return {
            "subject": statement.operands[0] if statement.operands else None,
            "when_clauses": self._extract_evaluate_when_clauses(statement)
        }

    def _generate_call_ast(self, statement: Statement) -> Dict[str, Any]:
        """CALL文のAST生成"""
        return {
            "program_name": statement.operands[0] if statement.operands else None,
            "using_parameters": self._extract_call_parameters(statement)
        }
