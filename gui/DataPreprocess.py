import wx
import wx.grid as gridlib
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
import threading


class DataPreprocessingPage(wx.Panel):
    def __init__(self, parent):
        super(DataPreprocessingPage, self).__init__(parent)
        self.data = None
        self.grid = None  # 延迟创建网格
        self.InitUI()

    def InitUI(self):
        # 使用垂直布局管理器
        self.vbox = wx.BoxSizer(wx.VERTICAL)

        # 标题
        title = wx.StaticText(self, label="数据预处理", style=wx.ALIGN_CENTER)
        title.SetFont(wx.Font(18, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.vbox.Add(title, 0, wx.ALL | wx.EXPAND, 10)

        # 水平布局中的按钮
        hbox_buttons = wx.BoxSizer(wx.HORIZONTAL)

        # 打开文件按钮
        btn_open = wx.Button(self, label="打开 Excel 文件")
        btn_open.Bind(wx.EVT_BUTTON, self.OnOpenFile)
        hbox_buttons.Add(btn_open, 0, wx.ALL, 5)

        # 数据处理按钮
        btn_delete = wx.Button(self, label="删除列")
        btn_normalize = wx.Button(self, label="归一化")
        btn_encode = wx.Button(self, label="独热编码")
        btn_clean = wx.Button(self, label="去除脏数据")
        btn_delete.Bind(wx.EVT_BUTTON, self.OnDeleteColumn)
        btn_normalize.Bind(wx.EVT_BUTTON, self.OnNormalize)
        btn_encode.Bind(wx.EVT_BUTTON, self.OnOneHotEncode)
        btn_clean.Bind(wx.EVT_BUTTON, self.OnCleanData)
        hbox_buttons.Add(btn_delete, 0, wx.ALL, 5)
        hbox_buttons.Add(btn_normalize, 0, wx.ALL, 5)
        hbox_buttons.Add(btn_encode, 0, wx.ALL, 5)
        hbox_buttons.Add(btn_clean, 0, wx.ALL, 5)

        self.vbox.Add(hbox_buttons, 0, wx.ALIGN_CENTER)

        # 输入框：用于指定要删除的行或列
        hbox_input = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, label="删除行/列（例如：1,2 或 A,B）：")
        self.input_delete = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        hbox_input.Add(label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        hbox_input.Add(self.input_delete, 1, wx.ALL | wx.EXPAND, 5)
        self.vbox.Add(hbox_input, 0, wx.EXPAND | wx.ALL, 5)

        # 创建一个占位符，稍后会在数据加载后替换为实际的网格
        self.placeholder = wx.StaticText(self, label="请先选择一个 Excel 文件...")
        self.vbox.Add(self.placeholder, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(self.vbox)

    def OnOpenFile(self, event):
        """打开 Excel 文件并加载数据"""
        with wx.FileDialog(self, "打开 Excel 文件", wildcard="Excel 文件 (*.xlsx)|*.xlsx",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            self.ShowProgressDialog("正在加载数据...", self.LoadData, pathname)

    def LoadData(self, pathname):
        """加载数据并更新表格"""
        try:
            self.data = pd.read_excel(pathname)
            wx.CallAfter(self.UpdateGrid)
        except Exception as e:
            wx.MessageBox(f"读取文件失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def UpdateGrid(self):
        """更新表格内容"""
        if self.data is None or self.data.empty:
            return

        # 如果还没有创建网格，则创建一个新的网格
        if self.grid is None:
            self.grid = gridlib.Grid(self)
            self.grid.CreateGrid(0, 0)
            self.vbox.Replace(self.placeholder, self.grid)
            self.placeholder.Destroy()
            self.placeholder = None
            self.Layout()  # 刷新布局

        # 更新列数并设置表头
        cols = len(self.data.columns)
        current_cols = self.grid.GetNumberCols()
        if current_cols != cols:
            if current_cols > 0:
                self.grid.DeleteCols(0, current_cols)
            self.grid.AppendCols(cols)
        for col, header in enumerate(self.data.columns):
            self.grid.SetColLabelValue(col, str(header))

        # 更新行数并填充数据
        rows = len(self.data)
        current_rows = self.grid.GetNumberRows()
        if current_rows < rows:
            self.grid.AppendRows(rows - current_rows)
        elif current_rows > rows:
            self.grid.DeleteRows(rows, current_rows - rows)

        for row_idx, (_, values) in enumerate(self.data.iterrows()):
            for col_idx, value in enumerate(values):
                self.grid.SetCellValue(row_idx, col_idx, str(value))

        self.Layout()  # 刷新布局

    def OnDeleteColumn(self, event):
        """删除指定的行或列"""
        if self.data is None:
            return

        # 获取输入框内容
        input_value = self.input_delete.GetValue().strip()
        if not input_value:
            wx.MessageBox("请输入要删除的行或列！", "提示", wx.OK | wx.ICON_INFORMATION)
            return

        try:
            # 判断输入是行还是列
            if input_value[0].isdigit():  # 删除行
                rows_to_delete = [int(x) - 1 for x in input_value.split(",")]  # 转换为0-based索引
                self.data.drop(rows_to_delete, axis=0, inplace=True)
            else:  # 删除列
                cols_to_delete = [x.strip() for x in input_value.split(",")]
                self.data.drop(cols_to_delete, axis=1, inplace=True)
            self.UpdateGrid()
        except Exception as e:
            wx.MessageBox(f"删除失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def OnNormalize(self, event):
        """归一化数据"""
        if self.data is None:
            return
        scaler = MinMaxScaler()
        self.data = pd.DataFrame(scaler.fit_transform(self.data), columns=self.data.columns)
        self.UpdateGrid()

    def OnOneHotEncode(self, event):
        """独热编码"""
        if self.data is None:
            return
        encoder = OneHotEncoder()
        encoded_data = encoder.fit_transform(self.data.select_dtypes(include=['object']))
        self.data = pd.concat([self.data.select_dtypes(exclude=['object']),
                               pd.DataFrame(encoded_data.toarray())], axis=1)
        self.UpdateGrid()

    def OnCleanData(self, event):
        """去除脏数据"""
        if self.data is None:
            return

        try:
            # 删除包含空值的行
            self.data.dropna(inplace=True)

            # 将数据转换为数值格式（除第一行外）
            for col in self.data.columns:
                try:
                    # 尝试将列转换为数值类型
                    self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
                except Exception as e:
                    wx.MessageBox(f"列 '{col}' 转换失败: {str(e)}", "警告", wx.OK | wx.ICON_WARNING)

            # 删除无法转换为数值的行
            self.data.dropna(inplace=True)

            self.UpdateGrid()
        except Exception as e:
            wx.MessageBox(f"去除脏数据失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def ShowProgressDialog(self, message, task, *args):
        """显示进度弹窗"""
        progress_dialog = wx.ProgressDialog("请稍候", message, maximum=100, parent=self,
                                            style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE)

        def RunTask():
            task(*args)
            wx.CallAfter(progress_dialog.Destroy)

        threading.Thread(target=RunTask).start()


if __name__ == '__main__':
    app = wx.App(False)
    frame = wx.Frame(None, title="数据预处理示例", size=(800, 600))
    notebook = wx.Notebook(frame)
    data_preprocessing_page = DataPreprocessingPage(notebook)
    notebook.AddPage(data_preprocessing_page, "数据预处理")
    frame.Show(True)
    app.MainLoop()