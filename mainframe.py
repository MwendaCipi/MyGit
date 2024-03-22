import wx
import wx.aui as aui
from datetime import datetime
from datetime import date
import wx.dataview as dv
import wx.lib.agw.aui
import mainframe
import appointments

class MainFrame(wx.Frame):
    def __init__(self):
        super(MainFrame, self).__init__(None, title="Clinix HRIO Assistant")
        self.Maximize(True)
        self.SetBackgroundColour('#C5C5C5')
        self.panel = wx.Panel(self)

        self.initStatusBar()
        self.statusBar.SetBackgroundColour('#F9F7F7')

        self.notebook = wx.aui.AuiNotebook(self.panel)
       
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.statusBar, 0, wx.ALL|wx.EXPAND, 5)
        self.sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        self.panel.SetSizer(self.sizer)

          # Add the Home tab, now passing 'self' as the main_frame reference
        self.home_tab = appointments.BookAppointments(self.notebook, self)  # 'self' is the MainFrame instance
        self.notebook.AddPage(self.home_tab, "Book Appointments")
        self.notebook.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.on_tab_close)

    def initStatusBar(self):
        self.statusBar = wx.Panel(self.panel)
        self.statusBar.SetMinSize((-1, 25))
        self.statusBar.SetBackgroundColour(wx.WHITE)
        self.statusText = wx.StaticText(self.statusBar, label="")
        self.statusText.SetForegroundColour(wx.GREEN)

        statusBarSizer = wx.BoxSizer(wx.HORIZONTAL)
        statusBarSizer.AddStretchSpacer() #center the text
        statusBarSizer.Add(self.statusText, 0, wx.ALIGN_CENTER)
        statusBarSizer.AddStretchSpacer()  # Center the text

        self.statusBar.SetSizer(statusBarSizer)

    def setStatus(self, message, duration=2000, textColour=wx.GREEN):
        self.statusText.SetLabel(message)
        self.statusText.SetForegroundColour(textColour) # Update text color if needed
        self.statusBar.Layout() # Refresh the layout to reflect the change
        wx.CallLater(duration, self.clearStatus)

    def clearStatus(self):
        self.statusText.SetLabel("")

    def open_or_select_tab(self, tab_name, tab_class=None):
    
        # Iterate through all tabs in the notebook
        for index in range(self.notebook.GetPageCount()):
            # Check if the current tab's title matches the desired tab name
            if self.notebook.GetPageText(index) == tab_name:
                # The tab is found, select it
                self.notebook.SetSelection(index)
                return
            
            # If the tab is not found and a tab class is provided, create a new tab
        if tab_class is not None:
            new_tab = tab_class(self.notebook, self)
            self.notebook.AddPage(new_tab, tab_name)
            self.notebook.SetSelection(self.notebook.GetPageCount() - 1)

    def on_tab_close(self, event):
        # Check if the tab being closed is the Home tab
        if self.notebook.GetPage(event.GetSelection()) == self.home_tab:
            # Veto the event to prevent the tab from closing
            event.Veto()
