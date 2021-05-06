from datetime import datetime
from typing import List

import xlrd
from xlrd.sheet import Cell

from model.common_model import FieldCheckType, TableType, NodeIndex
from model.orm.detecte_evaluate import *
from model.orm.model_orm import *
from model.orm.shared import *
from utils.excel_helper import ExcelHelper
from utils.snowflake import IdGenerator, globalIdGenerator


class FieldObj:
    """每个单元格(字段)对应的对象"""
    index_in_table = 0
    orm_attr_name = ''
    check_type = FieldCheckType.NO_CHECK_TYPE  # 默认检查类型是 "无"

    def __init__(self, field_param_dict):  # 先设置field, 再设置table_obj
        for key in field_param_dict:
            setattr(self, key, field_param_dict[key])
            pass
        pass

    pass


class TableObj:
    def __init__(self, table_obj_dict: dict):
        self.type = ''  # 表类型
        self.name = ''  # 表名称
        self.sheet_name = ''  # 所在sheet的名称
        self.end_flag = ''  # 结束标识
        self.useless_rows = []  # 记录无用的行的标记
        # excel_date_rows = []  # 需要额外处理的excel_date格式的日期
        self.value_list = []  # 记录将要存入数据库的值
        self.attrToSet_list = []  # 记录 要存入数据库的字段名
        self.field_checktype_list = []  # 记录 各个单元格的检查属性
        self.orm_class = None  # ORM 类
        self.node_index = None  # 如果有, 记录当前表 所在的节点的编号,
        self.field_obj_list = []  # 记录 单元格对象
        self.is_header_name_useless = True  # 有些表没有单独的表名, 是拿第一行的表内容来做的...
        self.constant_attr = {}  # 有些表有固定的ORM_attr
        self.wrongType_cell_index = []  # 记录格式错误的单元格
        self.cell_list = []  # excel 中对应的单元格的名字, 不用都写, 只有在需要错误检查的表中再填

        for key in table_obj_dict:
            if not isinstance(table_obj_dict[key], list):
                setattr(self, key, table_obj_dict[key])
            elif isinstance(table_obj_dict[key], list):
                the_value = table_obj_dict[key]
                assert isinstance(the_value, list)
                the_value_copy = the_value.copy()
                setattr(self, key, the_value_copy)

            pass
        if self.is_header_name_useless is True:
            self.useless_rows.append(self.name)  # 自动将标题添加到 useless_rows中
        pass

    def set_field_obj_list(self, field_obj_list: list):
        """设置自身的field_obj_list"""
        self.field_obj_list = field_obj_list
        pass

    pass


class NodeInfo:
    """接入节点(广义)的类, 包含node_id和其下属的phy_id"""
    def __init__(self, node_id=0, node_name='', phy_id_list=None):
        self.node_id = node_id
        self.node_name = node_name
        self.phy_id_list = phy_id_list
        pass
    pass


class AllLevelIdInfo:
    """包含个层级节点(report_id, node_id. 不包括physical_node_id) """
    def __init__(self, report_id=0, node_obj_list: List[NodeInfo] = None):
        self.report_id = report_id
        self.node_obj_list = node_obj_list  # list其中另有NodeObj的对象
        pass

    pass

class AllLvInfoGenerator:
    """负责生成各个节点的基础信息, 用于给ExcelInfo的all_level_info赋值 """
    def __init__(self, excel_name):
        self.excel_helper = ExcelHelper(file_name=excel_name)
        self.all_level_info = AllLevelIdInfo()
        self.node_info_list = []  # NodeInfo obj as element
        pass

    def get_all_level_info(self):
        """得到allLevelInfo 的对象"""
        node_info_list = self.__get_node_obj_list()
        report_id = globalIdGenerator.getNextId()
        return AllLevelIdInfo(report_id=report_id, node_obj_list=node_info_list)
        pass

    def __get_node_obj_list(self):
        """从自身的excel文件中解析出node_obj_list
        :returns: list of node_info """
        xls_helper = self.excel_helper
        all_sheets = xls_helper.getAllSheets()
        NODE_FLAGS = ['中心节点', '接入节点']  # 包含这两个flag其中之一, 则新增一个node_info
        node_info_obj_list = []
        for each_sheet_name in all_sheets:
            for each_flag in NODE_FLAGS:
                if each_flag in each_sheet_name:
                    # todo 在这里建node_info obj
                    sheet_index = all_sheets.index(each_sheet_name)
                    node_info_obj = self.__generate_node_info(sheet_index)
                    node_info_obj_list.append(node_info_obj)
                    break
                pass  # end inner for
            pass  # end outer for
        return node_info_obj_list
        pass

    def __generate_node_info(self, sheet_index):
        """根据sheet_index, 创建一个带有phy_id的node_info
        :returns: NodeInfo obj"""
        xls_helper = self.excel_helper
        xls_helper.set_sheet_by_index(sheet_index)
        node_id = globalIdGenerator.getNextId()
        node_name = xls_helper.getAllSheets()[sheet_index]
        node_info_obj = NodeInfo(node_id=node_id, node_name=node_name)
        # set the phy_id_list in node_info_obj
        self.__set_phyIdList_in_nodeObj(node_info_obj)
        return node_info_obj
        pass

    def __set_phyIdList_in_nodeObj(self, node_info_obj: NodeInfo):
        """为node_info_obj设定它的 phy_node_id list

        :returns: None"""
        PHY_NODE_FLAG = '物理环境表'  # 查看flag是否 in cell_value, 以此来计数phy_node的个数`1
        sheet_name = node_info_obj.node_name  # 节点的名字, 也就是excel sheet的名字
        self.excel_helper.set_sheet_by_name(sheet_name)
        first_column_contents = self.excel_helper.readOneColumn(0)
        phy_id_list = []  # 存储physical_node_id的list
        for cell in first_column_contents:
            assert isinstance(cell, Cell)
            if PHY_NODE_FLAG in str(cell.value):
                phy_id = globalIdGenerator.getNextId()
                phy_id_list.append(phy_id)
                pass
            pass  # end for
        node_info_obj.phy_id_list = phy_id_list  # 直接赋值
        pass
    pass


class ExcelInfo:
    """记录excel的各种信息, 包括各项字典等"""
    EXCEL_NAME = ''
    CURRENT_SHEET_INDEX = -1  # 当前的sheet_index
    END_SYMBOL = '{{结束}}'  # sheet结束标志
    current_row_cursor = 0  # 记录现在进行到当前sheet的哪一行

    excel_helper = None

    # 包含各种节点的对象: NodeInfo

    # 设定NodeId
    node_num = 1  # 现在只有1个
    node_id_list = []
    all_level_id = AllLevelIdInfo()

    # 各个sheetName的dictionary
    # SHEET_NAME_DICT = {
    #     'quest_info': '测评任务信息',
    #     'part_1': '第一部分 系统概述',
    #     'central_node': '中心节点',
    #     'node_1': '接入节点1',
    #     'node_n': '接入节点N',
    #     'part_2': '第二部分 系统检测',
    #     'part_3': '第三部分 专家评估',
    #     'part_4': '第四部分 测评结论',
    #     'appendix': '附件',
    # }

    # =================================================================================================================
    # =========================================================================
    # start of sheet and table dict
    # start 测评任务信息中的表
    # 封面 表的字典
    table_front_cover = {
        'type': TableType.TWO_COLUMN,
        'name': '封面',
        'end_flag': '',
        'useless_rows': [],  # 记录无用的行的标记
        'value_list': [],
        'attrToSet_list': ['ReportNumber', None, None, None, 'ReportDate'],
        'field_checktype_list': [
            FieldCheckType.NO_CHECK_TYPE,
            FieldCheckType.NO_CHECK_TYPE,
            FieldCheckType.NO_CHECK_TYPE,
            FieldCheckType.NO_CHECK_TYPE,
            FieldCheckType.DATE_TYPE,
        ],
        'orm_class': DeReport,
        'field_obj_list': [],  # 存入field_obj_list对象
        'cell_list': [
            '报告编号',
            '涉密系统名称',
            '建设使用单位',
            '测评机构',
            '日期',
        ],  # excel 中对应的单元格的名字, 不用都写, 只有在需要错误检查的表中再填

    }

    # 报告签批页 表的字典
    table_sign_off = {
        'type': TableType.SIGN_OFF,
        'name': '报告签批页',
        'end_flag': END_SYMBOL,
        'useless_rows': ['报告签批页'],
        'value_list': [],
        'attrToSet_list': [],  # 复合表, 不单独存入
        'orm_class': None,  # 复合表, 不单独存入
    }

    # 报告签批页被分割的主体表
    table_sign_off_outer = {
        'type': TableType.TWO_COLUMN,
        'name': '报告签批页',
        'end_flag': END_SYMBOL,
        'useless_rows': ['报告签批页'],
        'value_list': [],
        'attrToSet_list': [
            'SysName',
            'UseUnit',
            'DeResult',
            'TechnicalScore',
            'ManageScore',
            'ReviewResult',
            'ReviewDate',
            'ExamineResult',
            'ExamineDate',
            'ApprovedResult',
            'ApprovedDate',
        ],
        'field_checktype_list': [
            FieldCheckType.NO_CHECK_TYPE,  # 'SysName',
            FieldCheckType.NO_CHECK_TYPE,  # 'UseUnit',
            FieldCheckType.NO_CHECK_TYPE,  # 'DeResult',
            FieldCheckType.SCORE_TYPE,  # 'TechnicalScore',
            FieldCheckType.SCORE_TYPE,  # 'ManageScore',
            FieldCheckType.NO_CHECK_TYPE,  # 'ReviewResult',
            FieldCheckType.DATE_TYPE,  # 'ReviewDate',
            FieldCheckType.NO_CHECK_TYPE,  # 'ExamineResult',
            FieldCheckType.DATE_TYPE,  # 'ExamineDate',
            FieldCheckType.NO_CHECK_TYPE,  # 'ApprovedResult',
            FieldCheckType.DATE_TYPE,  # 'ApprovedDate',
        ],
        'field_obj_list': [],  # 存入field_obj_list对象
        'orm_class': DeReportSignOff,
        'wrongType_cell_index': [],  # 记录格式错误的单元格
        'cell_list': [
            '系统名称',
            '建设使用单位',
            '测评结论',
            '技术得分',
            '管理得分',
            '校审',
            '校审日期',
            '审核',
            '审核日期',
            '批准',
            '批准日期',
        ]  # excel 中对应的单元格的名字, 不用都写, 只有在需要错误检查的表中再填'
    }

    # 报告签批页 表的内部表---测评机构及检测人员
    table_sign_off_inner_ins_psn = {
        'type': TableType.MULTI_COLUMN,
        'name': '测评机构\n及检测人员',  # 内部表名字..
        'end_flag': END_SYMBOL,
        'useless_rows': ['测评机构\n及检测人员', '姓  名'],
        'value_list': [],
        'attrToSet_list': ['PersonName', 'Certificate'],
        'orm_class': DeReportInstitutionPerson,
    }

    # 测评机构及委托方信息 表的字典, 是一张特殊表...
    # 看时间而定, 可以考虑把table_institution_client这张表拆成2张简单表
    table_institution_client = {
        'type': TableType.TWO_COLUMN,
        'name': '测评机构及委托方信息',
        'end_flag': '',
        'useless_rows': ['测评机构', '委托方'],
        'value_list': [],
        'attrToSet_list': ['InstitutionName',
                           'InstitutionAddress',
                           'InstitutionPostcode',
                           'InstitutionContact',
                           'InstitutionTel',

                           'ClientName',
                           'ClientAddress',
                           'ClientPostcode',
                           'ClientContact',
                           'ClientTel'],
        'field_checktype_list': [
            FieldCheckType.NO_CHECK_TYPE,  # ['InstitutionName',
            FieldCheckType.NO_CHECK_TYPE,  # 'InstitutionAddress',
            FieldCheckType.INT_TO_STR_TYPE,  # 'InstitutionPostcode',
            FieldCheckType.NO_CHECK_TYPE,  # 'InstitutionContact',
            FieldCheckType.INT_TO_STR_TYPE,  # 'InstitutionTel',
            #
            FieldCheckType.NO_CHECK_TYPE,  # 'ClientName',
            FieldCheckType.NO_CHECK_TYPE,  # 'ClientAddress',
            FieldCheckType.INT_TO_STR_TYPE,  # 'ClientPostcode',
            FieldCheckType.NO_CHECK_TYPE,  # 'ClientContact',
            FieldCheckType.INT_TO_STR_TYPE,  # 'ClientTel'],
        ],
        'orm_class': [DeReportInstitution, DeReportClient],
        'cell_list': [
            '(测评机构)名称',
            '(测评机构)地址',
            '(测评机构)邮政编码',
            '(测评机构)联系人',
            '(测评机构)电话',

            '(委托方)名称',
            '(委托方)地址',
            '(委托方)邮政编码',
            '(委托方)联系人',
            '(委托方)电话',
        ]
    }

    # 任务描述 表的字典
    table_task_desc = {
        'type': TableType.TWO_COLUMN,
        'name': '任务描述',
        'end_flag': '',
        'useless_rows': ['任务描述'],
        'excel_date_rows': ['测评通知下发日期', '现场检测日期', '专家评估会日期', '形成报告日期'],  # 需要额外处理的excel_date格式的日期
        'value_list': [],
        'attrToSet_list': [
            '',
            '',
            '',
            '',
            '',
            '',
            '',
        ],
        'orm_class': DeReportTaskDesc,

    }

    # end of 测评任务信息中的表

    # =========================================================================
    # start 第一部分 系统概述

    # 系统总体情况表_上部2个
    table_system_info_upper = {
        'type': TableType.TWO_COLUMN,
        'name': '【信息系统基本情况描述】',
        'end_flag': '系统总体情况表',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [  # 注意填写...
            'SystemDescription',
            'DetectionEvaluationScope'
        ],
        'orm_class': DeReportSystemInfo,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
    }
    # 系统总体情况表
    table_system_info = {
        'type': TableType.SYSTEM_INFO,
        'name': '系统总体情况表',
        'end_flag': '【其他需说明的情况】',
        'useless_rows': ['项  目'],  # 注意填写
        'value_list': [],
        'attrToSet_list': [],  # special table doesn't have attribute to set
        'orm_class': None,  # specail table
        'node_index': NodeIndex.CENTRAL_NODE,
    }

    # 系统总体情况表_全作为一个TWO_COLUMN
    # 顺序: 内部个数--内部具体明细--内部变化情况--外部内容--外部变化情况
    table_system_info_two_column = {
        'type': TableType.TWO_COLUMN,
        'name': '系统总体情况表',  # actually, it is None...
        'end_flag': '',
        'useless_rows': [],  # all useful, because the table_dict has been handled
        'value_list': [],
        'attrToSet_list': [  # total 82 attributes to set
            # inner 安全域划分 个数
            'SecretJuemiArea',
            'SecretJimiArea',
            'SecretMimiArea',
            'SecretNeibuArea',

            # inner 应用系统 个数
            'SecretJuemiApplication',
            'SecretJimiApplication',
            'SecretMimiApplication',
            'SecretNeibuApplication',

            # inner 安全域划分 明细
            'SecretJuemiAreaMemo',
            'SecretJimiAreaMamo',
            'SecretMimiAreaMemo',
            'SecretNeibuAreaMemo',

            # inner 应用系统 明细
            'SecretJuemiApplicationMemo',
            'SecretJimiApplicationMemo',
            'SecretMimiApplicationMemo',
            'SecretNeibuApplicationMemo',

            # inner 安全域划分 变化情况
            'SecretJuemiAreaChanged',
            'SecretJimiAreaChanged',
            'SecretMimiAreaChanged',
            'SecretNeibuAreaChanged',

            # inner 应用系统 变化情况
            'SecretJuemiApplicationChanged',
            'SecretJimiApplicationChanged',
            'SecretMimiApplicationChanged',
            'SecretNeibuApplicationChanged',

            # outer 内容 upper_part
            'SystemName',
            'SecretLevel',
            'SecretLiableDepartment',
            'MaintainLiableDepartment',
            'ExamineCertificate',
            'ExamineInstitution',
            'FirstExamineDate',
            'LastExamineDate',
            'LastEvaluateDate',
            'LastEvaluateInstitution',
            'LastEvaluateReportNumber',
            'NetType',
            'NetUsage',
            'HostRoomAddress',
            'NetMode',

            # outer 内容 down_part
            'WiringPointCount',
            'TerminalPlanCount',
            None,
            'TerminalConnectedCount',
            'ServerCount',
            'SwitchCount',
            'NotebookCount',
            'LocalPrinterCount',
            'NetworkPrinterCount',
            'OtherCountMemo',
            'MobileStorageCount',
            'SystemAdministrator',
            'SecurityOfficer',
            'SecurityAuditor',

            # outer 变化情况 upper_part
            'SystemNameChanged',
            'SecretLevelChanged',
            'SecretLiableDepartmentChanged',
            'MaintainLiableDepartmentChanged',
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            'NetTypeChanged',
            'NetUsageChanged',
            'HostRoomAddressChanged',
            'NetModeChanged',

            # outer 变化情况 down_part
            'WiringPointCountChanged',
            'TerminalPlanCountChanged',
            None,
            'TerminalConnectedCountChanged',
            'ServerCountChanged',
            'SwitchCountChanged',
            'NotebookCountChanged',
            'LocalPrinterCountChanged',
            'NetworkPrinterCountChanged',
            'OtherCountChanged',
            'MobileStorageCountChanged',
            'SystemAdministratorChanged',
            'SecurityOfficerChanged',
            'SecurityAuditorChanged',
        ],
        'field_checktype_list': [
            # inner 安全域划分 个数
            FieldCheckType.INT_TO_STR_TYPE,  # 'SecretJuemiArea',
            FieldCheckType.INT_TO_STR_TYPE,  # 'SecretJimiArea',
            FieldCheckType.INT_TO_STR_TYPE,  # 'SecretMimiArea',
            FieldCheckType.INT_TO_STR_TYPE,  # 'SecretNeibuArea',

            # inner 应用系统 个数
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretJuemiApplication',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretJimiApplication',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretMimiApplication',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretNeibuApplication',

            # inner 安全域划分 明细
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretJuemiAreaMemo',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretJimiAreaMamo',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretMimiAreaMemo',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretNeibuAreaMemo',

            # inner 应用系统 明细
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretJuemiApplicationMemo',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretJimiApplicationMemo',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretMimiApplicationMemo',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretNeibuApplicationMemo',

            # inner 安全域划分 变化情况
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretJuemiAreaChanged',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretJimiAreaChanged',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretMimiAreaChanged',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretNeibuAreaChanged',

            # inner 应用系统 变化情况
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretJuemiApplicationChanged',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretJimiApplicationChanged',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretMimiApplicationChanged',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretNeibuApplicationChanged',

            # outer 内容 upper_part
            FieldCheckType.NO_CHECK_TYPE,  # 'SystemName',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretLevel',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretLiableDepartment',
            FieldCheckType.NO_CHECK_TYPE,  # 'MaintainLiableDepartment',
            FieldCheckType.NO_CHECK_TYPE,  # 'ExamineCertificate',
            FieldCheckType.NO_CHECK_TYPE,  # 'ExamineInstitution',
            FieldCheckType.DATE_TYPE,  # 'FirstExamineDate',
            FieldCheckType.DATE_TYPE,  # 'LastExamineDate',
            FieldCheckType.DATE_TYPE,  # 'LastEvaluateDate',
            FieldCheckType.NO_CHECK_TYPE,  # 'LastEvaluateInstitution',
            FieldCheckType.NO_CHECK_TYPE,  # 'LastEvaluateReportNumber',
            FieldCheckType.NO_CHECK_TYPE,  # 'NetType',
            FieldCheckType.NO_CHECK_TYPE,  # 'NetUsage',
            FieldCheckType.NO_CHECK_TYPE,  # 'HostRoomAddress',
            FieldCheckType.NO_CHECK_TYPE,  # 'NetMode',

            # outer 内容 down_part
            FieldCheckType.NO_CHECK_TYPE,  # 'WiringPointCount',
            FieldCheckType.NO_CHECK_TYPE,  # 'TerminalPlanCount',
            FieldCheckType.NO_CHECK_TYPE,  # None,
            FieldCheckType.NO_CHECK_TYPE,  # 'TerminalConnectedCount',
            FieldCheckType.NO_CHECK_TYPE,  # 'ServerCount',
            FieldCheckType.NO_CHECK_TYPE,  # 'SwitchCount',
            FieldCheckType.NO_CHECK_TYPE,  # 'NotebookCount',
            FieldCheckType.NO_CHECK_TYPE,  # 'LocalPrinterCount',
            FieldCheckType.NO_CHECK_TYPE,  # 'NetworkPrinterCount',
            FieldCheckType.NO_CHECK_TYPE,  # 'OtherCountMemo',
            FieldCheckType.NO_CHECK_TYPE,  # 'MobileStorageCount',
            FieldCheckType.NO_CHECK_TYPE,  # 'SystemAdministrator',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecurityOfficer',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecurityAuditor',

            # outer 变化情况 upper_part
            FieldCheckType.NO_CHECK_TYPE,  # 'SystemNameChanged',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretLevelChanged',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecretLiableDepartmentChanged',
            FieldCheckType.NO_CHECK_TYPE,  # 'MaintainLiableDepartmentChanged',
            FieldCheckType.NO_CHECK_TYPE,  # None,
            FieldCheckType.NO_CHECK_TYPE,  # None,
            FieldCheckType.NO_CHECK_TYPE,  # None,
            FieldCheckType.NO_CHECK_TYPE,  # None,
            FieldCheckType.NO_CHECK_TYPE,  # None,
            FieldCheckType.NO_CHECK_TYPE,  # None,
            FieldCheckType.NO_CHECK_TYPE,  # None,
            FieldCheckType.NO_CHECK_TYPE,  # NetTypeChanged,
            FieldCheckType.NO_CHECK_TYPE,  # NetUsageChanged,
            FieldCheckType.NO_CHECK_TYPE,  # HostRoomAddressChanged,
            FieldCheckType.NO_CHECK_TYPE,  # NetModeChanged,

            # outer 变化情况 down_part
            FieldCheckType.NO_CHECK_TYPE,  # 'WiringPointCountChanged',
            FieldCheckType.NO_CHECK_TYPE,  # 'TerminalPlanCountChanged',
            FieldCheckType.NO_CHECK_TYPE,  # None,
            FieldCheckType.NO_CHECK_TYPE,  # 'TerminalConnectedCountChanged',
            FieldCheckType.NO_CHECK_TYPE,  # 'ServerCountChanged',
            FieldCheckType.NO_CHECK_TYPE,  # 'SwitchCountChanged',
            FieldCheckType.NO_CHECK_TYPE,  # 'NotebookCountChanged',
            FieldCheckType.NO_CHECK_TYPE,  # 'LocalPrinterCountChanged',
            FieldCheckType.NO_CHECK_TYPE,  # 'NetworkPrinterCountChanged',
            FieldCheckType.NO_CHECK_TYPE,  # 'OtherCountChanged',
            FieldCheckType.NO_CHECK_TYPE,  # 'MobileStorageCountChanged',
            FieldCheckType.NO_CHECK_TYPE,  # 'SystemAdministratorChanged',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecurityOfficerChanged',
            FieldCheckType.NO_CHECK_TYPE,  # 'SecurityAuditorChanged',
        ],
        'orm_class': DeReportSystemInfo,
        'node_index': NodeIndex.CENTRAL_NODE,
    }

    # 系统总体情况表_下部_其他
    table_system_info_others = {
        'type': TableType.TWO_COLUMN,
        'name': '【其他需说明的情况】',
        'end_flag': '',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [  # 注意填写...
            'OtherDescription',
        ],
        'orm_class': DeReportSystemInfo,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
    }

    # 上次测评或评估意见整改情况表
    table_system_rectification = {
        'type': TableType.MULTI_COLUMN,
        'name': '上次测评或评估意见整改情况表',
        'end_flag': '',
        'useless_rows': ['序号'],  # 注意填写
        'value_list': [],
        'attrToSet_list': [
            'SortNo',
            None,
            'SystemProblem',
            'rectification_result'
        ],
        'field_checktype_list': [
        ],
        'orm_class': ReportSystemRectification  # todo, 这个orm_class更改过
    }

    # 表格 2.总体网络拓扑图
    table_topo = {
        'type': TableType.TWO_COLUMN,
        'name': '2.总体网络拓扑图',
        'end_flag': '',
        'useless_rows': [],  # useless_row, 不用将表标题加入
        'value_list': [],
        'attrToSet_list': [
            'TopoDescription',
            'TopoImage',
            'OtherDescription',
        ],
        'orm_class': DeReportTopo,
        'node_index': None
    }
    # end 第一部分 系统概述
    # =========================================================================

    # =========================================================================
    # start 中心节点
    # 物理环境表附属信息
    table_physical_node_others = {
        'type': TableType.TWO_COLUMN,
        'name': '【物理位置1环境描述】',
        'end_flag': '物理环境表',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [
            'Physical01Description',
            'Physical01Image',
        ],
        'orm_class': DeReportNode,
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,

    }
    # 表 物理环境表
    table_physical_node = {
        'type': TableType.TWO_COLUMN,
        'name': '物理环境表',
        'end_flag': '',
        'useless_rows': ['项目'],
        'value_list': [],
        'attrToSet_list': [
            'PhysicalAddress',
            'MinDistanceEast',
            'MinDistanceWest',
            'MinDistanceSouth',
            'MinDistanceNorth',
            'PeripheralProtection',
            'BuildingDistribution',
            'PassagewayCount',
            'VitalAddress',
            'CenterRoom',
            'IsSingle',
            'IsControl',
            'IsClosed',
        ],
        'orm_class': DeReportPhysicalNode,
        'constant_attr': {
            'PhysicalType': 1
        },
        'node_index': NodeIndex.CENTRAL_NODE
    }
    # 物理安全措施表
    table_physical_security = {
        'type': TableType.MULTI_COLUMN,
        'name': '物理安全措施表',
        'end_flag': '',
        'useless_rows': ['序号'],  # 注意填写
        'value_list': [],
        'attrToSet_list': [
            'SortNo',
            'SecurityTypeName',
            'SecurityName',
            'HasVideo',
            'HasAlarm',
            'HasAccess',
            'HasSentry',
            'SecurityMemo',
        ],
        'orm_class': DeReportPhysicalSecurity,
        'node_index': NodeIndex.CENTRAL_NODE,
        'constant_attr': {'PhysicalType': 1},
    }

    # 物理环境表2附属信息
    table_physical_node_others_2 = {
        'type': TableType.TWO_COLUMN,
        'name': '【物理位置2环境描述】',
        'end_flag': '物理环境表',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [
            'Physical02Description',
            'Physical02Image',
        ],
        'orm_class': DeReportNode,
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,

    }
    # todo 物理环境相关的: 物理环境表, 物理安全措施表. 这个xxx表2 其实应该是有n个
    # 表 物理环境表2
    table_physical_node_2 = {
        'type': TableType.TWO_COLUMN,
        'name': '物理环境表',
        'end_flag': '',
        'useless_rows': ['项目'],
        'value_list': [],
        'attrToSet_list': [
            'PhysicalAddress',
            'MinDistanceEast',
            'MinDistanceWest',
            'MinDistanceSouth',
            'MinDistanceNorth',
            'PeripheralProtection',
            'BuildingDistribution',
            'PassagewayCount',
            'VitalAddress',
            'CenterRoom',
            'IsSingle',
            'IsControl',
            'IsClosed',
        ],
        'orm_class': DeReportPhysicalNode,
        'constant_attr': {
            'PhysicalType': 2
        },
        'node_index': NodeIndex.CENTRAL_NODE
    }
    # 物理安全措施表2
    table_physical_security_2 = {
        'type': TableType.MULTI_COLUMN,
        'name': '物理安全措施表',
        'end_flag': '',
        'useless_rows': ['序号'],  # 注意填写
        'value_list': [],
        'attrToSet_list': [
            'SortNo',
            'SecurityTypeName',
            'SecurityName',
            'HasVideo',
            'HasAlarm',
            'HasAccess',
            'HasSentry',
            'SecurityMemo',
        ],
        'orm_class': DeReportPhysicalSecurity,
        'node_index': NodeIndex.CENTRAL_NODE,
        'constant_attr': {'PhysicalType': 2},
    }

    # 网络环境 (各建筑物综合布线情况表) 的附属信息
    table_network_environment_others = {
        'type': TableType.TWO_COLUMN,
        'name': '【网络环境描述】',
        'end_flag': '各建筑物综合布线情况表',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [
            'NetworkDescription',
            'NetworkImage',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }
    # 表 各建筑物综合布线情况表
    table_network_environment = {
        'type': TableType.TWO_COLUMN,
        'name': '各建筑物综合布线情况表',
        'end_flag': '',
        'useless_rows': ['项目'],
        'value_list': [],
        'attrToSet_list': [
            'Situation01',
            'Situation02',
            'Situation03',
        ],
        'field_checktype_list': [
            FieldCheckType.NO_CHECK_TYPE,
            FieldCheckType.NO_CHECK_TYPE,
            FieldCheckType.NO_CHECK_TYPE,
            FieldCheckType.NO_CHECK_TYPE,
            FieldCheckType.NO_CHECK_TYPE,
            FieldCheckType.NO_CHECK_TYPE,
            FieldCheckType.NO_CHECK_TYPE,
            FieldCheckType.DATE_TYPE,
        ],
        'orm_class': DeReportNetworkEnvironment,  # 小表都填到DeReportNode中去
        'node_index': NodeIndex.CENTRAL_NODE,
    }

    # 表格 安全域划分情况表
    table_network_area = {
        'type': TableType.MULTI_COLUMN,
        'name': '安全域划分情况表',
        'end_flag': '',
        'useless_rows': ['安全域划分情况表', '序号'],
        'value_list': [],
        'attrToSet_list': [
            'SortNo',
            'AreaName',
            'SecretLevel',
            'DivisionDevice',
            'AccessControlRule',
            'DeviceDescription',
            'VlanDescription',
        ],
        'orm_class': DeReportNetworkArea,
        'node_index': NodeIndex.CENTRAL_NODE
    }

    # 表格 VLAN划分情况表
    table_network_vlan = {
        'type': TableType.MULTI_COLUMN,
        'name': 'VLAN划分情况表',
        'end_flag': '【其他需说明的情况】',
        'useless_rows': ['序号'],
        'value_list': [],
        'attrToSet_list': [
            'SortNo',
            'VlanName',
            'VlanMemo',
            'SecretLevel',
            'IpRange',
            'AccessControlRule',
            'AreaName',
        ],
        'orm_class': DeReportNetworkVlan,
        'node_index': NodeIndex.CENTRAL_NODE
    }
    # 附加信息 网络环境
    table_network_other_description = {
        'type': TableType.TWO_COLUMN,
        'name': '【其他需说明的情况】',
        'end_flag': '',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [
            'NetworkOtherDescription',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }

    # 防护措施调整表附加表
    table_protection_adjust_others = {
        'type': TableType.TWO_COLUMN,
        'name': '【系统定级及防护措施调整情况描述】',
        'end_flag': '防护措施调整表',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [
            'ProtectionDescription'
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }
    # 表格 防护措施调整表
    table_protection_adjust = {
        'type': TableType.MULTI_COLUMN,
        'name': '防护措施调整表',
        'end_flag': '',
        'useless_rows': ['序号'],
        'value_list': [],
        'attrToSet_list': [
            'SortNo',
            'OldTerm',
            'NewTerm',
            'AdjustReason',
            'AdjustedMemo',
        ],
        'orm_class': DeReportProtectionAdjust,
        'node_index': NodeIndex.CENTRAL_NODE
    }

    # 表格 硬件平台表_others
    table_hardware_platform_description = {
        'type': TableType.TWO_COLUMN,
        'name': '【硬件平台描述】',
        'end_flag': '硬件平台表',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [
            'HardwarePlatformDescription',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }
    # 表格 硬件平台表
    table_hardware_platform = {
        'type': TableType.MULTI_COLUMN,
        'name': '硬件平台表',
        'end_flag': '',
        'useless_rows': ['序号'],
        'value_list': [],
        'attrToSet_list': [
            'SortNo',
            'Maker',
            'HardwareName',
            'HardwareModel',
            'Qty',
            'Usage',
            'InstallationLocation',
        ],
        'orm_class': DeReportHardwarePlatform,
        'node_index': NodeIndex.CENTRAL_NODE
    }

    # 表格 软件平台表_others
    table_software_platform_description = {
        'type': TableType.TWO_COLUMN,
        'name': '【软件平台描述】',
        'end_flag': '软件平台表',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [
            'SoftwarePlatformDescription',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }
    # 表格 软件平台表
    table_software_platform = {
        'type': TableType.MULTI_COLUMN,
        'name': '软件平台表',
        'end_flag': '',
        'useless_rows': ['序号'],
        'value_list': [],
        'attrToSet_list': [
            'SortNo',
            'Maker',
            'SoftwareName',
            'SoftwareVersion',
            'Usage',
            'DeploymentLocation',
        ],
        'orm_class': DeReportSoftwarePlatform,
        'node_index': NodeIndex.CENTRAL_NODE
    }

    # 表格 安全保密产品表_others
    table_device_others = {
        'type': TableType.TWO_COLUMN,
        'name': '【安全保密设备描述】',
        'end_flag': '安全保密产品表',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [
            'DeviceDescription',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }
    # 表格 安全保密产品表
    table_device = {
        'type': TableType.MULTI_COLUMN,
        'name': '安全保密产品表',
        'end_flag': '',
        'useless_rows': ['序号'],
        'value_list': [],
        'attrToSet_list': [
            'SortNo',
            'DeviceType',
            'DeviceInfo',
            'Usage',
            'DeploymentLocation',
            'Qty',
            None,
            'Certificate',
        ],
        'orm_class': DeReportDevice,
        'node_index': NodeIndex.CENTRAL_NODE
    }

    # 表格 应用系统表_others
    table_application_others = {
        'type': TableType.TWO_COLUMN,
        'name': '【应用系统描述】',
        'end_flag': '应用系统表',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [
            'ApplicationDescription',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }
    # 表格 应用系统表
    table_application = {
        'type': TableType.MULTI_COLUMN,
        'name': '应用系统表',
        'end_flag': '',
        'useless_rows': ['序号'],
        'value_list': [],
        'attrToSet_list': [
            'SortNo',
            'AppInfo',
            'SecretLevel',
            'Usage',
            'DeploymentLocation',
            'UserWide',
            'AccessControlRule',
            'DatabaseSystem',
            'DatabaseAddress',
            'Maker',
            'InteractionDescription',
        ],
        'orm_class': DeReportApplication,
        'node_index': NodeIndex.CENTRAL_NODE
    }

    # 表格 身份鉴别措施表_desc
    table_identity_description = {
        'type': TableType.TWO_COLUMN,
        'name': '【身份鉴别措施描述】',
        'end_flag': '身份鉴别措施表',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [
            'IdentityDescription',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }
    # 表格 身份鉴别措施表
    table_identity = {
        'type': TableType.MULTI_COLUMN,
        'name': '身份鉴别措施表',
        'end_flag': '【其他需说明的情况】',
        'useless_rows': ['鉴别对象'],
        'value_list': [],
        'attrToSet_list': [
            'IdentityObjectName',
            'LocalMethod',
            'RemoteMethod',
        ],
        'orm_class': DeReportIdentity,
        'node_index': NodeIndex.CENTRAL_NODE,
    }
    # 表格 身份鉴别措施表_others
    table_identity_others = {
        'type': TableType.TWO_COLUMN,
        'name': '【其他需说明的情况】',
        'end_flag': '',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [
            'IdentityOtherDescription',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }

    # 表格 安全审计措施表_desc
    table_security_audit_desc = {
        'type': TableType.TWO_COLUMN,
        'name': '【安全审计措施描述】',
        'end_flag': '安全审计措施表',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [
            'SecurityDescription',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }
    # 表格 安全审计措施表
    table_security_audit = {
        'type': TableType.MULTI_COLUMN,
        'name': '安全审计措施表',
        'end_flag': '【其他需说明的情况】',
        'useless_rows': ['审计措施'],
        'value_list': [],
        'attrToSet_list': [
            'AuditMeasure',
            'AuditObjectName',
        ],
        'orm_class': DeReportSecurityAudit,
        'node_index': NodeIndex.CENTRAL_NODE,
    }
    # 表格 安全审计措施表_others
    table_security_audit_others = {
        'type': TableType.TWO_COLUMN,
        'name': '【其他需说明的情况】',
        'end_flag': '',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [  # 注意填写...
            'SecurityOtherDescription',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }

    # 表格 电磁泄漏发射防护措施表_desc
    table_elec_mag_protection_desc = {
        'type': TableType.TWO_COLUMN,
        'name': '【电磁泄漏发射防护措施描述】',
        'end_flag': '电磁泄漏发射防护措施表',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [  # 注意填写...
            'ElectromagneticDescription',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }
    # 表格 电磁泄漏发射防护措施表
    table_elec_mag_protection = {
        'type': TableType.MULTI_COLUMN,
        'name': '电磁泄漏发射防护措施表',
        'end_flag': '【其他需说明的情况】',
        'useless_rows': ['项目'],  # 注意填写
        'value_list': [],
        'attrToSet_list': [
            'ProtectionItemName',
            'ProtectionContent',
        ],
        'orm_class': DeReportElectromagneticProtection,
        'node_index': NodeIndex.CENTRAL_NODE,
    }
    # 表格 电磁泄漏发射防护措施表_others
    table_elec_mag_protection_others = {
        'type': TableType.TWO_COLUMN,
        'name': '【其他需说明的情况】',
        'end_flag': '',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [  # 注意填写...
            'ElectromagneticOtherDescription',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }

    # 表 项目 (违规外联监控)_desc
    table_outreach_protection_desc = {
        'type': TableType.TWO_COLUMN,
        'name': '【违规外联监控措施描述】',
        'end_flag': '项目',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [  # 注意填写...
            'OutreachDescription',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }
    # 表 项目 (违规外联监控)
    table_outreach_protection = {
        'type': TableType.MULTI_COLUMN,
        'name': '项目',
        'end_flag': '【其他需说明的情况】',
        'useless_rows': [],  # 注意填写
        'value_list': [],
        'attrToSet_list': [
            'ProtectionItem',
            'ProtectionItemName',
            'ProtectionContent',
        ],
        'orm_class': DeReportOutreachProtection,
        'node_index': NodeIndex.CENTRAL_NODE,
    }
    # 表 项目 (违规外联监控)_others
    table_outreach_protection_others = {
        'type': TableType.TWO_COLUMN,
        'name': '【其他需说明的情况】',
        'end_flag': '',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [  # 注意填写...
            'OutreachOtherDescription',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }

    # 表 信息输入输出措施表_desc
    table_io_protection_desc = {
        'type': TableType.TWO_COLUMN,
        'name': '【信息输入输出机所在物理位置、\n管理部门及负责人或操作人员描述】',
        'end_flag': '信息输入输出措施表',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [  # 注意填写...
            'IoDescription',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }
    # 表 信息输入输出措施表
    table_io_protection = {
        'type': TableType.MULTI_COLUMN,
        'name': '信息输入输出措施表',
        'end_flag': '【其他需说明的情况】',
        'useless_rows': [['', '流程及措施']],  # 注意填写
        'value_list': [],
        'attrToSet_list': [
            'ProtectionIo',
            'ProtectionItemName',
            'ProtectionContent',
        ],
        'orm_class': DeReportIoProtection,
        'node_index': NodeIndex.CENTRAL_NODE,
    }
    # 表 信息输入输出措施表_others
    table_io_protection_others = {
        'type': TableType.TWO_COLUMN,
        'name': '【其他需说明的情况】',
        'end_flag': '',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [  # 注意填写...
            'IoOtherDescription',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }

    # 表 联网笔记本、介质管控措施表_desc
    table_medium_protection_desc = {
        'type': TableType.TWO_COLUMN,
        'name': '【联网笔记本、\n介质管控措施描述】',
        'end_flag': '联网笔记本、介质管控措施表',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [  # 注意填写...
            'MediumDescription',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }
    # 表 联网笔记本、介质管控措施表
    table_medium_protection = {
        'type': TableType.MULTI_COLUMN,
        'name': '联网笔记本、介质管控措施表',
        'end_flag': '【其他需说明的情况】',
        'useless_rows': ['项目'],  # 注意填写
        'value_list': [],
        'attrToSet_list': [
            'ProtectionItemName',
            'ProtectionContent',
        ],
        'orm_class': DeReportMediumProtection,
        'node_index': NodeIndex.CENTRAL_NODE,
    }
    # 表 联网笔记本、介质管控措施表_others
    table_medium_protection_others = {
        'type': TableType.TWO_COLUMN,
        'name': '【其他需说明的情况】',
        'end_flag': '',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [  # 注意填写...
            'MediumOtherDescription',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }

    # 表格 服务器安全保密防护措施表_desc
    table_server_protection_desc = {
        'type': TableType.TWO_COLUMN,
        'name': '【服务器安全保密防护措施描述】',
        'end_flag': '服务器安全保密防护措施表',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [  # 注意填写...
            'ServerDescription',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }
    # 表格 服务器安全保密防护措施表
    table_server_protection = {
        'type': TableType.MULTI_COLUMN,
        'name': '服务器安全保密防护措施表',
        'end_flag': '【其他需说明的情况】',
        'useless_rows': ['序号'],
        'value_list': [],
        'attrToSet_list': [
            'SortNo',
            'ServerName',
            'ServerIp',
            'DeploymentLocation',
            'TriadDescription',
            'AuditSystem',
            'AntivirusSoftware',
            'OtherDescription',
        ],
        'orm_class': DeReportServerProtection,
        'node_index': NodeIndex.CENTRAL_NODE
    }
    # 表格 服务器安全保密防护措施表_others
    table_server_protection_others = {
        'type': TableType.TWO_COLUMN,
        'name': '【其他需说明的情况】',
        'end_flag': '',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [  # 注意填写...
            'ServerOtherDescription',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }

    # 表格 安全保密管理人员情况表_desc
    table_manager_desc = {
        'type': TableType.TWO_COLUMN,
        'name': '【安全保密管理机构描述】',
        'end_flag': '安全保密管理人员情况表',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [  # 注意填写...
            'ManagerDescription',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }
    # 表格 安全保密管理人员情况表
    table_manager = {
        'type': TableType.MULTI_COLUMN,
        'name': '安全保密管理人员情况表',
        'end_flag': '',
        'useless_rows': ['序号'],
        'value_list': [],
        'attrToSet_list': [
            'SortNo',
            'PostName',
            'PostDuty',
            'PersonName',
            'PersonDepartment',
            'PersonTitle',
            'Certificate',
            'TrainDate'
        ],
        'field_checktype_list': [
            FieldCheckType.NO_CHECK_TYPE,
            FieldCheckType.NO_CHECK_TYPE,
            FieldCheckType.NO_CHECK_TYPE,
            FieldCheckType.NO_CHECK_TYPE,
            FieldCheckType.NO_CHECK_TYPE,
            FieldCheckType.NO_CHECK_TYPE,
            FieldCheckType.NO_CHECK_TYPE,
            FieldCheckType.DATE_TYPE,
        ],
        'orm_class': DeReportManager,
        'node_index': NodeIndex.CENTRAL_NODE
    }

    # 表格 安全保密管理制度情况表
    table_manage_system = {
        'type': TableType.MULTI_COLUMN,
        'name': '安全保密管理制度情况表',
        'end_flag': '',
        'useless_rows': ['序号'],
        'value_list': [],
        'attrToSet_list': [
            'SortNo',
            'SystemName',
            'Issuer',
            'IssueDate',
            'IssueRange',
        ],
        'field_checktype_list': [
            FieldCheckType.NO_CHECK_TYPE,  # 'SortNo',
            FieldCheckType.NO_CHECK_TYPE,  # 'SystemName',
            FieldCheckType.NO_CHECK_TYPE,  # 'Issuer',
            FieldCheckType.DATE_TYPE,  # 'IssueDate',
            FieldCheckType.NO_CHECK_TYPE,  # 'IssueRange',
        ],
        'orm_class': DeReportManagementSystem,
        'node_index': NodeIndex.CENTRAL_NODE,
        'cell_list': [

        ]
    }

    # 表 集成资质单位
    table_integration_unit = {
        'type': TableType.MULTI_COLUMN,
        'name': '集成资质单位',
        'end_flag': END_SYMBOL,
        'useless_rows': [''],
        'value_list': [],
        'attrToSet_list': [
            'UnitTypeName',
            'UnitName',
            'QualificationLevel',
            'Certificate',
            'Memo',
        ],
        'orm_class': DeReportIntegrationUnit,
        'node_index': NodeIndex.CENTRAL_NODE
    }

    # 国产化替代情况表 情况说明
    table_homemade_substitute_description = {
        'type': TableType.TWO_COLUMN,
        'name': '【国产化替代情况说明】',
        'end_flag': '国产化替代情况表',
        'useless_rows': [],
        'value_list': [],
        'attrToSet_list': [
            'HomemadeDescription',
        ],
        'orm_class': DeReportNode,  # 小表都填到DeReportNode中去
        'is_header_name_useless': False,  # 小表没有表名, name是第一行
        'node_index': NodeIndex.CENTRAL_NODE,
    }
    # 表 国产化替代情况表
    table_homemade_substitute = {
        'type': TableType.MULTI_COLUMN,
        'name': '国产化替代情况表',
        'end_flag': '【其他】',
        'useless_rows': [''],
        'value_list': [],
        'attrToSet_list': [
            'SubstituteObjectName',
            'SubstituteQty',
            'TotalQty',
            'Memo',
        ],
        'orm_class': DeReportHomemadeSubstitute,
        'node_index': NodeIndex.CENTRAL_NODE
    }
    # 国产化替代情况表 其他
    table_homemade_substitute_others = {

    }

    # end 中心节点
    # =========================================================================

    # =========================================================================
    # start 第二部分 系统概述
    table_detection_tool = {
        'type': TableType.MULTI_COLUMN,
        'name': '检测工具表',
        'end_flag': '',
        'useless_rows': ['序号'],
        'value_list': [],
        'attrToSet_list': [
            'SortNo',
            'ToolMaker',
            'ToolName',
            'ToolModel',
            'ToolVersion',
            'ToolSn',
            'Memo',
        ],
        'orm_class': DeReportDetectionTool,
        'node_index': None
    }
    # end of 第二部分 系统概述 的表
    # =========================================================================

    # =========================================================================
    # start 第三部分 专家评估
    # 表 专家组名单
    table_professionals = {
        'type': TableType.MULTI_COLUMN,
        'name': '专家组名单',
        'end_flag': '',
        'useless_rows': ['序号'],
        'value_list': [],
        'attrToSet_list': [
            'SortNo',
            'Name',
            'Unit',
            'Major',
            'Professional',
            'JobTitle',
        ],
        'orm_class': DeReportProfessionals,
        'node_index': None
    }
    # end 第三部分 专家评估
    # =========================================================================

    # =========================================================================
    # start 第四部分 测评结论
    # end 第四部分 测评结论
    # =========================================================================

    # =========================================================================
    # start 附件
    # 表 网络扫描结果表（仅列出部分高风险漏洞）
    table_vulnerability_network = {
        'type': TableType.MULTI_COLUMN,
        'name': '网络扫描结果表（仅列出部分高风险漏洞）',
        'end_flag': '',
        'useless_rows': ['序号'],
        'value_list': [],
        'attrToSet_list': [
            'SortNo',
            'VulnerabilityName',
            'VulnerabilityLocation',
            'VulnerabilityNO',
        ],
        'orm_class': DeReportVulnerability,
        'node_index': None,
        'constant_attr': {
            'ScanningType': 10,
            'ScanningTypeName': '网络扫描'
        }
    }

    # 表 数据库扫描结果表（仅列出部分高风险漏洞）
    table_vulnerability_db = {
        'type': TableType.MULTI_COLUMN,
        'name': '数据库扫描结果表（仅列出部分高风险漏洞）',
        'end_flag': '',
        'useless_rows': ['序号'],
        'value_list': [],
        'attrToSet_list': [
            'SortNo',
            'VulnerabilityName',
            'VulnerabilityLocation',
            'VulnerabilityNO',
        ],
        'orm_class': DeReportVulnerability,
        'node_index': None,
        'constant_attr': {
            'ScanningType': 20,
            'ScanningTypeName': '数据库扫描'
        }
    }

    # 表 附录1-1：用户终端漏洞检测结果及完善建议
    table_vulnerability_opinion_terminal = {
        'type': TableType.MULTI_COLUMN,
        'name': '附录1-1：用户终端漏洞检测结果及完善建议',
        'end_flag': '',
        'useless_rows': ['漏洞序列'],
        'value_list': [],
        'attrToSet_list': [
            'VulnerabilitySn',
            'VulnerabilityName',
            'VulnerabilityMemo',
            'OpinionContent',
        ],
        'orm_class': DeReportVulnerabilityOpinion,
        'node_index': None,
        'constant_attr': {
            'VulnerabilityType': 10,
            'VulnerabilityTypeName': '用户终端漏洞'
        }
    }

    # 表 附录1-2：服务器漏洞检测结果及完善建议
    table_vulnerability_opinion_server = {
        'type': TableType.MULTI_COLUMN,
        'name': '附录1-2：服务器漏洞检测结果及完善建议',
        'end_flag': '',
        'useless_rows': ['漏洞序列'],
        'value_list': [],
        'attrToSet_list': [
            'VulnerabilitySn',
            'VulnerabilityName',
            'VulnerabilityMemo',
            'OpinionContent',
        ],
        'orm_class': DeReportVulnerabilityOpinion,
        'node_index': None,
        'constant_attr': {
            'VulnerabilityType': 20,
            'VulnerabilityTypeName': '服务器漏洞'
        }

    }

    # 表 附录1-3：数据库系统漏洞检测结果及完善建议
    table_vulnerability_opinion_db = {
        'type': TableType.MULTI_COLUMN,
        'name': '附录1-3：数据库系统漏洞检测结果及完善建议',
        'end_flag': '',
        'useless_rows': ['漏洞序列'],
        'value_list': [],
        'attrToSet_list': [
            'VulnerabilitySn',
            'VulnerabilityName',
            'VulnerabilityMemo',
            'OpinionContent',
        ],
        'orm_class': DeReportVulnerabilityOpinion,
        'node_index': None,
        'constant_attr': {
            'VulnerabilityType': 30,
            'VulnerabilityTypeName': '数据库系统漏洞'
        }

    }

    # 表 用户终端电磁泄漏发射测试结果
    table_electromagnetic_leakage = {
        'type': TableType.MULTI_COLUMN,
        'name': '用户终端电磁泄漏发射测试结果',
        'end_flag': '',
        'useless_rows': ['序号'],
        'value_list': [],
        'attrToSet_list': [
            'SortNo',
            'Model',
            'Department',
            'Location',
            'MinDistance',
            'SignalNoise',
            'AcceptDistance',
            'BMB2',
        ],
        'orm_class': DeReportElectromagneticLeakage,
        'node_index': None
    }
    # end 附件
    # =========================================================================

    # 各个sheet对应的表, 如果这个dict动态完成了, 就可以套用原来的方法
    tables_in_sheets_dict = {
        '测评任务信息': [
            table_front_cover,  # list中每一项是一个dict, 此dict可以对应一个TableObj
            table_sign_off,
            table_institution_client,
            # table_task_desc
        ],
        '第一部分 系统概述': [
            table_system_info_upper,
            table_system_info,
            table_system_info_others,
            table_system_rectification,
            table_topo,
        ],

        '第二部分 系统检测': [
            table_detection_tool,
        ],
        '第三部分 专家评估': [
            table_professionals,
        ],
        '第四部分 测评结论': [],
        '附件': [
            table_vulnerability_network,
            table_vulnerability_db,
            table_vulnerability_opinion_terminal,
            table_vulnerability_opinion_server,
            table_vulnerability_opinion_db,
            table_electromagnetic_leakage,
        ],
    }

    # 需要动态生成的物理节点相关的 固定部分
    node_table_list_one_phy = [
        table_physical_node_others,
        table_physical_node,
        table_physical_security,
    ]

    # 把这个价到tables_in_sheets_dict, key 是sheet_name
    node_table_list_static = [
            # todo 现在physical_node的个数是不定的, 可以根据all_info的phy_node_id个数来确定


            table_network_environment_others,
            table_network_environment,
            table_network_area,
            table_network_vlan,
            table_network_other_description,

            table_protection_adjust_others,
            table_protection_adjust,

            table_hardware_platform_description,
            table_hardware_platform,

            table_software_platform_description,
            table_software_platform,

            table_device_others,
            table_device,

            table_application_others,
            table_application,

            table_identity_description,
            table_identity,
            table_identity_others,

            table_security_audit_desc,
            table_security_audit,
            table_security_audit_others,

            table_elec_mag_protection_desc,
            table_elec_mag_protection,
            table_elec_mag_protection_others,

            table_outreach_protection_desc,
            table_outreach_protection,
            table_outreach_protection_others,

            table_io_protection_desc,
            table_io_protection,
            table_io_protection_others,

            table_medium_protection_desc,
            table_medium_protection,
            table_medium_protection_others,

            table_server_protection_desc,
            table_server_protection,
            table_server_protection_others,

            table_manager_desc,
            table_manager,

            table_manage_system,
            table_integration_unit,

            table_homemade_substitute_description,
            table_homemade_substitute,
        ],

    # mapping of sheet_index and table_name_dict # SHEET_INDEX_DICT = { #     0: TABLE_NAME_DICT_QUEST_INFO,
    #     1: TABLE_NAME_DICT_PART_1,
    #
    # }

    def __init__(self, excel_name, all_level_id_obj: AllLevelIdInfo = None):
        self.EXCEL_NAME = excel_name
        self.excel_helper = ExcelHelper(file_name=excel_name)
        self.all_level_id = all_level_id_obj  # 各级id的数据
        pass

    def getNodeIdList(self):
        """每个report都需要不同的NodeId, 这些nodeId是使用生成器自动生成的"""
        node_id_list = []
        id_generator = globalIdGenerator
        for i in range(self.node_num):
            node_id = id_generator.getNextId()
            node_id_list.append(node_id)
            pass
        self.node_id_list = node_id_list
        return node_id_list
        pass

    # VERY critical method...
    def __extractResultFromAllRowList(self, all_row_list, table_obj):
        """
        从all_row_list中, 根据table_type, 提取出最终结果

        :param all_row_list: ...
        :param table_obj: table obj
        :return: 最终处理结果result
        """
        type_function_dict = {
            # TableType.TWO_COLUMN: self.__handleTwoColumn(all_row_list, table_obj),
            # TableType.MULTI_COLUMN: self.__handleMultiColumn(all_row_list, table_obj),
            # TableType.SIGN_OFF: self.__handleSignOff(all_row_list, table_obj),
            TableType.TWO_COLUMN: self.__handleTwoColumn,
            TableType.MULTI_COLUMN: self.__handleMultiColumn,
            TableType.SIGN_OFF: self.__handleSignOff,
            TableType.SYSTEM_INFO: self.__handleSystemInfo,
        }
        for tableType_key in type_function_dict:
            if table_obj.type == tableType_key:
                result = type_function_dict[tableType_key](all_row_list, table_obj)
                return result
        pass

    def __handleTwoColumn(self, all_row_list: list, table_obj: TableObj):
        """
        对于towColumn的表的一般处理方法

        :param all_row_list: ...
        :param table_obj: ...
        :return: 最终结果
        """
        if table_obj.type != TableType.TWO_COLUMN:
            return
        result = []
        useful_row_index = 0
        for row in all_row_list:
            if row[0] in table_obj.useless_rows:  # 判断无用行
                continue
            useful_cell = row[1]  # 第二列是存储实际数据的地方
            useful_cell = self.__cell_type_check(useful_cell, useful_row_index, table_obj)
            useful_row_index += 1
            result.append(useful_cell)
        table_obj.value_list = result
        return table_obj
        pass

    def __cell_type_check(self, cell, cell_index_in_record, table_obj):
        """
        对一个单元格进行格式检查

        :param cell: 待处理的单元格内容
        :param cell_index_in_record: 单元格在一条记录中的index值
        :param table_obj: tableObj 对象
        :return: 处理过的 cell
        """
        if not table_obj.field_checktype_list:  # 这个table 不用进行类型检查
            return cell
        try:
            cell_check_type = table_obj.field_checktype_list[cell_index_in_record]
            if cell_check_type == FieldCheckType.DATE_TYPE:  # 判断是否更改格式
                cell, is_cellType_correct = ExcelInfo.__handle_type_ExcelDate(cell)
                self.__set_cell_type(table_obj, cell_index_in_record, is_cellType_correct)
                pass
            elif cell_check_type == FieldCheckType.INT_TO_STR_TYPE:  # 去掉小数点和0, 转为str, 如电话号码, 邮编
                cell, is_cellType_correct = ExcelInfo.__handle_type_int2str(cell)
                self.__set_cell_type(table_obj, cell_index_in_record, is_cellType_correct)
                pass
            elif cell_check_type == FieldCheckType.SCORE_TYPE:  # 分数类型, 小数...
                cell, is_cellType_correct = ExcelInfo.__handle_type_score(cell)
                self.__set_cell_type(table_obj, cell_index_in_record, is_cellType_correct)
        except IndexError:
            print(table_obj)
        return cell
        pass

    @staticmethod
    def __set_cell_type(table_obj, cell_index, is_cellType_correct):
        """set the table_obj wrong_cell_index parameter, append cell_index to  wrong_cell_index if
         is_cellType_correct is False, otherwise do nothing
         """
        if is_cellType_correct is False:
            table_obj.wrongType_cell_index.append(cell_index)
        else:
            pass
        pass

    def __handleMultiColumn(self, all_row_list, table_obj: TableObj):
        """处理多列的表格的一般方法"""
        result = []
        for row in all_row_list:
            if self.__is_useless_row(row, table_obj) is True:
                continue
                pass
            # 处理row 中所有 cell 的格式
            for cell_index in range(len(table_obj.attrToSet_list)):
                row[cell_index] = self.__cell_type_check(row[cell_index], cell_index, table_obj)
                pass
            # cell_index = 0
            # for cell in row:
            #     cell = self.__cell_type_check(cell, cell_index, table_obj)
            #     cell_index += 1
            #     pass
            # excel_date_index = table_obj.attrToSet_list.index(excel_date_flag)
            # row[excel_date_index] = ExcelInfo.__handleExcelDate(row[excel_date_index])
            # for excel_date_flag in table_obj.excel_date_rows:
            #     excel_date_index = table_obj.attrToSet_list.index(excel_date_flag)
            #     row[excel_date_index] = ExcelInfo.__handleExcelDate(row[excel_date_index])
            #     pass
            result.append(row)
        table_obj.value_list = result
        return table_obj
        pass

    def __is_useless_row(self, row: list, table_obj: TableObj):
        """判断row 是否是 useless_row"""
        is_useless_row = False
        for known_useless_row in table_obj.useless_rows:
            # 有一个的..不是list, 两列的是list
            if isinstance(known_useless_row, list):  # 判断两列的
                if row[0] == known_useless_row[0] and row[1] == known_useless_row[1]:
                    is_useless_row = True
                    pass
                pass
            else:  # 只判断一列
                if row[0] == known_useless_row:
                    is_useless_row = True
                pass
            pass
        return is_useless_row
        pass

    def __handleSignOff(self, all_row_list: list, table_obj: TableObj):
        """返回 outer_result, inner_result"""
        inner_start_index = self.__getIndexOfCell(all_row_list, '测评机构\n及检测人员')
        inner_end_index = self.__getIndexOfCell(all_row_list, '校审')
        inner_row_list = all_row_list[inner_start_index: inner_end_index]
        # 转化为标准的, 把左边的裁掉
        for inner_row in inner_row_list:
            assert isinstance(inner_row, list)
            inner_row.pop(0)

        outer_row_list_up = all_row_list[0: inner_start_index]
        outer_row_list_down = all_row_list[inner_end_index:]
        outer_row_list_up.extend(outer_row_list_down)
        outer_row_list = outer_row_list_up

        inner_table_obj = TableObj(ExcelInfo.table_sign_off_inner_ins_psn)
        inner_result_obj = self.__handleMultiColumn(inner_row_list, inner_table_obj)
        inner_result_obj.sheet_name = table_obj.sheet_name

        outer_table_obj = TableObj(ExcelInfo.table_sign_off_outer)
        outer_result_obj = self.__handleTwoColumn(outer_row_list, outer_table_obj)
        outer_result_obj.sheet_name = table_obj.sheet_name

        return (outer_result_obj, inner_result_obj)
        pass

    def __handleSystemInfo(self, all_row_list: list, table_obj: TableObj):
        """特殊处理 系统总体情况表"""
        all_in_one_twoColumn = []  # 最后都存为一个two_column表, 按inner, outer的顺序排
        # 处理内部表
        inner_start_index = self.__getIndexOfCell(all_row_list, '安全域划分')
        inner_end_index = self.__getIndexOfCell(all_row_list, '规划信息点数量(布线点数量)')
        inner_row_list = all_row_list[inner_start_index: inner_end_index]
        # 把内部左边两列裁掉
        for inner_row in inner_row_list:
            assert isinstance(inner_row, list)
            inner_row.pop(0)
            inner_row.pop(0)
            pass
        # 内部表分成3列处理, 每列都是一个two_column...

        rowList_field_num = []  # 机密域个数
        rowList_concrete_content = []  # 具体明细
        rowList_change_inner = []  # 变化情况

        list_of_rowList = [rowList_field_num, rowList_concrete_content, rowList_change_inner]
        THE_INNER_TABLE_NUM = 3
        for inner_row in inner_row_list:
            for i in range(THE_INNER_TABLE_NUM):
                row_with_empty_column_0 = ['', inner_row[i]]
                list_of_rowList[i].append(row_with_empty_column_0)
                pass
            pass
        for rowList in list_of_rowList:
            all_in_one_twoColumn.extend(rowList)  # 都并入一个two_columnlist

        # 处理外部表
        outer_row_list_up = all_row_list[0: inner_start_index]  # outer_table upper part
        outer_row_list_down = all_row_list[inner_end_index:]  # outer_table down part
        outer_row_list_up.extend(outer_row_list_down)
        outer_row_list = outer_row_list_up
        USELESS_ROW_NUM = 2  # 前2行不是内容
        for i in range(USELESS_ROW_NUM):
            outer_row_list.pop(0)
            pass

        for row in outer_row_list:
            # 裁掉第一列, 和第二列(合并单元格的), 和第四列(合并单元格的)
            row.pop(0)
            row.pop(0)
            row.pop(1)
            pass

        # 生成新的two_column的row_list
        rowList_content_outer = []
        rowList_change_outer = []
        list_of_rowList = [rowList_content_outer, rowList_change_outer]
        THE_OUTER_TABLE_NUM = 2
        for outer_row in outer_row_list:
            for i in range(THE_OUTER_TABLE_NUM):
                row_with_empty_column_0 = ['', outer_row[i]]
                list_of_rowList[i].append(row_with_empty_column_0)
                pass
            pass
        for rowList in list_of_rowList:
            all_in_one_twoColumn.extend(rowList)
            pass
        table_obj_all_in_one = TableObj(ExcelInfo.table_system_info_two_column)
        table_obj_all_in_one.sheet_name = table_obj.sheet_name
        table_obj_result = self.__handleTwoColumn(all_in_one_twoColumn, table_obj_all_in_one)
        return table_obj_result
        pass

        pass

    def __getIndexOfCell(self, all_row_list: list, cell_value):
        """根据第一列的值, 返回对应的index, 错误返回-1"""
        the_index = -1

        for row in all_row_list:
            if row[0] == cell_value:
                the_index = all_row_list.index(row)
        return the_index

        pass

    def __get_sheetIdx_with_name(self, sheet_name):
        """
        依据sheet名字得到sheetIndex

        :param sheet_name: ...
        :return: sheet_index: int, 出错则返回-1
        """
        sheet_index = -1
        real_sheet_names = self.excel_helper.getAllSheets()
        for real_sheet_name in real_sheet_names:
            if sheet_name == real_sheet_name:
                sheet_index = real_sheet_names.index(sheet_name)
                pass
            pass
        self.CURRENT_SHEET_INDEX = sheet_index
        return sheet_index
        pass

    def __get_table_row_no(self, table_name):
        """
        得到对应表所在的行数

        :param table_name: ...

        :return: row_no : int, 错误则返回-1
        """
        row_no = self.__get_end_row_no(self.current_row_cursor, table_name)
        # self.excel_helper = ExcelHelper(self.EXCEL_NAME, self.CURRENT_SHEET_INDEX)
        # row_no = self.excel_helper.findTableHeader_row(table_name)
        return row_no
        pass

    def __get_end_row_no(self, the_start_row, end_flag):
        """得到从start_row开始的第一个end_flag出现 的行数, end_row_no 不包含在表格内容中"""
        offset = 0
        end_row = 0
        while offset < 65535:  # 只需一个很大的数...
            try:
                the_first_column_value = self.excel_helper.readOneCell(the_start_row + offset, 0).value
                if the_first_column_value == end_flag:
                    end_row = the_start_row + offset
                    break
                    pass
                offset += 1
                pass
            except IndexError:
                end_row = -1
                break
        return end_row
        pass

    def __get_tableContent_twoColumn(self, header_row, row_list, useless_rows):
        """获得一张表中的数据, 返回的形式是TableInfo对象"""
        result = self.excel_helper.readOneTable_2Column(header_row, row_list, useless_rows)
        return result
        pass

    @staticmethod
    def __handle_type_ExcelDate(cell_value: float):
        """判断cell_value是否格式符合 ExcelDate的要求, 现在是float, 以及不为空,
        返回: 如果不符合: 处理过的date格式, (默认日期是一个古老的日期,) 以及False的标记
             如果符合:  处理过的date格式, 以及True的标记
        """
        if not isinstance(cell_value, float) or cell_value == '':
            null_date = datetime(1900, 1, 1).date()
            return null_date, False  # 没填, 或是格式不一致,也不处理..
        new_date = xlrd.xldate_as_tuple(cell_value, 0)
        new_date_str = str(new_date[0]) + '年' + str(new_date[1]) + '月' + str(new_date[2]) + '日'
        new_date_formatted = datetime.strptime(new_date_str, "%Y年%m月%d日").date()
        return new_date_formatted, True
        pass

    @staticmethod
    def __handle_type_int2str(cell_value):
        """处理要转换为int_to_str类型的单元格, 如电话号码, 现在是出现valueError(转化错误), 以及不为空,
        返回: 如果不符合: 处理过的date格式, (默认日期是一个古老的日期,) 以及False的标记
             如果符合:  处理过的date格式, 以及True的标记
        """

        if cell_value == '':  # cell value is ''
            return cell_value, False
        try:
            result_value = str(int(cell_value))
            # record the rightness of cellType, returns it when reaching the end of method
            is_cellType_right = True
        except ValueError:
            result_value = cell_value  # 转化出错, 就原样返回
            is_cellType_right = False
        return result_value, is_cellType_right
        pass

    @staticmethod
    def __handle_type_score(cell_value):
        """处理分数的类型,
        返回: 如果格式不对, 返回-1, 以及False标记
             如果格式正确, 返回cell_value, 以及True标记
        """
        if cell_value == '' or not isinstance(cell_value, float):
            return -1, False  # 格式不对, 返回分数为-1
        else:
            return cell_value, True
        pass

    def __getAllRowsOfOneTable(self, excel_name, sheet_name, table_obj: TableObj):
        """
        得到一个特定excel表(table_obj对应的)从开头到结尾的所有row_list, 这个是底层的调用...

        :param excel_name: excel名称
        :param sheet_name: sheet名称
        :param table_obj: TableObj 的对象
        :return: table_obj对应的表从开头到结尾的所有的row_list
        """
        # todo 那这个..物理环境要怎么去找它的开头和结尾...
        sheet_index = self.__get_sheetIdx_with_name(sheet_name)
        self.excel_helper = ExcelHelper(excel_name, sheet_index)

        # 得到某张表头一行 行数 ,
        the_start_row = self.__get_table_row_no(table_obj.name)
        # 得到某张表最末行 行数
        the_end_row = self.__get_end_row_no(the_start_row, table_obj.end_flag)
        self.current_row_cursor = the_end_row  # 标记当前sheet到达的行数, 这个变量也许有用

        # 得到某张表中(包括头, 去掉尾)的所有row_list
        all_row_list = self.excel_helper.readOneTableAll(the_start_row, the_end_row)
        return all_row_list
        pass

    def __set_dynamic_table_sheets_dict(self):
        """ExcelInfo类中的tables_in_sheets_dict, 需要动态生成, 其中sheet要动态, sheet中的table_obj也要动态"""
        tbl_in_sht_dct = self.tables_in_sheets_dict

        # sheet 顺序无所谓, 但是其中的table_obj顺序
        pass

    def get_all_table_obj_list(self):
        """
        根据配置, 得到所有的table_obj

        :return: TableObj的list, 其中存有待存储的数据, 以及要存入的相应字段
        """
        # todo now 现在sheet的个数是写死的, sheet只有keys里的那些..这里也需要更改,
        #  需要更改self.tables_in_sheets_dict 为动态生成
        self.__set_dynamic_table_sheets_dict()
        sheets = self.excel_helper.getAllSheets()
        all_table_obj_list = []
        for sheet in sheets:
            self.current_row_cursor = 0  # 更换sheet时, 要把current_row_cursor清为0
            table_obj_list_one_sheet = self.__handle_one_sheet(sheet)
            all_table_obj_list.extend(table_obj_list_one_sheet)
            pass
        return all_table_obj_list
        pass

    def __handle_one_sheet(self, sheet_name):
        """返回一个sheet 中的所有table """
        table_obj_list = []
        tables_in_sheets_dict = self.tables_in_sheets_dict
        tables_in_one_sheet = []
        for one_sheet in tables_in_sheets_dict.keys():
            if sheet_name == one_sheet:
                tables_in_one_sheet = tables_in_sheets_dict[one_sheet]
                pass
            pass

        for table_dict in tables_in_one_sheet:  # table_dict可以转换为table_obj
            # 向dict 中新加 一个 key, sheet_name
            table_dict['sheet_name'] = sheet_name  # 新加入sheet_name 属性
            table_obj = TableObj(table_dict)
            self.__set_fieldObjList_for_tableObj(table_obj)

            result = self.__getOneTableResult(sheet_name, table_obj)
            # self.__handleAllTable(self.EXCEL_NAME, sheet_name, table_obj)
            if isinstance(result, TableObj):
                table_obj_list.append(result)
            elif isinstance(result, tuple):
                table_obj_list.extend(result)
            pass
        return table_obj_list
        pass

    def __set_fieldObjList_for_tableObj(self, table_obj: TableObj):
        """为一个table_obj设定field_obj_list属性, FieldObj类是数据检查类"""
        # 对每个attr_to_set, 设定一个field_obj
        if not table_obj.field_checktype_list:  # 没有设定检查类型
            return
        field_obj_list = []
        attrToSet_list = table_obj.attrToSet_list
        for each_attr in attrToSet_list:
            index = attrToSet_list.index(each_attr)
            one_field_dict = {
                'index_in_table': index,
                'orm_attr_name': each_attr,
                'check_type': table_obj.field_checktype_list[index]
            }
            one_field_obj = FieldObj(one_field_dict)
            field_obj_list.append(one_field_obj)
            pass
        table_obj.set_field_obj_list(field_obj_list)  # 最后把field_obj_list赋值到table_obj中
        pass

    def __getOneTableResult(self, sheet_name, table_obj):
        """自动化地处理完一张表, 返回一个TableObj 对象"""
        all_row_results = self.__getAllRowsOfOneTable(self.EXCEL_NAME, sheet_name, table_obj)
        table_obj.sheet_name = sheet_name
        obj_results = self.__extractResultFromAllRowList(all_row_results, table_obj)
        return obj_results
        pass

    def unit_test_get_one_table_result(self, sheet_name, table_dict_name):
        """测试 同名方法"""
        table_obj = TableObj(table_dict_name)
        self.__set_fieldObjList_for_tableObj(table_obj)
        result = self.__getOneTableResult(sheet_name, table_obj)
        return result

    pass
