import xlrd


class ExcelHelper:
    """需要确定excelName和sheetIndex"""

    def __init__(self, file_name, sheet_index):
        self.book = xlrd.open_workbook(file_name)
        self.sheet = self.book.sheet_by_index(sheet_index)
        pass

    def readOneRow(self, row: int = 0):
        """得到一行的内容"""
        rowContents = self.sheet.row(row)
        return rowContents
        pass

    def readOneColumn(self, column: int = 0):
        """得到一列的内容"""
        columnContents = self.sheet.col(column)
        return columnContents
        pass

    def readOneCell(self, row: int, column: int):
        """
        返回一个单元格的内容

        :param row: cells num
        :param column: column num
        :return: 一个cell
        """
        cell = self.sheet.cell(row, column)
        return cell
        pass

    def readAllRows(self, need_header=False):
        """
        得到row_list, 其中row是一行内容的list

        :param need_header: 是否读取第一行(通常是表头而不是内容)
        :returns: row_list, 默认不包含列头
        """

        sheet = self.sheet
        row_list = []
        for row in range(sheet.nrows):
            if row == 0 and (not need_header):
                continue  # 列头不加入此list
            else:
                row_content = []
                column_num = sheet.ncols
                for column in range(column_num):
                    cell_value = sheet.cell(row, column).value
                    cell_value = str(cell_value).strip()  # 去除左右两侧的空白
                    row_content.append(cell_value)
                row_list.append(row_content)
        return row_list

    def findTableHeader_row(self, cellContent):
        """
        根据cellContent的内容, 返回内容所在的行

        :param cellContent: 单元格的内容
        :return: row_no: int 错误则返回-1
        """
        rows = self.sheet.get_rows()
        find_out_flag = -1  # 记录是否找到对应的行
        row_no = 0
        for row in rows:
            if not row:
                continue
            if row[0].value == cellContent:
                return row_no

            row_no += 1
        return find_out_flag
        pass

    def readOneTableAll(self, the_start_row, the_end_row):
        """得到[the_start_row, the_end_row)之间(包括头, 去掉尾)的所有row_list"""
        sheet = self.sheet
        row_list = []
        for row in range(the_start_row, the_end_row):
            row_content = []
            column_num = sheet.ncols
            for column in range(column_num):
                cell_value = sheet.cell(row, column).value
                cell_value = str(cell_value).strip()  # 去除左右两侧的空白
                row_content.append(cell_value)
            row_list.append(row_content)

        return row_list
        pass

    def readOneTable_2Column(self, header_row, row_list, useless_rows):
        """
        得到一个sheet中的一张表的内容, 处理仅有2列的表

        :param useless_rows: 无用的行内容, 没有对应的值
        :param header_row: 表头的所在行数
        :param row_list: 需要填的项的list
        :return: row_list对应的value_list, 即对应的值的list
        """
        content_start_row = header_row + 1
        content_end_row = header_row + len(row_list) + len(useless_rows)
        result_list = []
        for row in range(content_start_row, content_end_row + 1):
            first_column_value = str(self.sheet.cell(row, 0).value).strip()
            if first_column_value in useless_rows:  # 如果开头就是无用的列, 则跳过这一行
                continue
                pass

            row_content = []
            for column in range(self.sheet.ncols):
                cell_value = self.sheet.cell(row, column).value
                cell_value = str(cell_value).strip()
                if cell_value != '':
                    row_content.append(cell_value)
                pass
            try:
                result_list.append(row_content[1])  # 2列的表, 其第二列是结果
            except IndexError:
                print(row)
            pass
        return result_list
        pass


class SheetHelper:
    """在调用ExcelHelper之前需要知道sheetName"""

    @staticmethod
    def getSheetNames(excelName):
        book = xlrd.open_workbook(excelName)
        sheetList = book.sheet_names()
        return sheetList

    pass


class ExcelInfo:
    # todo 现在换一个新的思路, 保留表格, 记录开始行, 结束标志行, 把所有的row_list读出后, 根据table类型(一行多值, 一行单值)再进行处理
    """记录excel的各种信息, 包括各项字典等"""
    EXCEL_NAME = ''
    CURRENT_SHEET_INDEX = -1  # 当前的sheet_index
    SHEET_END_SYMBOL = '{{结束}}'  # sheet结束标志

    excel_helper = None

    # 各个sheetName的dictionary
    SHEET_NAME_DICT = {
        'quest_info': '测评任务信息',
        'part_1': '第一部分 系统概述',
        'central_node': '中心节点',
        'node_1': '接入节点1',
        'node_n': '接入节点N',
        'part_2': '第二部分 系统检测',
        'part_3': '第三部分 专家评估',
        'part_4': '第四部分 测评结论',
        'appendix': '附件',
    }
    # 测评任务信息中的表

    # =================================================================================================================
    # start of sheet and table dict
    # 封面 表的字典
    table_dict_front_cover = {
        'type': '2Column',
        'useless_rows': [],  # 记录无用的行的标记
        'excel_date_rows': ['日期'],  # 需要额外处理的excel_date格式的日期
        'row_list': ['报告编号', '涉密系统名称', '建设使用单位', '测评机构', '日期'],
        'value_list': [],
        'attrToSet_list': []
    }

    # 报告签批页 表的字典
    table_dict_sign_off = {
        'type': '2Column',
        'useless_rows': ['测评机构\n及检测人员'],
        'excel_date_rows': ['日期'],  # 需要额外处理的excel_date格式的日期
        'row_list': ['系统名称', '建设使用单位', '测评结论', '技术得分', '管理得分', '审核', '审核日期', '批准', '批准日期'],
        'value_list': [],
        'attrToSet_list': []

    }

    # 测评机构及委托方信息 表的字典
    table_dict_institution_client = {
        'type': '2Column',
        'useless_rows': ['测评机构', '委托方'],
        'excel_date_rows': [],  # 需要额外处理的excel_date格式的日期
        'row_list': ['名称', '地址', '邮政编码', '联系人', '电话',  # 测评机构
                     '名称', '地址', '邮政编码', '联系人', '电话'],  # 委托方
        'value_list': [],
        'attrToSet_list': []
    }

    # 任务描述 表的字典
    table_dict_task_desc = {
        'type': '2Column',
        'useless_rows': [],
        'excel_date_rows': ['测评通知下发日期', '现场检测日期', '专家评估会日期', '形成报告日期'],  # 需要额外处理的excel_date格式的日期
        'row_list': ['测评通知下发日期', '现场检测日期', '专家评估会日期', '形成报告日期', '保密行政管理部门',
                     '测评机构', '测评召开地点'],
        'value_list': [],
        'attrToSet_list': []

    }

    TABLE_NAME_DICT_QUEST_INFO = {
        'front_cover': {'table_name': '封面', 'table_dict': table_dict_front_cover},
        'sign_off': {'table_name': '报告签批页', 'table_dict': table_dict_sign_off},
        'institution_client': {'table_name': '测评机构及委托方信息', 'table_dict': table_dict_institution_client},
        'task_desc': {'table_name': '任务描述', 'table_dict': table_dict_task_desc},
    }

    # end of 测评任务信息中的表

    # =========================================================================
    # start of 第二部分 系统概述 的表
    table_dict_last_time = {
        'type': 'multiColumn',
        'name': '上次测评或评估意见整改情况表',  # 同时也是start
        'end_flag': ''  # todo, what is none in excel?
    }

    TABLE_NAME_DICT_PART_1 = {
         'lastTime': table_dict_last_time
    }

    # end of 第二部分 系统概述 的表
    # =========================================================================

    def __init__(self, excel_name):
        self.EXCEL_NAME = excel_name
        pass

    def __get_sheetIdx_with_name(self, sheet_name):
        """
        依据sheet名字得到sheetIndex

        :param sheet_name: ...
        :return: sheet_index: int, 出错则返回-1
        """
        sheet_index = -1
        excel_name = self.EXCEL_NAME
        sheet_names = SheetHelper.getSheetNames(excel_name)
        for existed_name in sheet_names:
            if sheet_name == existed_name:
                sheet_index = sheet_names.index(sheet_name)
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
        self.excel_helper = ExcelHelper(self.EXCEL_NAME, self.CURRENT_SHEET_INDEX)
        row_no = self.excel_helper.findTableHeader_row(table_name)
        return row_no
        pass

    def __get_end_row_no(self, the_start_row, end_flag):
        """得到从start_row开始的第一个end_flag出现 的行数, end_row_no 不包含在表格内容中"""
        offset = 1
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
    def __handleExcelDate(excel_date: float):
        """将excel_date (一个float) 转化为 xx年xx月xx日 的字符串"""
        if not isinstance(excel_date, float):
            excel_date = float(excel_date)
        new_date = xlrd.xldate_as_tuple(excel_date, 0)
        new_date_str = str(new_date[0]) + '年' + str(new_date[1]) + '月' + str(new_date[2]) + '日'
        return new_date_str
        pass

    @staticmethod
    def handleTable_2Column(excel_name, sheet_dict_name, table_dict_name):
        """处理只有2列的表格的一般步骤"""
        excel_info = ExcelInfo(excel_name)
        the_index = excel_info.__get_sheetIdx_with_name(ExcelInfo.SHEET_NAME_DICT[sheet_dict_name])

        the_table_dict = ExcelInfo.TABLE_NAME_DICT_QUEST_INFO[table_dict_name]['table_dict']
        the_table_name = ExcelInfo.TABLE_NAME_DICT_QUEST_INFO[table_dict_name]['table_name']
        the_header_row = excel_info.__get_table_row_no(the_table_name)

        the_row_list = the_table_dict['row_list']
        useless_rows = the_table_dict['useless_rows']
        result_list = excel_info.__get_tableContent_twoColumn(the_header_row, the_row_list, useless_rows)

        excel_date_values = the_table_dict['excel_date_rows']
        for date_value in excel_date_values:
            excel_date_index = ExcelInfo.TABLE_NAME_DICT_QUEST_INFO[table_dict_name]['table_dict']['row_list'].index(date_value)
            result_list[excel_date_index] = ExcelInfo.__handleExcelDate(result_list[excel_date_index])

        return result_list
        pass

    def handleAllTable(self, excel_name, sheet_name, table_dict_name):
        """得到从开头到结尾的所有row_list"""
        the_sheet_index = self.__get_sheetIdx_with_name(sheet_name)
        self.excel_helper = ExcelHelper(excel_name, the_sheet_index)
        the_sheet_dict = ExcelInfo.TABLE_NAME_DICT_PART_1[table_dict_name]
        table_name = the_sheet_dict['name']

        # 得到头一行 行数
        the_start_row = self.__get_table_row_no(table_name)
        # 得到最末行 行数
        the_end_row = self.__get_end_row_no(the_start_row, the_sheet_dict['end_flag'])

        # 得到其中(包括头, 去掉尾)的所有row_list
        all_row_list = self.excel_helper.readOneTableAll(the_start_row, the_end_row)

        pass

    pass


if __name__ == '__main__':
    pass
    # 已测试: sheet_测评任务信息: front_cover, task_desc, institution_client,
    the_excel_name = r'C:\Users\xuyb\Desktop\excel\标注_内容版-检测评估报告导入模板2.xls'
    the_sheet_name = '第一部分 系统概述'
    the_tableDict_name = 'lastTime'
    # result_list = ExcelInfo.handleTable_2Column(the_excel_name, the_sheet_name, the_tableDict_name)
    info = ExcelInfo(the_excel_name)
    info.handleAllTable(the_excel_name, the_sheet_name, the_tableDict_name)
    pass
