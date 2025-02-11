import wx
import wx.grid as gridlib
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator
import threading
import joblib  # 使用joblib来加载模型


class DummyModel(BaseEstimator):
    """模拟一个机器学习模型"""

    def predict_proba(self, X):
        return np.random.rand(len(X), 2)  # 随机概率


class TrafficMonitoringPage(wx.Panel):
    def __init__(self, parent):
        super(TrafficMonitoringPage, self).__init__(parent)
        self.model = None
        self.traffic_data = None
        self.InitUI()

    def InitUI(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(self, label="流量监测", style=wx.ALIGN_CENTER)
        title.SetFont(wx.Font(18, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        vbox.Add(title, 0, wx.ALL | wx.EXPAND, 10)

        hbox_buttons = wx.BoxSizer(wx.HORIZONTAL)

        btn_load_model = wx.Button(self, label="加载模型")
        btn_load_model.Bind(wx.EVT_BUTTON, self.OnLoadModel)
        hbox_buttons.Add(btn_load_model, 0, wx.ALL, 5)

        btn_load_traffic_data = wx.Button(self, label="加载流量数据")
        btn_load_traffic_data.Bind(wx.EVT_BUTTON, self.OnLoadTrafficData)
        hbox_buttons.Add(btn_load_traffic_data, 0, wx.ALL, 5)

        btn_analyze = wx.Button(self, label="分析流量")
        btn_analyze.Bind(wx.EVT_BUTTON, self.OnAnalyzeTraffic)
        hbox_buttons.Add(btn_analyze, 0, wx.ALL, 5)

        vbox.Add(hbox_buttons, 0, wx.ALIGN_CENTER)

        # 初始化网格但不添加行和列
        self.grid = gridlib.Grid(self)
        self.grid.CreateGrid(0, 3)  # 创建网格，3列：位置、样本、概率
        self.grid.HideRowLabels()
        self.grid.SetColLabelValue(0, "位置")
        self.grid.SetColLabelValue(1, "样本")
        self.grid.SetColLabelValue(2, "风险概率")
        self.grid.AutoSizeColumns()
        vbox.Add(self.grid, 1, wx.EXPAND | wx.ALL, 5)

        self.stats_output = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        vbox.Add(self.stats_output, 0, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(vbox)

    def OnLoadModel(self, event):
        """通过文件对话框加载模型"""
        with wx.FileDialog(self, "打开模型文件", wildcard="Pickle 文件 (*.pkl)|*.pkl",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            self.ShowProgressDialog("正在加载模型...", self.LoadModel, pathname)

    def LoadModel(self, pathname):
        """加载模型"""
        try:
            self.model = joblib.load(pathname)
            wx.CallAfter(self.stats_output.AppendText, f"模型 {pathname} 加载成功！\n")
        except Exception as e:
            wx.MessageBox(f"加载模型失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def OnLoadTrafficData(self, event):
        """加载流量数据"""
        with wx.FileDialog(self, "打开流量数据文件", wildcard="Excel 文件 (*.xlsx)|*.xlsx",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            self.ShowProgressDialog("正在加载流量数据...", self.LoadTrafficData, pathname)

    def LoadTrafficData(self, pathname):
        """加载流量数据"""
        try:
            self.traffic_data = pd.read_excel(pathname)
            wx.CallAfter(self.stats_output.AppendText, f"流量数据加载成功！共 {len(self.traffic_data)} 条数据。\n")
        except Exception as e:
            wx.MessageBox(f"加载流量数据失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def OnAnalyzeTraffic(self, event):
        """分析流量数据"""
        if self.model is None:
            wx.MessageBox("请先加载模型！", "错误", wx.OK | wx.ICON_ERROR)
            return
        if self.traffic_data is None:
            wx.MessageBox("请先加载流量数据！", "错误", wx.OK | wx.ICON_ERROR)
            return

        try:
            risk_probs = self.model.predict_proba(self.traffic_data)[:, 1]  # 正类的概率

            # 清空网格
            self.grid.ClearGrid()
            if self.grid.GetNumberRows() > 0:
                self.grid.DeleteRows(0, self.grid.GetNumberRows())

            # 显示风险样本
            for idx, (row, prob) in enumerate(zip(self.traffic_data.itertuples(index=False), risk_probs), start=1):
                if prob > 0.5:  # 假设概率大于 0.5 为风险样本
                    self.grid.AppendRows(1)
                    self.grid.SetCellValue(idx - 1, 0, str(idx))  # 位置
                    self.grid.SetCellValue(idx - 1, 1, str(row))  # 样本
                    self.grid.SetCellValue(idx - 1, 2, f"{prob:.4f}")  # 风险概率

            # 自动调整列宽
            self.grid.AutoSizeColumns()

            # 显示统计学数据
            self.stats_output.Clear()
            self.stats_output.AppendText("统计学数据：\n")
            self.stats_output.AppendText(f"总样本数: {len(self.traffic_data)}\n")
            self.stats_output.AppendText(f"风险样本数: {sum(risk_probs > 0.5)}\n")
            self.stats_output.AppendText(f"平均风险概率: {np.mean(risk_probs):.4f}\n")
            self.stats_output.AppendText(f"最大风险概率: {np.max(risk_probs):.4f}\n")
            self.stats_output.AppendText(f"最小风险概率: {np.min(risk_probs):.4f}\n")
        except Exception as e:
            wx.MessageBox(f"分析失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

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
    frame = wx.Frame(None, title="流量监测示例", size=(800, 600))
    notebook = wx.Notebook(frame)
    traffic_monitoring_page = TrafficMonitoringPage(notebook)
    notebook.AddPage(traffic_monitoring_page, "流量监测")
    frame.Show(True)
    app.MainLoop()