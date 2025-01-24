import wx
import pandas as pd
import wx.grid as gridlib


class MyFrame(wx.Frame):
    def __init__(self, *args, **kw):
        super(MyFrame, self).__init__(*args, **kw)

        # 创建面板
        pnl = wx.Panel(self)

        # 创建菜单栏
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        openItem = fileMenu.Append(wx.ID_OPEN, '&Open\tCtrl+O', 'Open a new document')
        menubar.Append(fileMenu, '&File')
        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.OnOpenFile, openItem)

        # 创建用于显示数据的Grid
        self.grid = gridlib.Grid(pnl)
        self.grid.CreateGrid(0, 0)  # 初始时没有行和列

        # 绑定鼠标滚轮事件以实现滚动加载更多数据
        self.grid.Bind(wx.EVT_MOUSEWHEEL, self.OnMouseWheel)

        # 布局管理器
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.grid, 1, wx.EXPAND | wx.ALL, 5)
        pnl.SetSizer(sizer)

        # 设置窗口大小和标题
        self.SetSize((800, 600))
        self.SetTitle('Excel Viewer')

        # 数据存储变量
        self.data = None
        self.display_rows = 100  # 每次显示的行数
        self.current_row = 0  # 当前行索引

    def OnOpenFile(self, event):
        with wx.FileDialog(self, "Open Excel file", wildcard="Excel files (*.xlsx)|*.xlsx",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:

            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # 用户取消选择

            pathname = fileDialog.GetPath()
            try:
                # 完全读取Excel文件中的所有数据
                self.data = pd.read_excel(pathname)

                # 初始化显示前100行数据
                self.UpdateGrid()
            except Exception as e:
                wx.LogError(f"Failed to read file: {e}")

    def UpdateGrid(self):
        if self.data is None or self.data.empty:
            return  # 如果没有数据或者数据为空，则不更新表格

        # 更新列数并设置表头
        cols = len(self.data.columns)
        current_cols = self.grid.GetNumberCols()

        # 如果现有列数与新数据列数不同，则重新设置列数
        if current_cols != cols:
            self.grid.DeleteCols(0, current_cols) if current_cols > 0 else None
            self.grid.AppendCols(cols)

        for col, header in enumerate(self.data.columns):
            self.grid.SetColLabelValue(col, str(header))

        # 更新行数并填充数据
        end_row = min(self.current_row + self.display_rows, len(self.data))
        num_rows = end_row - self.current_row
        current_rows = self.grid.GetNumberRows()

        # 如果现有行数少于需要显示的行数，则添加新行
        if current_rows < num_rows:
            self.grid.AppendRows(num_rows - current_rows)

        # 如果现有行数多于需要显示的行数，则删除多余行
        elif current_rows > num_rows:
            self.grid.DeleteRows(num_rows, current_rows - num_rows)

        # 批量设置单元格值
        for row_idx, (_, values) in enumerate(self.data.iloc[self.current_row:end_row].iterrows()):
            for col_idx, value in enumerate(values):
                self.grid.SetCellValue(row_idx, col_idx, str(value))

    def OnMouseWheel(self, event):
        # 获取当前可视区域的高度
        client_size = self.grid.GetClientSize()
        scroll_pos = self.grid.GetViewStart()[1]
        scroll_range = self.grid.GetScrollRange(wx.VERTICAL)

        # 检查是否滚动到了接近底部
        if (scroll_pos + client_size[1] >= scroll_range and
                self.current_row + self.display_rows < len(self.data)):
            self.current_row += self.display_rows
            self.UpdateGrid()


if __name__ == '__main__':
    app = wx.App(False)
    frm = MyFrame(None)
    frm.Show()
    app.MainLoop()