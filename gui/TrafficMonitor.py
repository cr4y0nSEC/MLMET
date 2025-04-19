import wx
import wx.grid as gridlib
import pandas as pd
import numpy as np
import matplotlib

matplotlib.use('WXAgg')
import logging

# 抑制字体警告
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)


# 设置中文字体
def setup_chinese_fonts():
    """配置中文字体支持并处理错误"""
    # 尝试多种中文字体
    font_list = ['SimHei', 'Microsoft YaHei', 'SimSun', 'KaiTi', 'FangSong']
    font_found = False

    for font in font_list:
        try:
            from matplotlib.font_manager import FontProperties
            # 尝试找到字体
            FontProperties(family=font)
            matplotlib.rcParams['font.sans-serif'] = [font] + matplotlib.rcParams.get('font.sans-serif', [])
            print(f"成功设置字体: {font}")
            font_found = True
            break
        except Exception as e:
            print(f"字体 {font} 设置失败: {str(e)}")
            continue

    if not font_found:
        # 如果系统中没有合适的中文字体，使用matplotlib默认字体
        print("警告: 未找到合适的中文字体，将使用默认字体")

    # 解决负号显示问题
    matplotlib.rcParams['axes.unicode_minus'] = False


# 设置中文字体
setup_chinese_fonts()

from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import matplotlib.pyplot as plt
import threading
import joblib
import os
from sklearn.base import BaseEstimator
from wx.lib.scrolledpanel import ScrolledPanel


class TrafficMonitoringPage(wx.Panel):
    def __init__(self, parent):
        super(TrafficMonitoringPage, self).__init__(parent)
        self.model = None
        self.feature_names = None  # 存储特征名
        self.traffic_data = None
        self.target_data = None  # 存储目标变量
        self.InitUI()

    def InitUI(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # 添加顶部控制面板
        ctrl_panel = wx.Panel(self)
        ctrl_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 模型加载按钮
        self.load_model_btn = wx.Button(ctrl_panel, label="加载模型")
        self.load_model_btn.Bind(wx.EVT_BUTTON, self.OnLoadModel)
        ctrl_sizer.Add(self.load_model_btn, 0, wx.ALL | wx.EXPAND, 5)

        # 数据加载按钮
        self.load_data_btn = wx.Button(ctrl_panel, label="加载数据")
        self.load_data_btn.Bind(wx.EVT_BUTTON, self.OnLoadData)
        ctrl_sizer.Add(self.load_data_btn, 0, wx.ALL | wx.EXPAND, 5)

        # 分析按钮
        self.analyze_btn = wx.Button(ctrl_panel, label="开始分析")
        self.analyze_btn.Bind(wx.EVT_BUTTON, self.OnAnalyzeTraffic)
        ctrl_sizer.Add(self.analyze_btn, 0, wx.ALL | wx.EXPAND, 5)

        ctrl_panel.SetSizer(ctrl_sizer)
        main_sizer.Add(ctrl_panel, 0, wx.EXPAND)

        # 创建拆分器，上方用于展示网格数据，下方用于展示统计信息和图表
        self.splitter = wx.SplitterWindow(self, style=wx.SP_3D | wx.SP_LIVE_UPDATE)

        # 上半部分 - 网格数据
        self.grid = gridlib.Grid(self.splitter)
        self.grid.CreateGrid(0, 4)
        self.grid.SetColLabelValue(0, "ID")
        self.grid.SetColLabelValue(1, "关键特征示例")
        self.grid.SetColLabelValue(2, "预测概率")
        self.grid.SetColLabelValue(3, "判定结果")
        self.grid.SetRowLabelSize(30)
        self.grid.AutoSizeColumns()

        # 下半部分 - 创建可滚动面板
        self.bottom_panel = ScrolledPanel(self.splitter)
        bottom_sizer = wx.BoxSizer(wx.VERTICAL)

        # 统计信息文本框
        self.stats_output = wx.TextCtrl(self.bottom_panel, size=(100, 150),
                                        style=wx.TE_MULTILINE | wx.TE_READONLY)
        bottom_sizer.Add(self.stats_output, 0, wx.EXPAND | wx.ALL, 5)

        # 创建图表区域
        self.viz_panel = wx.Panel(self.bottom_panel)
        self.viz_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 添加图表容器
        self.figure1 = Figure(figsize=(5, 4), dpi=100)
        self.canvas1 = FigureCanvas(self.viz_panel, -1, self.figure1)
        self.viz_sizer.Add(self.canvas1, 1, wx.EXPAND | wx.ALL, 5)

        self.figure2 = Figure(figsize=(5, 4), dpi=100)
        self.canvas2 = FigureCanvas(self.viz_panel, -1, self.figure2)
        self.viz_sizer.Add(self.canvas2, 1, wx.EXPAND | wx.ALL, 5)

        self.viz_panel.SetSizer(self.viz_sizer)
        bottom_sizer.Add(self.viz_panel, 1, wx.EXPAND)

        self.bottom_panel.SetSizer(bottom_sizer)
        self.bottom_panel.SetupScrolling()

        # 配置拆分器
        self.splitter.SplitHorizontally(self.grid, self.bottom_panel)
        self.splitter.SetSashPosition(300)
        main_sizer.Add(self.splitter, 1, wx.EXPAND)

        self.SetSizer(main_sizer)

    def OnLoadModel(self, event):
        """手动加载模型"""
        dlg = wx.FileDialog(
            self, message="选择模型文件",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard="Joblib files (*.joblib)|*.joblib",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        )

        if dlg.ShowModal() == wx.ID_OK:
            pathname = dlg.GetPath()
            try:
                saved_data = joblib.load(pathname)
                self.model = saved_data['model']
                self.feature_names = saved_data['feature_names']  # 加载特征名
                wx.CallAfter(self.stats_output.AppendText,
                             f"模型加载成功！\n特征数: {len(self.feature_names)}\n")
            except Exception as e:
                wx.MessageBox(f"加载模型失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
        dlg.Destroy()

    def OnLoadData(self, event):
        """手动加载数据"""
        dlg = wx.FileDialog(
            self, message="选择数据文件",
            defaultDir=os.getcwd(),
            defaultFile="",
            wildcard="Excel files (*.xlsx)|*.xlsx|CSV files (*.csv)|*.csv",
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST
        )

        if dlg.ShowModal() == wx.ID_OK:
            pathname = dlg.GetPath()
            try:
                if pathname.endswith('.csv'):
                    df = pd.read_csv(pathname)
                else:
                    df = pd.read_excel(pathname)

                # 验证必要列是否存在
                if 'Class' not in df.columns:
                    raise ValueError("数据必须包含'Class'列")

                # 分离特征和目标
                self.target_data = df['Class']
                self.traffic_data = df.drop('Class', axis=1)

                # 检查特征是否匹配
                if hasattr(self, 'feature_names') and self.feature_names:
                    missing = set(self.feature_names) - set(df.columns)
                    if missing:
                        wx.CallAfter(self.stats_output.AppendText,
                                     f"警告：缺少特征 {missing}\n")

                wx.CallAfter(self.stats_output.AppendText,
                             f"数据加载成功！\n样本数: {len(df)}\n正样本: {sum(df['Class'] == 1)}\n负样本: {sum(df['Class'] == 0)}\n")
            except Exception as e:
                wx.MessageBox(f"加载数据失败: {str(e)}", "错误", wx.OK | wx.ICON_ERROR)
        dlg.Destroy()

    def OnAnalyzeTraffic(self, event):
        """执行分析并可视化"""
        if not all([self.model, self.traffic_data is not None]):
            wx.MessageBox("请先加载模型和数据！", "错误", wx.OK | wx.ICON_ERROR)
            return

        try:
            # 特征顺序对齐
            if hasattr(self, 'feature_names') and self.feature_names:
                # 确保所有特征都存在
                missing_features = [f for f in self.feature_names if f not in self.traffic_data.columns]
                if missing_features:
                    wx.MessageBox(f"数据中缺少以下特征: {', '.join(missing_features)}", "错误", wx.OK | wx.ICON_ERROR)
                    return
                X = self.traffic_data[self.feature_names]
            else:
                X = self.traffic_data

            # 获取预测概率
            risk_probs = self.model.predict_proba(X)[:, 1]
            predictions = (risk_probs > 0.5).astype(int)

            # 清空并初始化网格
            self.grid.ClearGrid()
            if self.grid.GetNumberRows() > 0:
                self.grid.DeleteRows(0, self.grid.GetNumberRows())
            if self.grid.GetNumberCols() != 4:
                self.grid.DeleteCols(0, self.grid.GetNumberCols())
                self.grid.AppendCols(4)
                self.grid.SetColLabelValue(0, "ID")
                self.grid.SetColLabelValue(1, "关键特征示例")
                self.grid.SetColLabelValue(2, "预测概率")
                self.grid.SetColLabelValue(3, "判定结果")

            # 填充数据（显示高风险样本）
            high_risk_count = 0
            for idx, prob in enumerate(risk_probs, start=1):
                if prob > 0.5:  # 高风险样本
                    self.grid.AppendRows(1)
                    row_pos = self.grid.GetNumberRows() - 1
                    self.grid.SetCellValue(row_pos, 0, str(idx))

                    # 显示前3个重要特征的值
                    top_features = ", ".join([f"{X.columns[i]}={X.iloc[idx - 1, i]:.2f}"
                                              for i in range(min(3, X.shape[1]))])
                    self.grid.SetCellValue(row_pos, 1, top_features)

                    self.grid.SetCellValue(row_pos, 2, f"{prob:.4f}")
                    self.grid.SetCellValue(row_pos, 3, "高风险" if prob > 0.7 else "警告")
                    high_risk_count += 1

            # 统计信息输出
            self.stats_output.Clear()
            self.stats_output.AppendText("=== 分析结果 ===\n")
            self.stats_output.AppendText(f"总样本数: {len(X)}\n")
            self.stats_output.AppendText(f"高风险样本(>0.7): {sum(risk_probs > 0.7)}\n")
            self.stats_output.AppendText(f"警告样本(0.5-0.7): {sum((risk_probs > 0.5) & (risk_probs <= 0.7))}\n")
            self.stats_output.AppendText(f"安全样本: {sum(risk_probs <= 0.5)}\n")

            if high_risk_count == 0:
                self.stats_output.AppendText("\n未发现高风险样本\n")

            # 高风险样本特征统计
            if sum(risk_probs > 0.7) > 0:
                high_risk_data = X[risk_probs > 0.7]
                self.stats_output.AppendText("\n高风险样本特征均值:\n")
                for feat in X.columns[:5]:  # 显示前5个特征
                    self.stats_output.AppendText(f"{feat}: {high_risk_data[feat].mean():.2f}\n")

            # 绘制可视化图表
            self.visualize_results(risk_probs, predictions)

            # 调整网格列宽
            self.grid.AutoSizeColumns()

        except Exception as e:
            import traceback
            err_msg = traceback.format_exc()
            wx.MessageBox(f"分析出错: {str(e)}\n\n详细信息:\n{err_msg}", "错误", wx.OK | wx.ICON_ERROR)

    def visualize_results(self, risk_probs, predictions):
        """生成可视化结果"""
        try:
            # 清除旧图表
            self.figure1.clear()
            self.figure2.clear()

            # 使用FontProperties确保中文显示
            from matplotlib.font_manager import FontProperties
            # 尝试使用可用的中文字体
            try:
                font_props = FontProperties(family='SimHei')
            except:
                try:
                    font_props = FontProperties(family='Microsoft YaHei')
                except:
                    # 如果无法找到中文字体，使用默认字体
                    font_props = FontProperties()

            # 图表1：风险概率分布直方图
            ax1 = self.figure1.add_subplot(111)
            ax1.hist(risk_probs, bins=20, alpha=0.75, color='skyblue', edgecolor='black')
            ax1.axvline(x=0.5, color='red', linestyle='--', linewidth=2, label='预警阈值')
            ax1.axvline(x=0.7, color='darkred', linestyle='--', linewidth=2, label='高风险阈值')
            ax1.set_title('风险概率分布', fontproperties=font_props)
            ax1.set_xlabel('风险概率', fontproperties=font_props)
            ax1.set_ylabel('样本数量', fontproperties=font_props)
            ax1.legend(prop=font_props)
            ax1.grid(True, linestyle='--', alpha=0.7)

            # 图表2：各风险级别饼图
            ax2 = self.figure2.add_subplot(111)
            risk_levels = [
                sum(risk_probs > 0.7),  # 高风险
                sum((risk_probs > 0.5) & (risk_probs <= 0.7)),  # 警告
                sum(risk_probs <= 0.5)  # 安全
            ]
            labels = ['高风险 (>0.7)', '警告 (0.5-0.7)', '安全 (≤0.5)']
            colors = ['#ff6b6b', '#feca57', '#1dd1a1']

            # 确保有数据才绘制饼图
            if sum(risk_levels) > 0:
                wedges, texts, autotexts = ax2.pie(
                    risk_levels,
                    labels=labels,
                    autopct='%1.1f%%',
                    startangle=90,
                    colors=colors
                )

                # 设置饼图文本的字体
                for text in texts:
                    text.set_fontproperties(font_props)
                for autotext in autotexts:
                    autotext.set_fontproperties(font_props)
            else:
                ax2.text(0.5, 0.5, '没有可用数据',
                         horizontalalignment='center',
                         verticalalignment='center',
                         fontproperties=font_props,
                         transform=ax2.transAxes)

            ax2.set_title('风险级别分布', fontproperties=font_props)
            ax2.axis('equal')  # 确保饼图是圆形

            # 更新画布
            self.canvas1.draw()
            self.canvas2.draw()

        except Exception as e:
            import traceback
            print(f"可视化错误: {str(e)}")
            print(traceback.format_exc())
            # 在图表上显示错误信息
            for fig in [self.figure1, self.figure2]:
                fig.clear()
                ax = fig.add_subplot(111)
                ax.text(0.5, 0.5, f'绘图错误: {str(e)}',
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=ax.transAxes)
                ax.axis('off')
            self.canvas1.draw()
            self.canvas2.draw()


if __name__ == '__main__':
    app = wx.App(False)
    frame = wx.Frame(None, title="网络流量风险分析系统", size=(1200, 900))

    # 设置图标（可选）
    if os.path.exists("icon.ico"):
        frame.SetIcon(wx.Icon("icon.ico"))

    notebook = wx.Notebook(frame)
    page = TrafficMonitoringPage(notebook)
    notebook.AddPage(page, "实时监测")
    frame.Show()
    app.MainLoop()