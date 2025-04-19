import wx
import wx.grid as gridlib
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder
from sklearn.decomposition import PCA  # 导入 PCA 模块
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

        # 水平布局中的按钮和输入框
        hbox_controls = wx.BoxSizer(wx.HORIZONTAL)

        # 打开文件按钮
        btn_open = wx.Button(self, label="打开流量文件")
        btn_open.Bind(wx.EVT_BUTTON, self.OnOpenFile)
        hbox_controls.Add(btn_open, 0, wx.ALL, 5)

        # 输入框
        label = wx.StaticText(self, label="操作列/行：")
        self.input_indices = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER, size=(100, -1))  # 缩短输入框
        hbox_controls.Add(label, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        hbox_controls.Add(self.input_indices, 0, wx.ALL | wx.EXPAND, 5)

        # 删除按钮
        btn_delete_column = wx.Button(self, label="删除列")
        btn_delete_column.Bind(wx.EVT_BUTTON, self.OnDeleteColumn)
        hbox_controls.Add(btn_delete_column, 0, wx.ALL, 5)

        # 删除行按钮
        btn_delete_row = wx.Button(self, label="删除行")
        btn_delete_row.Bind(wx.EVT_BUTTON, self.OnDeleteRow)
        hbox_controls.Add(btn_delete_row, 0, wx.ALL, 5)

        # 归一化按钮
        btn_normalize = wx.Button(self, label="归一化")
        btn_normalize.Bind(wx.EVT_BUTTON, self.OnNormalize)
        hbox_controls.Add(btn_normalize, 0, wx.ALL, 5)

        # 独热编码按钮
        btn_encode = wx.Button(self, label="独热编码")
        btn_encode.Bind(wx.EVT_BUTTON, self.OnOneHotEncode)
        hbox_controls.Add(btn_encode, 0, wx.ALL, 5)

        # 去除脏数据按钮
        btn_clean = wx.Button(self, label="去除脏数据")
        btn_clean.Bind(wx.EVT_BUTTON, self.OnCleanData)
        hbox_controls.Add(btn_clean, 0, wx.ALL, 5)

        # PCA 降维按钮
        btn_pca = wx.Button(self, label="PCA 降维")
        btn_pca.Bind(wx.EVT_BUTTON, self.OnPCA)
        hbox_controls.Add(btn_pca, 0, wx.ALL, 5)

        # 保存文件按钮
        btn_save = wx.Button(self, label="保存文件")
        btn_save.Bind(wx.EVT_BUTTON, self.OnSaveFile)
        hbox_controls.Add(btn_save, 0, wx.ALL, 5)

        self.vbox.Add(hbox_controls, 0, wx.EXPAND | wx.ALL, 5)

        # 创建一个占位符，稍后会在数据加载后替换为实际的网格
        self.placeholder = wx.StaticText(self, label="打开流量文件后数据将会显示于此")
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

    def GetSelectedIndices(self):
        """从输入框中获取用户选择的行或列索引"""
        input_value = self.input_indices.GetValue().strip()
        if not input_value:
            wx.MessageBox("请输入要操作的行或列索引！", "提示", wx.OK | wx.ICON_INFORMATION)
            return None

        try:
            selected_indices = [int(idx.strip()) for idx in input_value.split(",")]
            return selected_indices
        except ValueError:
            wx.MessageBox("请输入有效的整数索引！", "错误", wx.OK | wx.ICON_ERROR)
            return None

    def OnDeleteColumn(self, event):
        """删除指定的列"""
        if self.data is None:
            return

        selected_columns = self.GetSelectedIndices()
        if not selected_columns:
            return

        try:
            self.data.drop(self.data.columns[selected_columns], axis=1, inplace=True)
            self.UpdateGrid()
        except Exception as e:
            wx.MessageBox(f"删除失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def OnDeleteRow(self, event):
        """删除指定的行"""
        if self.data is None:
            return

        selected_rows = self.GetSelectedIndices()
        if not selected_rows:
            return

        try:
            # 确保索引在有效范围内
            if any(idx < 0 or idx >= len(self.data) for idx in selected_rows):
                wx.MessageBox("输入的行索引超出范围！", "错误", wx.OK | wx.ICON_ERROR)
                return

            self.data.drop(selected_rows, inplace=True)
            self.UpdateGrid()
        except Exception as e:
            wx.MessageBox(f"删除行失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def OnNormalize(self, event):
        """归一化指定的列"""
        if self.data is None:
            return

        selected_columns = self.GetSelectedIndices()
        if not selected_columns:
            return

        try:
            scaler = MinMaxScaler()
            normalized_data = scaler.fit_transform(self.data.iloc[:, selected_columns])

            # 将归一化后的数据转换为 DataFrame 并设置正确的列名
            normalized_df = pd.DataFrame(normalized_data, columns=self.data.columns[selected_columns])

            # 更新原始数据框中的对应列
            self.data.update(normalized_df)

            # 强制更新网格显示
            self.UpdateGrid()
        except Exception as e:
            wx.MessageBox(f"归一化失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def OnOneHotEncode(self, event):
        """对指定的列进行独热编码"""
        if self.data is None:
            return

        selected_columns = self.GetSelectedIndices()
        if not selected_columns:
            return

        try:
            encoder = OneHotEncoder()
            encoded_data = encoder.fit_transform(self.data.iloc[:, selected_columns])
            encoded_df = pd.DataFrame(encoded_data.toarray(), columns=encoder.get_feature_names_out())
            self.data = pd.concat([self.data.drop(self.data.columns[selected_columns], axis=1), encoded_df], axis=1)
            self.UpdateGrid()
        except Exception as e:
            wx.MessageBox(f"独热编码失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def OnCleanData(self, event):

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

    def OnPCA(self, event):

        if self.data is None:
            wx.MessageBox("没有数据可以处理！", "错误", wx.OK | wx.ICON_ERROR)
            return

        selected_columns = self.GetSelectedIndices()
        if not selected_columns:
            return

        try:
            # 获取用户输入的主成分数量
            num_components = wx.GetNumberFromUser(
                "请输入主成分数量（1 到 {} 之间）：".format(len(selected_columns)),
                "主成分数量", "PCA 降维", value=2, min=1, max=len(selected_columns), parent=self)

            if num_components == -1:  # 用户点击了取消
                return

            # 执行 PCA 降维
            pca = PCA(n_components=num_components)
            pca_result = pca.fit_transform(self.data.iloc[:, selected_columns])

            # 将降维结果转换为 DataFrame
            pca_df = pd.DataFrame(pca_result, columns=[f"PC{i+1}" for i in range(num_components)])

            # 删除原始列并添加 PCA 结果列
            self.data = pd.concat([self.data.drop(self.data.columns[selected_columns], axis=1), pca_df], axis=1)

            # 更新网格显示
            self.UpdateGrid()
        except Exception as e:
            wx.MessageBox(f"PCA 降维失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def OnSaveFile(self, event):

        if self.data is None:
            wx.MessageBox("没有数据可以保存！", "错误", wx.OK | wx.ICON_ERROR)
            return

        with wx.FileDialog(self, "保存 Excel 文件", wildcard="Excel 文件 (*.xlsx)|*.xlsx",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            self.ShowProgressDialog("正在保存数据...", self.SaveData, pathname)

    def SaveData(self, pathname):
        """保存数据到指定路径"""
        try:
            self.data.to_excel(pathname, index=False)
            wx.MessageBox("文件保存成功！", "成功", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"保存文件失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def ShowProgressDialog(self, message, task, *args):

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