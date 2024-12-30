import wx


class MyFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(MyFrame, self).__init__(*args, **kw)

        # 创建一个面板，并且将所有控件添加到这个面板上
        panel = wx.Panel(self)

        # 创建按钮并添加到面板中
        button = wx.Button(panel, label="Click Me")

        # 使用 BoxSizer 管理布局
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(button, 0, wx.ALL | wx.CENTER, 5)  # 将按钮添加到 sizer 中

        panel.SetSizer(sizer)  # 设置面板的 sizer
        self.Centre()  # 居中显示窗口


app = wx.App(False)
frame = MyFrame(None, title="Simple Frame", size=(300, 200))
frame.Show()
app.MainLoop()