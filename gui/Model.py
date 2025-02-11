import wx
import wx.grid as gridlib
import pandas as pd
import numpy as np
from sklearn.metrics import (
    roc_curve,
    auc,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    accuracy_score,
)
import matplotlib.pyplot as plt
from sklearn.base import BaseEstimator
import threading
import joblib  # 添加此行确保导入joblib

class DummyModel(BaseEstimator):
    """模拟一个机器学习模型"""

    def predict(self, X):
        return np.random.randint(0, 2, size=len(X))  # 随机预测

    def predict_proba(self, X):
        return np.random.rand(len(X), 2)  # 随机概率


class ModelEvaluationPage(wx.Panel):
    def __init__(self, parent):
        super(ModelEvaluationPage, self).__init__(parent)
        self.model = None
        self.test_data = None
        self.InitUI()

    def InitUI(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(self, label="模型评估", style=wx.ALIGN_CENTER)
        title.SetFont(wx.Font(18, wx.FONTFAMILY_SWISS, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        vbox.Add(title, 0, wx.ALL | wx.EXPAND, 10)

        hbox_buttons = wx.BoxSizer(wx.HORIZONTAL)

        btn_load_model = wx.Button(self, label="加载模型")
        btn_load_model.Bind(wx.EVT_BUTTON, self.OnLoadModel)
        hbox_buttons.Add(btn_load_model, 0, wx.ALL, 5)

        btn_load_test_data = wx.Button(self, label="加载测试数据")
        btn_load_test_data.Bind(wx.EVT_BUTTON, self.OnLoadTestData)
        hbox_buttons.Add(btn_load_test_data, 0, wx.ALL, 5)

        btn_evaluate = wx.Button(self, label="评估模型")
        btn_evaluate.Bind(wx.EVT_BUTTON, self.OnEvaluateModel)
        hbox_buttons.Add(btn_evaluate, 0, wx.ALL, 5)

        vbox.Add(hbox_buttons, 0, wx.ALIGN_CENTER)

        self.text_output = wx.TextCtrl(self, style=wx.TE_MULTILINE | wx.TE_READONLY)
        vbox.Add(self.text_output, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(vbox)

    def OnLoadModel(self, event):
        """通过文件对话框加载模型"""
        with wx.FileDialog(self, "打开模型文件", wildcard="Pickle 文件 (*.pkl)|*.pkl",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            try:
                self.model = joblib.load(pathname)
                self.text_output.AppendText(f"模型 {pathname} 加载成功！\n")
            except Exception as e:
                wx.MessageBox(f"加载模型失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def OnLoadTestData(self, event):
        """加载测试数据"""
        with wx.FileDialog(self, "打开测试数据文件", wildcard="CSV 文件 (*.csv)|*.csv|Excel 文件 (*.xlsx)|*.xlsx",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return

            pathname = fileDialog.GetPath()
            self.ShowProgressDialog("正在加载测试数据...", self.LoadTestData, pathname)

    def LoadTestData(self, pathname):
        """加载测试数据"""
        try:
            if pathname.endswith(".csv"):
                self.test_data = pd.read_csv(pathname)
            else:
                self.test_data = pd.read_excel(pathname)
            wx.CallAfter(self.text_output.AppendText, f"测试数据加载成功！共 {len(self.test_data)} 条数据。\n")
        except Exception as e:
            wx.MessageBox(f"加载测试数据失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def OnEvaluateModel(self, event):
        """评估模型"""
        if self.model is None:
            wx.MessageBox("请先加载模型！", "错误", wx.OK | wx.ICON_ERROR)
            return
        if self.test_data is None:
            wx.MessageBox("请先加载测试数据！", "错误", wx.OK | wx.ICON_ERROR)
            return

        try:
            X_test = self.test_data.iloc[:, :-1]
            y_true = self.test_data.iloc[:, -1]

            y_pred = self.model.predict(X_test)
            y_pred_proba = self.model.predict_proba(X_test)[:, 1]  # 正类的概率

            accuracy = accuracy_score(y_true, y_pred)
            precision = precision_score(y_true, y_pred)
            recall = recall_score(y_true, y_pred)
            f1 = f1_score(y_true, y_pred)
            conf_matrix = confusion_matrix(y_true, y_pred)
            fpr, tpr, _ = roc_curve(y_true, y_pred_proba)
            roc_auc = auc(fpr, tpr)

            self.text_output.AppendText(f"准确率: {accuracy:.4f}\n")
            self.text_output.AppendText(f"精确率: {precision:.4f}\n")
            self.text_output.AppendText(f"召回率: {recall:.4f}\n")
            self.text_output.AppendText(f"F1 分数: {f1:.4f}\n")
            self.text_output.AppendText(f"混淆矩阵:\n{conf_matrix}\n")
            self.text_output.AppendText(f"ROC 曲线下面积 (AUC): {roc_auc:.4f}\n")

            plt.figure()
            plt.plot(fpr, tpr, label=f'ROC 曲线 (AUC = {roc_auc:.2f})')
            plt.xlabel('假正率')
            plt.ylabel('真正率')
            plt.title('ROC 曲线')
            plt.legend(loc="lower right")
            plt.show()
        except Exception as e:
            wx.MessageBox(f"评估失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)

    def ShowProgressDialog(self, message, task, *args):
        progress_dialog = wx.ProgressDialog("请稍候", message, maximum=100, parent=self,
                                            style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE)

        def RunTask():
            task(*args)
            wx.CallAfter(progress_dialog.Destroy)

        threading.Thread(target=RunTask).start()


if __name__ == '__main__':
    app = wx.App(False)
    frame = wx.Frame(None, title="模型评估示例", size=(800, 600))
    notebook = wx.Notebook(frame)
    model_evaluation_page = ModelEvaluationPage(notebook)
    notebook.AddPage(model_evaluation_page, "模型评估")
    frame.Show(True)
    app.MainLoop()