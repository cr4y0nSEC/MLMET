import wx
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator


class DummyModel(BaseEstimator):
    def predict(self, X):
        return np.random.randint(0, 2, size=len(X))  # 随机预测


class TrafficMonitoringPage(wx.Panel):
    def __init__(self, parent):
        super(TrafficMonitoringPage, self).__init__(parent)
        self.data = None
        self.InitUI()

    def InitUI(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        # 标题
        title = wx.StaticText(self, label="流量监测", style=wx.ALIGN_CENTER)
        title.SetFont(wx.Font(18, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        vbox.Add(title, 0, wx.ALL | wx.EXPAND, 10)

        # 打开文件按钮
        btn_open = wx.Button(self, label="打开 Excel 文件")
        btn_open.Bind(wx.EVT_BUTTON, self.OnOpenFile)
        vbox.Add(btn_open, 0, wx.ALL | wx.EXPAND, 5)

        # 预测按钮
        btn_predict = wx.Button(self, label="风险预测")
        btn_predict.Bind(wx.EVT_BUTTON, self.OnPredict)
        vbox.Add(btn_predict, 0, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(vbox)

    def OnOpenFile(self, event):
        """打开 Excel 文件"""
        with wx.FileDialog(self, "打开 Excel 文件", wildcard="Excel 文件 (*.xlsx)|*.xlsx",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return
            pathname = fileDialog.GetPath()
            self.data = pd.read_excel(pathname)
            wx.MessageBox("文件加载成功！", "提示", wx.OK | wx.ICON_INFORMATION)

    def OnPredict(self, event):
        """使用模型进行风险预测"""
        if not hasattr(self, 'data'):
            wx.MessageBox("请先加载数据！", "错误", wx.OK | wx.ICON_ERROR)
            return
        if not hasattr(self.Parent, 'model'):
            wx.MessageBox("请先加载模型！", "错误", wx.OK | wx.ICON_ERROR)
            return

        # 使用模型进行预测
        model = self.Parent.model
        predictions = model.predict(self.data)
        wx.MessageBox(f"预测完成！风险预测结果: {predictions}", "提示", wx.OK | wx.ICON_INFORMATION)