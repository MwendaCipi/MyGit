import wx
import wx.aui as aui
import wx.adv  # For wx.DatePickerCtrl
import wx.lib.mixins.listctrl  # For CheckListCtrlMixin, if needed
import sqlite3
from datetime import datetime
from datetime import date
import wx.dataview as dv
import wx.lib.agw.aui
import mainframe
      
class LoginDialog(wx.Dialog):
    def __init__(self, parent):
        super(LoginDialog, self).__init__(parent, title="Clinix Login", size=(400, 400))
        sizer = wx.BoxSizer(wx.VERTICAL)

        font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
    
        #self.SetForegroundColour('#6g7b5g')
        
        # Username and Password Fields
        username_label = wx.StaticText(self, label="Username:")
        username_label.SetFont(font)  # Set the font for the label
        sizer.Add(username_label, 0, wx.ALL, 10)
        
        self.username = wx.TextCtrl(self)
        self.username.SetFont(font)  # Set the font for the TextCtrl
        sizer.Add(self.username, 0, wx.ALL | wx.EXPAND, 25)
        
        # Password Label and TextCtrl
        password_label = wx.StaticText(self, label="Password:")
        password_label.SetFont(font)  # Set the font for the label
        sizer.Add(password_label, 0, wx.ALL, 10)
        
        self.password = wx.TextCtrl(self, style=wx.TE_PASSWORD)
        self.password.SetFont(font)  # Set the font for the TextCtrl
        sizer.Add(self.password, 0, wx.ALL | wx.EXPAND, 25)
        
        # Login Button
        login_button = wx.Button(self, label="Login")
        login_button.SetFont(font)
        sizer.Add(login_button, 0, wx.ALL | wx.ALIGN_CENTER, 5)
        login_button.Bind(wx.EVT_BUTTON, self.OnLogin)
        
        self.SetSizer(sizer)
        self.Layout()

    def OnLogin(self, event):
       
        self.EndModal(wx.ID_OK)
        # Otherwise, you can show an error message
        # wx.MessageBox("Login Failed", "Error", wx.OK | wx.ICON_ERROR)

class AppointmentApp(wx.App):
    def OnInit(self):
        login_dialog = LoginDialog(None)
        login_dialog.Center()
        if login_dialog.ShowModal() == wx.ID_OK:
            frame = mainframe.MainFrame()
            frame.Show(True)
            return True
        else:
            return False  # Prevents the app from continuing if login fails
    

if __name__ == "__main__":
    app = AppointmentApp()
    app.MainLoop()

   