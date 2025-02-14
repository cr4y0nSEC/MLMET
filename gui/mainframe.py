import wx
from DataPreprocess import DataPreprocessingPage
from TrafficMonitor import TrafficMonitoringPage


class MainFrame(wx.Frame):
    def __init__(self):
        super(MainFrame, self).__init__(None, title="工业互联网流量检测系统", size=(1000, 700))
        self.InitUI()

    def InitUI(self):
        # 设置窗口图标
        self.SetIcon(wx.Icon("icon.png", wx.BITMAP_TYPE_PNG))

        # 创建笔记本（多页面）
        notebook = wx.Notebook(self)

        # 添加页面
        page1 = DataPreprocessingPage(notebook)
        page3 = TrafficMonitoringPage(notebook)
        notebook.AddPage(page1, "数据预处理")
        notebook.AddPage(page3, "流量监测")

        # 设置窗口居中并显示
        self.Centre()
        self.Show()


if __name__ == '__main__':
    app = wx.App(False)
    frame = MainFrame()
    app.MainLoop()