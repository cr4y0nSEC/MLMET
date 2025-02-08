import wx
import numpy as np
from sklearn.metrics import roc_curve, auc
import matplotlib.pyplot as plt
from sklearn.base import BaseEstimator


class DummyModel(BaseEstimator):
    def predict(self, X):
        return np.random.randint(0, 2, size=len(X))  # 随机预测


class ModelEvaluationPage(wx.Panel):
    def __init__(self, parent):
        super(ModelEvaluationPage, self).__init__(parent)
        self.InitUI()

    def InitUI(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        # 标题
        title = wx.StaticText(self, label="模型评估", style=wx.ALIGN_CENTER)
        title.SetFont(wx.Font(18, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        vbox.Add(title, 0, wx.ALL | wx.EXPAND, 10)

        # 加载模型按钮
        btn_load_model = wx.Button(self, label="加载模型")
        btn_load_model.Bind(wx.EVT_BUTTON, self.OnLoadModel)
        vbox.Add(btn_load_model, 0, wx.ALL | wx.EXPAND, 5)

        # 评估按钮
        btn_evaluate = wx.Button(self, label="评估模型")
        btn_evaluate.Bind(wx.EVT_BUTTON, self.OnEvaluateModel)
        vbox.Add(btn_evaluate, 0, wx.ALL | wx.EXPAND, 5)

        self.SetSizer(vbox)

    def OnLoadModel(self, event):
        """加载模型"""
        self.model = DummyModel()
        wx.MessageBox("模型加载成功！", "提示", wx.OK | wx.ICON_INFORMATION)

    def OnEvaluateModel(self, event):
        """评估模型并显示 ROC 曲线"""
        if not hasattr(self, 'model'):
            wx.MessageBox("请先加载模型！", "错误", wx.OK | wx.ICON_ERROR)
            return

        # 模拟评估
        y_true = np.random.randint(0, 2, size=100)
        y_pred = np.random.rand(100)
        fpr, tpr, _ = roc_curve(y_true, y_pred)
        roc_auc = auc(fpr, tpr)

        # 绘制 ROC 曲线
        plt.figure()
        plt.plot(fpr, tpr, label=f'ROC 曲线 (AUC = {roc_auc:.2f})')
        plt.xlabel('假正率')
        plt.ylabel('真正率')
        plt.title('ROC 曲线')
        plt.legend(loc="lower right")
        plt.show()