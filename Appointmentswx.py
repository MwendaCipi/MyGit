import wx
import wx.aui as aui
import wx.adv  # For wx.DatePickerCtrl
import wx.lib.mixins.listctrl  # For CheckListCtrlMixin, if needed
import sqlite3
from datetime import datetime
from datetime import date
import wx.dataview as dv
      
class LoginDialog(wx.Dialog):
    def __init__(self, parent):
        super(LoginDialog, self).__init__(parent, title="Clinix Login", size=(400, 400))
        sizer = wx.BoxSizer(wx.VERTICAL)

        font = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        
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
            frame = MainFrame()
            frame.Show(True)
            return True
        else:
            return False  # Prevents the app from continuing if login fails
    
class MainFrame(wx.Frame):
    def __init__(self):
        super(MainFrame, self).__init__(None, title="Clinix Clinic Management System")
        self.Maximize(True)
        self.SetBackgroundColour('#F0F0F0')
        self.panel = wx.Panel(self)

        self.initStatusBar()
        self.statusBar.SetBackgroundColour('#2B2B2B)')
        self.notebook = wx.aui.AuiNotebook(self.panel)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.statusBar, 0, wx.ALL|wx.EXPAND, 5)
        self.sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        self.panel.SetSizer(self.sizer)

          # Add the Home tab, now passing 'self' as the main_frame reference
        self.home_tab = BookAppointments(self.notebook, self)  # 'self' is the MainFrame instance
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

    def setStatus(self, message, textColour=wx.GREEN):
        self.statusText.SetLabel(message)
        self.statusText.SetForegroundColour(textColour) # Update text color if needed
        self.statusBar.Layout() # Refresh the layout to reflect the change
        wx.CallLater(2000, self.clearStatus)

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

class AppointmentsModel(dv.PyDataViewModel):
    def __init__(self, data=None):
        super(AppointmentsModel, self).__init__()
        self.data = data or {}  # data is structured as { 'Month Year': { 'DD/MM/YYYY': [appointments] } }
        self.UseWeakRefs(False)

    def setData(self, data):
        self.data = data
        self.Cleared()
    
    def GetColumnCount(self):
        return 10

    def GetColumnType(self, col):
        return "string"
    
    def convert_yyyy_mm_dd_to_dd_mm_yyyy(self, date_str):
        """Converts a date string from 'yyyy-mm-dd' to 'dd/mm/yyyy' format."""
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
        except ValueError:
            # Return the original string if it cannot be converted.
            return date_str

    def convert_dd_mm_yyyy_to_yyyy_mm_dd(self, date_str):
        """Converts a date string from 'dd/mm/yyyy' to 'yyyy-mm-dd' format."""
        try:
            return datetime.strptime(date_str, "%d/%m/%Y").strftime("%Y-%m-%d")
        except ValueError:
            # Return the original string if it cannot be converted.
            return date_str
        
    def IsContainer(self, item):
        if not item:
            return True  # Root item is a container.
        obj = self.ItemToObject(item)
        if isinstance(obj, str):
            # Check if this string is a top-level key (month-year).
            if obj in self.data:
                return True
            # More efficiently check if this string is a second-level key (date).
            return any(obj in dates_dict for dates_dict in self.data.values())
        # Appointment details (dict) are not containers.
        return False

    def GetParent(self, item):
        if not item:
            # Root item has no parent
            return dv.NullDataViewItem
        
        obj = self.ItemToObject(item)
        
        # If the object is a date, find its month-year
        if isinstance(obj, str):
            for month_year, dates_dict in self.data.items():
                if obj in dates_dict:  # obj is a date string here
                    # Find the month-year this date belongs to
                    return self.ObjectToItem(month_year)
            
        # If the object is an appointment, find its date
        elif isinstance(obj, dict):
            date_str = obj['Date']

            date_formatted = self.convert_yyyy_mm_dd_to_dd_mm_yyyy(date_str)

            for month_year, dates_dict in self.data.items():
                # This loop assumes each date can only belong to one month_year
                if date_formatted in dates_dict:
                    # Found the date this appointment belongs to
                    return self.ObjectToItem(date_formatted)

        return dv.NullDataViewItem

    def GetChildren(self, parent, children):
        if not parent:  # Root node
            # Append all month-year as child items
            for month_year in self.data.keys():
                children.append(self.ObjectToItem(month_year))
            return len(self.data)
        
        parent_obj = self.ItemToObject(parent)
        if parent_obj in self.data:  # Month-year node
            # Append all dates within the month-year as child items
            for date_formatted in self.data[parent_obj].keys():
                children.append(self.ObjectToItem(date_formatted))
            return len(self.data[parent_obj])
        
        for month_year in self.data:  # This loop is only necessary if the exact month-year for parent_obj isn't directly known.
            if parent_obj in self.data[month_year]:  # Check if the parent_obj (date) exists in the current month-year
                # Append all appointments for the date as child items
                for appointment in self.data[month_year][parent_obj]:
                    children.append(self.ObjectToItem(appointment))
                return len(self.data[month_year][parent_obj])

        return 0

    def GetValue(self, item, col):
        obj = self.ItemToObject(item)
        
        # Logic for the first column
        if col == 0:
            # Directly return the string for month-year and date nodes
            if isinstance(obj, str):
                return obj

            # For appointment objects, calculate and display the row number within its date
            elif isinstance(obj, dict):
                parent_item = self.GetParent(item)  # This is the date item

            if parent_item.IsOk():
                parent_obj = self.ItemToObject(parent_item)  # This is the date string
                
                # Assuming the parent_obj is correctly identified as the date string,
                # and self.data[month_year][date_string] gives you the list of appointments
                for month_year, dates_dict in self.data.items():
                    if parent_obj in dates_dict:
                        appointments = dates_dict[parent_obj]
                        try:
                            index = appointments.index(obj) + 1  # Calculate index starting from 1
                            return str(index)
                        except ValueError:
                            pass

            return ""  # Default return for any non-handled case or if index calculation fails

        if isinstance(obj, dict):  # Make sure obj is an appointment (dict) before trying to access its details
            if col == 1:
                return str(obj.get('Clinic', ''))
            elif col == 2:
                return str(obj.get('ClinicNumber', ''))
            elif col == 3:
                return str(obj.get('FirstName', ''))
            elif col == 4:
                return str(obj.get('LastName', ''))
            elif col == 5:
                return str(obj.get('PhoneNumber', ''))
            elif col == 6:
                return str(obj.get('Gender', ''))
            elif col == 7:
                return str(obj.get('Date', ''))
            elif col == 8:
                return str(obj.get('Time', ''))
            elif col == 9:
                return str(obj.get('Comments', ''))
            elif col == 10:
                return str(obj.get('Rowid', ''))
            return ""
                
    def HasContainerColumns(self, item):
        return self.IsContainer(item)  
    
    def GetItemData(self, item):
        # Convert the item to the object it represents in the model
        obj = self.ItemToObject(item)
        # Check if the object is an appointment (a dictionary in this context)
        if isinstance(obj, dict):
            # Return the appointment data directly
            return obj
        # If the item is not an appointment, return None or an appropriate default
        return None
    
    def getItemByRowid(self, lastrowid):
        # Traverse through the month-year and date hierarchy
        for month_year, dates in self.data.items():
            for date, appointments in dates.items():
                for appointment in appointments:
                    # Check if 'appointment' is a dictionary and has a 'Rowid' key
                    if isinstance(appointment, dict) and str(appointment.get('Rowid')) == str(lastrowid):
                        return self.ObjectToItem(appointment)
                    
        return None


class BookAppointments(wx.Panel):
    def __init__(self, parent, main_frame):
        super(BookAppointments, self).__init__(parent)
        self.maxChars = 15
        self.main_frame = main_frame
        # Initialize the SplitterWindow
        splitter = wx.SplitterWindow(self)

        
        # Panel for the form fields (left)
        self.formPanel = wx.Panel(splitter)
        self.formPanel.SetBackgroundColour('#F0F0F0')
        self.setupFormFields(self.formPanel)
        
        # Panel for the DataViewCtrl (right)
        self.dvcPanel = wx.Panel(splitter)

        # Menubar
        menubar = wx.MenuBar()
        # Manage Menu
        manage_menu = wx.Menu()
        manage_item = manage_menu.Append(wx.ID_ANY, "Manage", "Manage Appointments")
        self.Bind(wx.EVT_MENU, self.onManageClick, manage_item)
        menubar.Append(manage_menu, "Manage")
        self.main_frame.SetMenuBar(menubar)  # Set the menubar on the main frame directly


        self.dataViewCtrl()
        self.expandAllNodes()

        self.dvc.Bind(dv.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.onRightClick)
        self.dvc.Bind(dv.EVT_DATAVIEW_ITEM_ACTIVATED, self.onItemActivated)
    
        # Split the window vertically with the form on the left and tree view on the right
        splitter.SplitVertically(self.formPanel, self.dvcPanel)
        # Delay setting the sash position using wx.CallAfter
        wx.CallAfter(self.adjustSashPosition, splitter)

        splitter.SetMinimumPaneSize(20)  # Minimum size of a pane
        
        # Layout management for the BookAppointments panel to include the splitter
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(splitter, 1, wx.EXPAND)
        self.SetSizer(sizer)

        self.clinicLastRowid = {}

        self.exclusions = {
                "01/01": "New Year's Day",
                "01/05": "Labour Day",
                "01/06": "Madaraka Day",
                "10/10": "Huduma Day",
                "20/10": "Mashujaa Day",
                "12/12": "Jamhuri Day",
                "25/12": "Christmas Day",
                "26/12": "Boxing Day",
                "31/12": "New Year's Eve"
            }
        
        self.selected_date_str = None

    def onManageClick(self, event):
        pass

    def adjustSashPosition(self, splitter):
        # Set sash position based on the current size
        splitter.SetSashPosition(int(self.GetSize().GetWidth() / 3))

    def onTextChange(self, event):
        textCtrl = event.GetEventObject()
        self.capitalizeCtrl(textCtrl)

    def capitalizeCtrl(self, textCtrl):

         # Capitalizes the first letter of the content of the given TextCtrl
        cursorPos = textCtrl.GetInsertionPoint() #current cursor position
        text = textCtrl.GetValue()
         # Capitalize the first letter and keep the rest of the text as is
        capitalizedText = text[:1].upper() + text[1:]
        textCtrl.ChangeValue(capitalizedText) #update textctrl's content
        textCtrl.SetInsertionPoint(cursorPos) #restore cursor position

    def setupFormFields(self, parent):
        
        self.entries = {}
        fields = ["CLINIC","CLINIC NUMBER", "FIRST NAME", "LAST NAME",  "PHONE NUMBER", "GENDER",
                   "DATE", "TIME"]
        clinics = ["DOPC", "GOPC", "HOPC", "SOPC", "MOPC"]
        genders = ["Male", "Female", "Other"]

        font = wx.Font(10, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        for field in fields:
            field_sizer = wx.BoxSizer(wx.VERTICAL)

            label = wx.StaticText(parent, label=f"{field}:")  # Using 'parent' as the parent widget
            label.SetFont(font)
            field_sizer.Add(label, 0, wx.ALL, 5)

            if field == "GENDER":
                input_field = wx.ComboBox(parent, choices=genders, style=wx.CB_READONLY)
                self.entries[field] = input_field
                self.genderComboBox = input_field
                
            elif field == "CLINIC":
                input_field = wx.ComboBox(parent, choices=clinics, style= wx.CB_READONLY)
                self.clinicsComboBox = input_field
                self.clinicsComboBox.SetSelection(0)

                self.clinicsComboBox.Bind(wx.EVT_COMBOBOX, self.onClinicSelected)
                self.entries[field] = input_field

            elif field == "CLINIC NUMBER":
                input_field = wx.TextCtrl(parent)
                self.entries[field] = input_field
                input_field.Bind(wx.EVT_CHAR, self.onTypeChar)
                self.clinic_number_field = input_field
                self.clinic_number_field.Bind(wx.EVT_TEXT, self.onTypeClinicNumber)

            elif field == "DATE":
                input_field = wx.adv.DatePickerCtrl(parent, style=wx.adv.DP_DROPDOWN | wx.adv.DP_ALLOWNONE)
                self.entries[field] = input_field

            elif field == "TIME":
                input_field = wx.adv.TimePickerCtrl(parent)
                # Set default time to 8:00:00
                input_field.SetTime(8, 0, 0)
                self.entries[field] = input_field

            elif field == "COMMENTS":
                input_field = wx.TextCtrl(parent, style=wx.TE_MULTILINE, size=(-1, 60))
                self.entries[field] = input_field
                
            elif field == "FIRST NAME" or field == "LAST NAME":
                input_field = wx.TextCtrl(parent)
                self.entries[field] = input_field
                input_field.Bind(wx.EVT_TEXT, self.onTextChange)
                first_name_field = input_field
                first_name_field.Bind(wx.EVT_TEXT, self.onTypeName)

            elif field == "PHONE NUMBER":
                input_field = wx.TextCtrl(parent)
                input_field.Bind(wx.EVT_CHAR, self.onTypeChar)
                self.entries[field] = input_field
                self.phone_field = input_field
                self.phone_field.Bind(wx.EVT_TEXT, self.onTypeDigit)


            input_field.SetFont(font)
            field_sizer.Add(input_field, 1, wx.ALL|wx.EXPAND, 5)
            main_sizer.Add(field_sizer, 0, wx.EXPAND)

        if field in ["CLINIC NUMBER", "FIRST NAME", "LAST NAME", "PHONE NUMBER"]:  
            input_field = wx.TextCtrl(parent, style=wx.TE_PROCESS_ENTER) #enter key setting


        # Setup for CLEAR and BOOK buttons arranged horizontally
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.reset_button = wx.Button(parent, label="RESET")
        self.search_button = wx.Button(parent, label="SEARCH")
        self.edit_button = wx.Button(parent, label="EDIT")
        self.book_button = wx.Button(parent, label="BOOK")

        self.reset_button.SetFont(font)
        self.search_button.SetFont(font)
        self.edit_button.SetFont(font)
        self.book_button.SetFont(font)

        button_sizer.Add(self.reset_button, 0, wx.ALL, 5)
        button_sizer.Add(self.search_button, 0, wx.ALL, 5) 
        button_sizer.Add(self.edit_button, 0, wx.ALL, 5)
        button_sizer.Add(self.book_button, 0, wx.ALL, 5)

        # Bind the buttons to their event handlers
        self.reset_button.Bind(wx.EVT_BUTTON, lambda evt: self.onResetClick(parent, evt))
        self.edit_button.Bind(wx.EVT_BUTTON, self.onEditClick)
        self.book_button.Bind(wx.EVT_BUTTON, self.submitForm)
        self.search_button.Bind(wx.EVT_BUTTON, self.onSearchClick)

        self.edit_button.Disable()

        # Correct use of AddStretchSpacer
        main_sizer.AddStretchSpacer()
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER)
        parent.SetSizer(main_sizer)

    def onTypeClinicNumber(self, event):
        value = self.clinic_number_field.GetValue().strip()

        #check if the length exceeds 10 digits
        if len(value) > 6:
            self.clinic_number_field.ChangeValue(value[:6])
            #set the insertion point to the end of the text
            self.clinic_number_field.SetInsertionPointEnd()
        else:
            event.Skip() #proceed with the default event handling


    def onTypeDigit(self, event):
        value = self.phone_field.GetValue().strip()

        #check if the length exceeds 10 digits
        if len(value) > 10:
            self.phone_field.ChangeValue(value[:10])
            #set the insertion point to the end of the text
            self.phone_field.SetInsertionPointEnd()
        else:
            event.Skip() #proceed with the default event handling

    def onTypeChar(self, event):
        keycode = event.GetKeyCode()

        # Allow tab, shift+tab, backspace, delete, enter/return, and numeric keys
        allowed_keys = [
            wx.WXK_TAB, wx.WXK_NUMPAD_TAB, 
            wx.WXK_BACK, wx.WXK_DELETE, wx.WXK_NUMPAD_DELETE,
            wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER,  # Include enter/return keys
        ]
        if keycode in allowed_keys or ord('0') <= keycode <= ord('9') or wx.WXK_NUMPAD0 <= keycode <= wx.WXK_NUMPAD9:
            event.Skip()  # Let the event be processed elsewhere as well.
        elif keycode < 256 and chr(keycode).isnumeric():  # For numeric keys outside the numpad
            event.Skip()  # This is numeric, let it through.
        else:
            # Ignore other non-numeric, non-control characters
            return  # No event.Skip() means we're consuming this event without further processing.
        
    def onTypeName(self, event):
        textCtrl = event.GetEventObject()
        # Check if the length of text exceeds the maxChars limit
        if len(textCtrl.GetValue()) > self.maxChars:
            # If it does, set the value to its first maxChars characters
            textCtrl.ChangeValue(textCtrl.GetValue()[:self.maxChars])
            textCtrl.SetInsertionPointEnd()  # Move the cursor to the end
        event.Skip()  # Always call Skip to continue processing the event


    def dataViewCtrl(self):
        self.dvc = dv.DataViewCtrl(self.dvcPanel, style=dv.DV_ROW_LINES | dv.DV_VERT_RULES)
        self.model = AppointmentsModel(self.loadAppointments())
        self.dvc.AssociateModel(self.model)
        

        # Add columns to the DataViewCtrl
        self.dvc.AppendTextColumn("VISIT DATE", 0, width=100)
        self.dvc.AppendTextColumn("CLINIC", 1, width=100)
        self.dvc.AppendTextColumn("CLINIC NUMBER", 2, width = 100)
        self.dvc.AppendTextColumn("FIRST NAME", 3, width = 100)
        self.dvc.AppendTextColumn("LAST NAME", 4, width=100)
        self.dvc.AppendTextColumn("PHONE NUMBER", 5, width=100)
        self.dvc.AppendTextColumn("GENDER", 6, width = 100)
        self.dvc.AppendTextColumn("DATE", 7, width = 100)
        self.dvc.AppendTextColumn("TIME", 8, width = 100)
    

        # Layout for the DataViewCtrl panel
        dvcSizer = wx.BoxSizer(wx.VERTICAL)
        dvcSizer.Add(self.dvc, 1, wx.EXPAND | wx.ALL, 5)
        self.dvcPanel.SetSizer(dvcSizer)

    def prepareData(self):
        wx_date = self.entries['DATE'].GetValue()
        if wx_date.IsValid():
            year = wx_date.GetYear()
            # wx.DateTime month is zero-based, so add 1
            month = wx_date.GetMonth() + 1
            day = wx_date.GetDay()
            # Convert to Python's datetime.date
            python_date = date(year, month, day)
            # ISO format

            self.iso_date = python_date.isoformat()
        else:
            self.iso_date = None

        #format time
        time = self.entries['TIME'].GetValue()
        self.iso_time = time.Format("%I:%M %p")

    def expandAllNodes(self):
        self.model = self.dvc.GetModel()
        
        # Iterate through month-year nodes first
        for month_year in self.model.data.keys():
            month_year_item = self.model.ObjectToItem(month_year)
            if month_year_item.IsOk():
                self.dvc.Expand(month_year_item)
                
                # Now iterate through the dates within this month-year
                for date in self.model.data[month_year].keys():
                    date_item = self.model.ObjectToItem(date)
                    if date_item.IsOk():
                        self.dvc.Expand(date_item)

    def onItemActivated(self, event):
        self.edit_button.Enable()
        self.book_button.Disable()
        item = event.GetItem()
        if item.IsOk():
            self.item_data = self.model.GetItemData(item)  # Retrieve data for the selected item

            # Update form fields based on retrieved data
            self.entries['CLINIC NUMBER'].SetValue(str(self.item_data['ClinicNumber']))  # Convert numeric data to string
            if 'Gender' in self.item_data:
                self.entries['GENDER'].SetStringSelection(self.item_data['Gender']) 
            self.entries['FIRST NAME'].SetValue(self.item_data['FirstName'])
            self.entries['LAST NAME'].SetValue(self.item_data['LastName'])
            self.entries['PHONE NUMBER'].SetValue(str(self.item_data['PhoneNumber']))

            self.entries['CLINIC'].SetValue(self.item_data['Clinic'])

            date_string = self.item_data['Date']
            #Convert the dateString to a datetime.date object
            dateObject = datetime.strptime(date_string, "%d/%m/%Y").date()
            # Create a wx.DateTime object from the dateObject
            self.item_date = wx.DateTime.FromDMY(day=dateObject.day, month=dateObject.month-1, year=dateObject.year)
            self.entries['DATE'].SetValue(self.item_date)

            time_str = self.item_data['Time']  # The time string, e.g., "15:30" or "03:30 PM"
            time_dt = wx.DateTime()  # Create an empty wx.DateTime object
            # Parse the time string into the wx.DateTime object
            if time_dt.ParseTime(time_str):
                self.entries['TIME'].SetValue(time_dt)
                        

    def onRightClick(self, event):
        menu = wx.Menu()
        deleteItem = menu.Append(wx.ID_ANY, 'Delete')
         # Bind the menu item selection event to a method that handles deletion
        self.Bind(wx.EVT_MENU, self.onDeleteItem, deleteItem)
           # Show the context menu at the position of the mouse cursor
        self.PopupMenu(menu)
        #cleanUp
        menu.Destroy()

    def onDeleteItem(self, event):
        message = "Appointment deleted from the application!"
        colour = wx.RED
        item = self.dvc.GetSelection()
        if item.IsOk():
            if wx.MessageBox("This appointment will be permanently deleted from the application. Proceed?",
                              "Confirm delete", wx.ICON_WARNING | wx.YES_NO | wx.NO_DEFAULT) != wx.YES:
                return
            
            # Convert the item to the object it represents in the model
            obj = self.model.ItemToObject(item)
            # If the object is an appointment (a dictionary in this context)
            if isinstance(obj, dict):
        
                row_id = obj.get('Rowid')
                if row_id:
                    try:
                        conn = sqlite3.connect('appointments.db')
                        cursor = conn.cursor()
                        # Delete the appointment from the database using its RowID
                        cursor.execute("DELETE FROM bookings WHERE RowID = ?", (row_id,))
                        conn.commit()
                    except sqlite3.Error as error:
                        wx.MessageBox(f"Failed to delete appointment from the database: {error}", "Database Error", wx.ICON_ERROR)
                    finally:
                        conn.close()

                self.loadAppointments()
                self.updateModel(self.data)
                self.main_frame.setStatus(message, colour)
                self.expandAllNodes()

    def loadAppointments(self):
        self.data = {}
        conn = sqlite3.connect('appointments.db')
        cursor = conn.cursor()

        clinic = self.entries['CLINIC'].GetValue()

        try:
            cursor.execute("SELECT Clinic, ClinicNumber, \
                        FirstName, LastName, PhoneNumber, Gender, \
                        Date, Time, Comments, ROWID as Rowid FROM bookings \
                           WHERE Date >= date('now') AND Clinic = \
                            :clinic ORDER BY Date", {'clinic': clinic})
            bookings = cursor.fetchall()
            
            for booking in bookings:
                clinic, clinic_number, first_name, last_name, phone_number, gender,\
                date, time, comments, rowid = booking
                
                # Convert the date string to a datetime object to extract year and month
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                self.month_year = date_obj.strftime("%B %Y")  # Format as "Month Year", e.g., "March 2023"
                self.date_formatted = date_obj.strftime("%d/%m/%Y")  # Format date as "dd/mm/yyyy"
  
                # Check if the month_year is already a key in the data dictionary
                if self.month_year not in self.data:
                    self.data[self.month_year] = {}  # Initialize a new dict for this month_year if not present
                
                # Check if the date is already a key under the month_year
                if self.date_formatted not in self.data[self.month_year]:
                    self.data[self.month_year][self.date_formatted] = []  # Initialize a new list for this date if not present
                
                # Append a dictionary of the booking details to the list associated with the date under the month_year
                self.data[self.month_year][self.date_formatted].append({
                    'Clinic': clinic,
                    'ClinicNumber': clinic_number,
                    'FirstName': first_name,
                    'LastName': last_name,
                    'Gender': gender,
                    'PhoneNumber': phone_number,
                    'Date': self.date_formatted,
                    'Time': time,
                    'Comments': comments,
                    'Rowid': rowid
                })

        except sqlite3.Error as e:
            wx.MessageBox(f"Failed to load appointments: {e}", "Database Error", wx.OK | wx.ICON_ERROR)
        finally:
            conn.close()

        return self.data

    def updateModel(self, data):
        if hasattr(self, 'model'):
            self.model.setData(data)

    def onResetClick(self, parent, event=None):  # Adjust the signature to include parent after event
        # Iterate through all children of the parent panel
        self.book_button.Enable()
        for child in parent.GetChildren():
            # Determine the type of each child and clear its value as appropriate
            if child == self.genderComboBox:
                child.SetSelection(-1)  # Reset combo box selection
            elif isinstance(child, wx.TextCtrl):
                child.SetValue('')  # Clear text fields
            elif isinstance(child, wx.adv.DatePickerCtrl):
                self.entries["DATE"].SetValue(wx.DefaultDateTime)

        self.updateModel(self.data)
        self.edit_button.Disable()
        self.expandAllNodes()
        self.entries['CLINIC NUMBER'].SetFocus()

    def onSearchClick(self, event):
        self.search_data = {}
        conn = sqlite3.connect('appointments.db')
        cursor = conn.cursor()
        self.prepareData()

        clinicnumber = self.entries['CLINIC NUMBER'].GetValue().strip()
        firstname = self.entries['FIRST NAME'].GetValue().strip()
        lastname = self.entries['LAST NAME'].GetValue().strip()
        phonenumber = self.entries['PHONE NUMBER'].GetValue().strip()
        searchdate = self.iso_date
        gender = self.entries['GENDER'].GetValue()

        if clinicnumber or firstname or lastname or phonenumber or searchdate or gender:
                # Start with the base query
            query_parts = ["SELECT Clinic, ClinicNumber, FirstName, LastName, PhoneNumber, Gender, Date, Time, Comments, ROWID as Rowid FROM bookings"]
            conditions = []
            params = {}

            # Add conditions dynamically based on provided values
            if clinicnumber:
                conditions.append("ClinicNumber = :clinicnumber")
                params['clinicnumber'] = clinicnumber

            if firstname:
                conditions.append("FirstName LIKE :firstname")
                params['firstname'] = '%' + firstname + '%'

            if lastname:
                conditions.append("LastName LIKE :lastname")
                params['lastname'] = '%' + lastname + '%'

            if phonenumber:
                conditions.append("PhoneNumber = :phonenumber")
                params['phonenumber'] = phonenumber

            if searchdate:
                conditions.append("Date = :searchdate")
                params['searchdate'] = searchdate

            if gender:
                conditions.append("Gender = :gender")
                params['gender'] = gender

            # Only add a WHERE clause if there are conditions
            if conditions:
                query_parts.append("WHERE " + " AND ".join(conditions))

            # Always add the order by clause
            query_parts.append("ORDER BY Date")

            # Join the parts to form the final query
            query = " ".join(query_parts)

            # Execute the query
            try:
                cursor.execute(query, params)

                bookings = cursor.fetchall()

                if bookings:

                    for booking in bookings:
                        clinic, clinic_number, first_name, last_name, phone_number, gender,\
                        date, time, comments, rowid = booking
                        
                        # Convert the date string to a datetime object to extract year and month
                        date_obj = datetime.strptime(date, "%Y-%m-%d")
                        month_year = date_obj.strftime("%B %Y")  # Format as "Month Year", e.g., "March 2023"
                        date_formatted = date_obj.strftime("%d/%m/%Y")  # Format date as "dd/mm/yyyy"

                        # Check if the month_year is already a key in the data dictionary
                        if month_year not in self.search_data:
                            self.search_data[month_year] = {}  # Initialize a new dict for this month_year if not present
                        
                        # Check if the date is already a key under the month_year
                        if date_formatted not in self.search_data[month_year]:
                            self.search_data[month_year][date_formatted] = []  # Initialize a new list for this date if not present
                        
                        # Append a dictionary of the booking details to the list associated with the date under the month_year
                        self.search_data[month_year][date_formatted].append({
                            'Clinic': clinic,
                            'ClinicNumber': clinic_number,
                            'FirstName': first_name,
                            'LastName': last_name,
                            'Gender': gender,
                            'PhoneNumber': phone_number,
                            'Date': date_formatted,
                            'Time': time,
                            'Comments': comments,
                            'Rowid': rowid
                        })

                    self.updateModel(self.search_data)
                    self.edit_button.Disable()
                    self.entries['CLINIC NUMBER'].SetFocus()
                    self.expandAllNodes()

                else:
                    wx.MessageBox("There is nothing to show for that search; please try a different one")
                    self.entries['CLINIC NUMBER'].SetFocus()
                    return

            except sqlite3.Error as e:
                wx.MessageBox(f"Failed to load appointments: {e}", "Database Error", wx.OK | wx.ICON_ERROR)
                return
            finally:
                conn.close()

        else:
            wx.MessageBox("No search item entered: please enter an item and try again")
            self.entries['CLINIC NUMBER'].SetFocus()
            return


    def onEditClick(self, event):
        self.prepareData()
        self.update_performed = False

        data = {
                'clinic': self.entries['CLINIC'].GetValue(),
                'clinic_number': self.entries['CLINIC NUMBER'].GetValue().strip(),
                'first_name': self.entries['FIRST NAME'].GetValue().strip(),
                'last_name': self.entries['LAST NAME'].GetValue().strip(),
                'gender': self.entries['GENDER'].GetValue(),
                'phone_number': self.entries["PHONE NUMBER"].GetValue().strip(),
                'date': self.iso_date,
                'time': self.iso_time
            }
        
        validation_result = self.validate_edit(data)
        if validation_result is not None:
            dialog = wx.MessageDialog(self, validation_result, "Validation Error", wx.OK | wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()
            return
        
        current_clinic = self.item_data['Clinic']
        current_clinic_number = self.item_data['ClinicNumber']
        current_date = self.item_data['Date']
        python_date = datetime.strptime(current_date, '%d/%m/%Y').date() 
        #ISO format
        current_date = python_date.isoformat()  

        conn = sqlite3.connect('appointments.db')
        cursor = conn.cursor()

        sql = '''SELECT Clinic, ClinicNumber, Date from bookings 
        WHERE Clinic = :current_clinic 
        AND ClinicNumber = :current_clinic_number 
        AND Date = :current_date'''
        params = {'current_clinic': current_clinic, 
                'current_clinic_number': current_clinic_number,
                'current_date': current_date}
                            
        cursor.execute(sql, params)
        result = cursor.fetchall()

        if result:
    
            if (self.item_data['Clinic'] != data['clinic'] or 
                self.item_data['ClinicNumber'] != data['clinic_number'] or
                self.item_date != self.entries['DATE'].GetValue()):

                with conn:
                    sql = '''UPDATE bookings
                            SET Clinic = :clinic,
                            ClinicNumber = :clinic_number,
                            Date = :date 
                        WHERE Clinic = :current_clinic 
                        AND ClinicNumber = :current_clinic_number 
                        AND Date = :current_date'''
                    params = {'clinic': data['clinic'], 'clinic_number': data['clinic_number'],
                            'date': data['date'], 'current_clinic': current_clinic, 
                            'current_clinic_number': current_clinic_number,
                            'current_date': current_date}
                    
                    cursor.execute(sql, params)
                    self.update_performed = True

            if (self.item_data['FirstName'] != data['first_name'] or
                self.item_data['LastName'] != data['last_name'] or
                self.item_data['PhoneNumber'] != data['phone_number'] or
                self.item_data['Gender'] != data['gender'] or
                self.item_data['Time']!= data['time']
                ):
            
                with conn:
                    sql = '''UPDATE bookings
                            SET FirstName= :first_name,
                            LastName= :last_name,
                            PhoneNumber= :phone_number,
                            Gender= :gender, 
                            Time= :time
                        WHERE Clinic= :clinic AND ClinicNumber = :clinic_number
                        AND Date= :date
                            '''
                    cursor.execute(sql, data)

                    self.update_performed = True
        else:
            response = wx.MessageBox("Edit not done: The selected item might have been deleted. Rebook instead?",
                           "Edit dichotomy", style = wx.ICON_ERROR | wx.YES_NO | wx.YES_DEFAULT)
            if response == wx.YES:
                self.edit_button.Disable()
                self.book_button.Enable()
                self.book_button.SetFocus()
            else:
                self.onResetClick()
            return
                
        if self.update_performed:
            self.message = "Appointment edited successfully"
            self.onResetClick(self.formPanel)
            self.onEditSuccessful()    
            self.book_button.Enable()
            self.edit_button.Disable()

        else:
            edit_dialog = wx.MessageDialog(None, 
                            "You didn't make any changes to the selected data: Exit editing?", 
                            "No changes made",
                            wx.OK | wx.CANCEL | wx.CANCEL_DEFAULT | wx.ICON_INFORMATION)
            
            # Show the dialog and check the response
            edit_response = edit_dialog.ShowModal()
            if edit_response == wx.ID_OK:
                self.onResetClick(self.formPanel)
                self.edit_button.Disable()
            elif edit_response == wx.ID_CANCEL:
                self.entries['CLINIC NUMBER'].SetFocus()
                return
            edit_dialog.Destroy()

        # Get the RowID of the newly updated item
        item = self.model.getItemByRowid(cursor.lastrowid)
        
        if item:
            self.dvc.EnsureVisible(item)
            self.dvc.Select(item)

        conn.close()

    def onEditSuccessful(self):
            self.main_frame.setStatus(self.message)
            self.loadAppointments()
            self.updateModel(self.data)
            self.expandAllNodes()

    def submitForm(self, event):
        self.prepareData()
        data = {
                'clinic': self.entries['CLINIC'].GetValue(),
                'clinic_number': self.entries['CLINIC NUMBER'].GetValue().strip(),
                'first_name': self.entries['FIRST NAME'].GetValue().strip(),
                'last_name': self.entries['LAST NAME'].GetValue().strip(),
                'gender': self.entries['GENDER'].GetValue(),
                'phone_number': self.entries["PHONE NUMBER"].GetValue().strip(),
                'date': self.iso_date,
                'time': self.iso_time,
            }
            
        self.check_duplication(data)
        validation_result = self.validate_booking(data)
        if validation_result is not None:
            dialog = wx.MessageDialog(self, validation_result, "Validation Error", wx.OK | wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()
            return 
        
        conn = sqlite3.connect('appointments.db')
        cursor = conn.cursor()

        try:
            with conn: # Using the connection as a context manager to auto-commit/rollback
                    sql = '''INSERT INTO bookings(Clinic, ClinicNumber, FirstName, LastName, PhoneNumber,
                                Gender, Date, Time)
                            VALUES(:clinic, :clinic_number, :first_name, :last_name, :phone_number, :gender,
                            :date, :time)'''

    
            cursor.execute(sql, data)
            conn.commit() 
            
            message = "Successfully booked!"
            
            self.loadAppointments()
            self.updateModel(self.data)
            self.expandAllNodes()

            self.rowid = cursor.lastrowid
            try:
                current_rowid = self.rowid
                item = self.model.getItemByRowid(current_rowid)
                if item and item.IsOk():
                    self.dvc.Select(item)
                    self.dvc.EnsureVisible(item)
                else:
                    print("The item is either None or not valid.")
            except Exception as e:
                print(f"An error occurred: {e}")


            self.clinicLastRowid[data['clinic']] = cursor.lastrowid
        

            self.main_frame.setStatus(message)
            #wx.MessageBox(f"TCA {data['date']}, {data['time']}, {data['clinic']}")

        except sqlite3.IntegrityError:
            wx.MessageBox("Failed to book: The patient already has an appointment on the selected date!", "Error", wx.OK | wx.ICON_ERROR)
        finally:
            conn.close()
        self.entries['CLINIC NUMBER'].SetFocus()


    def validate_booking(self, data):
        validation_data = data
        current_date = datetime.now().date() #date component only, ignore time as it considers only midnight as valid
        #since string date cannot be compared to a datetime object, convert
        input_date_str = validation_data['date']
        input_date = datetime.strptime(input_date_str, '%Y-%m-%d').date()
    
        try:
            clinic_number = int(validation_data['clinic_number'])
            if clinic_number < 0: 
                return "Clinic number must be a positive number."
        except ValueError:
            return "Clinic number should be entered as numbers!"
        
        if len(validation_data['clinic_number']) < 6:
                self.entries['CLINIC NUMBER'].SetFocus()
                return "Clinic number must be 6 numbers"

        # First Name and Last Name: Cannot be null (empty)
        if not validation_data['first_name']:
            self.entries['FIRST NAME'].SetFocus()
            return "First name cannot be empty."
        if not validation_data['last_name']:
            self.entries['LAST NAME'].SetFocus()
            return "Last name cannot be empty."

        # Validation of phone numbers
        if not validation_data['phone_number']:
            self.entries['PHONE NUMBER'].SetFocus()
            return "Supply patient's or next of kin's phone number."
        if not (validation_data['phone_number'].isdigit()):
                self.entries['PHONE NUMBER'].SetFocus()
                return "Phone number must be 10 digits!"
        if not len(validation_data['phone_number'])==10:
                self.entries['PHONE NUMBER'].SetFocus()
                return "Phone number must be 10 digits"

        if not (validation_data['gender']):
            self.entries['GENDER'].SetFocus()
            return "Patient's gender is required"

        # Clinic: Must also be filled
        if not validation_data['clinic']:
            self.entries['CLINIC'].SetFocus()
            return "Clinic must be selected."

        if validation_data['clinic'] == 'GOPC' and validation_data['gender'] == 'Male':
            self.entries['GENDER'].SetFocus()
            return "Male patients cannot be booked for GOPC! Please confirm correct gender and/or clinic selection"
        
        if not validation_data['date']:
            self.entries['DATE'].SetFocus()
            return "Appointment date must be selected"
        if input_date < current_date: #date component only, ignore time as it considers only midnight as valid
            return "You cannot book an appointment on a past date; please select a current or future one!"
          
        selected_date = self.entries['DATE'].GetValue()
        self.date_month = selected_date.Format('%d/%m')
        date_str = selected_date.Format("%a %d %B %Y") #%a for abbreviated day-of-week, %A for full

        if self.date_month in self.exclusions:
            self.selected_date_str = date_str

        if self.selected_date_str:
            decision = wx.MessageBox(f"{self.selected_date_str}: {self.exclusions[self.date_month]}. Continue booking anyway?",
                                        "Excluded Date",
                                        style= wx.ICON_WARNING | wx.YES_NO | wx.NO_DEFAULT)
            if decision == wx.YES:
                self.selected_date_str = None
                pass
            else: 
                self.selected_date_str = None
            return
                
        # If all validations pass
        return None
    
    def check_duplication(self, data):
        data = data
        # Traverse through the month-year and date hierarchy
        for month_year, dates in self.data.items():
            for date, appointments in dates.items():
                for appointment in appointments:
                    if (appointment['Clinic'] == data['clinic'] and 
                        appointment['ClinicNumber'] == data['clinic_number']):
                        # Found a conflicting appointment
                        self.entries['CLINIC NUMBER'].SetFocus()
                        booked_date = self.model.convert_yyyy_mm_dd_to_dd_mm_yyyy(date)  
                        reaction = wx.MessageBox(f"Clinic number {data['clinic_number']} has an unhonored {data['clinic']} appointment on {booked_date}. Edit it instead?", 
                                                 "Appointment Exists", style = wx.ICON_ERROR | wx.YES_NO | wx.YES_DEFAULT)
                        if reaction == wx.YES:
                            conn = sqlite3.connect('appointments.db')
                            cursor = conn.cursor()
                            this_clinic = appointment['Clinic']
                            this_clinic_number = appointment['ClinicNumber']
                            this_date = appointment['Date']
                            this_date = self.model.convert_dd_mm_yyyy_to_yyyy_mm_dd(this_date)

                            cursor.execute('''SELECT ROWID as Rowid
                                            FROM bookings WHERE Clinic = :this_clinic
                                           AND ClinicNumber = :this_clinic_number AND Date = :this_date ORDER BY Date''',
                                            {'this_clinic': this_clinic,
                                             'this_clinic_number': this_clinic_number,
                                             'this_date': this_date})
                            this_rowid = cursor.fetchone()
                            
                            if this_rowid:
                                this_rowid = this_rowid[0]
                                print(this_rowid)
                                item = self.model.getItemByRowid(this_rowid)
                                self.dvc.EnsureVisible(item)
                                self.dvc.Select(item)

                            return

                        else:
                            self.entries['CLINIC NUMBER'].SetFocus()
                        return
                                     

    def validate_edit(self, data):
        selected_date = self.entries['DATE'].GetValue()
        self.date_month = selected_date.Format('%d/%m')
        date_str = selected_date.Format("%a %d %B %Y") #%a for abbreviated day-of-week, %A for full

        if self.date_month in self.exclusions:
            self.selected_date_str = date_str

        if self.selected_date_str:
            decision = wx.MessageBox(f"{self.selected_date_str}: {self.exclusions[self.date_month]}. Continue booking anyway?",
                                        "Excluded Date",
                                        style= wx.ICON_WARNING | wx.YES_NO | wx.NO_DEFAULT)
            if decision == wx.YES:
                self.selected_date_str = None
                pass
            else: 
                self.selected_date_str = None
            return
                
        validation_data = data
        current_date = datetime.now().date() #date component only, ignore time as it considers only midnight as valid
        #since string date cannot be compared to a datetime object, convert
        input_date_str = validation_data['date']
        input_date = datetime.strptime(input_date_str, '%Y-%m-%d').date()
    
        try:
            clinic_number = int(validation_data['clinic_number'])
            if clinic_number < 0: 
                return "Clinic number must be a positive number."
        except ValueError:
            return "Clinic number should be entered as numbers!"
        
        if len(validation_data['clinic_number']) < 6:
                return "Clinic number must be 6 numbers"

        # First Name and Last Name: Cannot be null (empty)
        if not validation_data['first_name']:
            return "First name cannot be empty."
        if not validation_data['last_name']:
            return "Last name cannot be empty."

        # Validation of phone numbers
        if not validation_data['phone_number']:
            return "Supply patient's or next of kin's phone number."
        if not (validation_data['phone_number'].isdigit()):
                return "Phone number must be 10 digits!"
        if not len(validation_data['phone_number'])==10:
                return "Phone number must be 10 digits"

        if not (validation_data['gender']):
            return "Patient's gender is required"

        # Clinic: Must also be filled
        if not validation_data['clinic']:
            return "Clinic must be selected."

        if validation_data['clinic'] == 'GOPC' and validation_data['gender'] == 'Male':
            return "Male patients cannot be booked for GOPC! Please confirm correct gender and/or clinic selection"
        
        if not validation_data['date']:
            return "Appointment date must be selected"
        if input_date < current_date: #date component only, ignore time as it considers only midnight as valid
            return "You cannot book an appointment on a past date; please select a current or future one!"
        
        # If all validations pass
        return None

    def onClinicSelected(self, event):
        self.loadAppointments()
        self.model.setData(self.data)
        self.expandAllNodes()

        clinic = self.entries['CLINIC'].GetValue()

        
        if clinic in self.clinicLastRowid:

            item = self.model.getItemByRowid(self.rowid)
            if item:
                self.dvc.EnsureVisible(item)
        
if __name__ == "__main__":
    app = AppointmentApp()
    app.MainLoop()

   