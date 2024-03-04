import wx
import wx.aui
import wx.adv  # For wx.DatePickerCtrl
import wx.lib.mixins.listctrl  # For CheckListCtrlMixin, if needed
import sqlite3
from datetime import datetime
from datetime import date
import wx.dataview as dv

       
class AppointmentApp(wx.App):
    def OnInit(self):
        frame = MainFrame()
        frame.Show(True)
        return True
        
    
class MainFrame(wx.Frame):
    def __init__(self):
        super(MainFrame, self).__init__(None, title="ClinicPro Appointment Booking System")
        self.Maximize(True)
        self.SetBackgroundColour('#F0F0F0')
        self.panel = wx.Panel(self)

        self.initStatusBar()
        self.statusBar.SetBackgroundColour('#2B2B2B)')
        self.notebook = wx.aui.AuiNotebook(self.panel)
        
        # Initialize Login Screen
        self.login_tab = LoginScreen(self.notebook, self)
        self.notebook.AddPage(self.login_tab, "Login")

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.statusBar, 0, wx.ALL|wx.EXPAND, 5)
        self.sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        self.panel.SetSizer(self.sizer)

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

    def focus_next_widget(self, event):
        # move focus to the next control in the tab order
        event.Skip(False)  # Important to allow for default processing
        widget = event.GetEventObject()
        widget.Navigate()
            
    def successful_login(self):
        # Remove the login tab
        self.notebook.DeletePage(0)
        
        # Add the Home tab, now passing 'self' as the main_frame reference
        home_tab = HomeScreen(self.notebook, self)  # 'self' is the MainFrame instance
        self.notebook.AddPage(home_tab, "Home")


class LoginScreen(wx.Panel):
    def __init__(self, parent, main_frame):
        super(LoginScreen, self).__init__(parent)
        self.main_frame = main_frame
        
        # Username Field
        wx.StaticText(self, label="Username:", pos=(10, 10))
        self.username = wx.TextCtrl(self, pos=(110, 10), size=(200, -1))
        
        # Password Field
        wx.StaticText(self, label="Password:", pos=(10, 50))
        self.password = wx.TextCtrl(self, pos=(110, 50), size=(200, -1), style=wx.TE_PASSWORD)
        
        # Login Button
        login_button = wx.Button(self, label="Login", pos=(110, 100))
        login_button.Bind(wx.EVT_BUTTON, self.on_login_click)
        
    def on_login_click(self, event):
      
        self.main_frame.successful_login()

class HomeScreen(wx.Panel):
    def __init__(self, parent, main_frame):
        super(HomeScreen, self).__init__(parent)
        self.main_frame = main_frame  # Store the reference to the main frame
        self.SetBackgroundColour('#F0F0F0')
        # Layout for buttons
        layout = wx.BoxSizer(wx.VERTICAL)
        
        # Welcome text
        welcome_text = wx.StaticText(self, label="Welcome to the ClinicPro Homescreen!")
        layout.Add(welcome_text, 0, wx.ALL|wx.CENTER, 5)
        
        # Book Appointments Button
        book_page_button = wx.Button(self, label="Book Appointments")
        book_page_button.Bind(wx.EVT_BUTTON, self.on_book_click)
        layout.Add(book_page_button, 0, wx.ALL|wx.CENTER, 5)
        
        # See Appointments Button
        see_button = wx.Button(self, label="View Appointments")
        see_button.Bind(wx.EVT_BUTTON, self.on_see_click)
        layout.Add(see_button, 0, wx.ALL|wx.CENTER, 5)
        
        self.SetSizer(layout)
        
        # Menubar
        menubar = wx.MenuBar()
        
        # Manage Menu
        manage_menu = wx.Menu()
        manage_item = manage_menu.Append(wx.ID_ANY, "Manage", "Manage Appointments")
        self.Bind(wx.EVT_MENU, self.on_manage_click, manage_item)
        
        menubar.Append(manage_menu, "Manage")
        
        self.main_frame.SetMenuBar(menubar)  # Set the menubar on the main frame directly

    def on_book_click(self, event):
        self.main_frame.open_or_select_tab("Book Appointments", BookAppointments)
    
    def on_see_click(self, event):
        wx.MessageBox("There's nothing to see here")
    
    def on_manage_click(self, event):
        pass

class AppointmentsModel(dv.PyDataViewModel):
    def __init__(self, data=None):
        super(AppointmentsModel, self).__init__()
        self.data = data or {}  # Assuming data is structured as { 'Month Year': { 'DD/MM/YYYY': [appointments] } }
        self.UseWeakRefs(False)

        self.itemMap = {}

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
    

    def initializeMapping(self):
        # Reset mapping
        self.itemMap.clear()

        # Example: Populate the mapping
        for month_year, dates in self.data.items():
            month_year_item = wx.dataview.DataViewItem()
            self.itemMap[month_year] = month_year_item
            for date, appointments in dates.items():
                date_item = wx.dataview.DataViewItem()
                self.itemMap[date] = date_item
                for appointment in appointments:
                    appointment_item = wx.dataview.DataViewItem()
                    self.itemMap[appointment['Rowid']] = appointment_item

        
    def getItemByRowid(self, rowid):
        item = self.itemMap.get(str(rowid))
        if item:
            return item
        return None


class BookAppointments(wx.Panel):
    def __init__(self, parent, main_frame):
        super(BookAppointments, self).__init__(parent)
        self.main_frame = main_frame
        self.currentRowid = None
        # Initialize the SplitterWindow
        splitter = wx.SplitterWindow(self)
        
        # Panel for the form fields (left)
        self.formPanel = wx.Panel(splitter)
        self.formPanel.SetBackgroundColour('#F0F0F0')
        self.setupFormFields(self.formPanel)
        
        # Panel for the DataViewCtrl (right)
        self.dvcPanel = wx.Panel(splitter)
        self.dvcPanel.SetBackgroundColour('light yellow')
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

        self.rowid = None
        self.clinicLastRowid = {}

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
                   "DATE", "TIME", "COMMENTS"]
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

            elif field == "DATE":
                input_field = wx.adv.DatePickerCtrl(parent, style=wx.adv.DP_DROPDOWN)
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
                input_field = wx.TextCtrl(parent, style=wx.TE_PROCESS_ENTER)
                self.entries[field] = input_field
                input_field.Bind(wx.EVT_TEXT_ENTER, self.main_frame.focus_next_widget)
                input_field.Bind(wx.EVT_TEXT, self.onTextChange)

            else:
                input_field = wx.TextCtrl(parent, style=wx.TE_PROCESS_ENTER)
                self.entries[field] = input_field
                input_field.Bind(wx.EVT_TEXT_ENTER, self.main_frame.focus_next_widget)

            input_field.SetFont(font)
            field_sizer.Add(input_field, 1, wx.ALL|wx.EXPAND, 5)
            main_sizer.Add(field_sizer, 0, wx.EXPAND)

        if field in ["CLINIC NUMBER", "FIRST NAME", "LAST NAME", "PHONE NUMBER"]:  
            input_field = wx.TextCtrl(parent, style=wx.TE_PROCESS_ENTER)#enter key setting
        # Setup for CLEAR and BOOK buttons arranged horizontally
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        clear_button = wx.Button(parent, label="CLEAR")
        search_button = wx.Button(parent, label="SEARCH")
        self.edit_button = wx.Button(parent, label="EDIT")
        self.book_button = wx.Button(parent, label="BOOK")

        clear_button.SetFont(font)
        search_button.SetFont(font)
        self.edit_button.SetFont(font)
        self.book_button.SetFont(font)

        button_sizer.Add(clear_button, 0, wx.ALL, 5)
        button_sizer.Add(search_button, 0, wx.ALL, 5) 
        button_sizer.Add(self.edit_button, 0, wx.ALL, 5)
        button_sizer.Add(self.book_button, 0, wx.ALL, 5)

        # Bind the buttons to their event handlers
        clear_button.Bind(wx.EVT_BUTTON, lambda evt: self.onClearClick(parent, evt))
        self.edit_button.Bind(wx.EVT_BUTTON, self.onEdit)
        self.book_button.Bind(wx.EVT_BUTTON, self.submitForm)

        self.edit_button.Disable()

        # Correct use of AddStretchSpacer
        main_sizer.AddStretchSpacer()
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER)
        parent.SetSizer(main_sizer)

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
        self.dvc.AppendTextColumn("COMMENTS", 9, width=100)
        self.dvc.AppendTextColumn("ROWID", 10, width = 100)
    

        # Layout for the DataViewCtrl panel
        dvcSizer = wx.BoxSizer(wx.VERTICAL)
        dvcSizer.Add(self.dvc, 1, wx.EXPAND | wx.ALL, 5)
        self.dvcPanel.SetSizer(dvcSizer)

    def prepareData(self):
        wx_date = self.entries['DATE'].GetValue()
        year = wx_date.GetYear()
        # wx.DateTime month is zero-based, so add 1
        month = wx_date.GetMonth() + 1
        day = wx_date.GetDay()
        # Convert to Python's datetime.date
        python_date = date(year, month, day)
        # ISO format

        self.iso_date = python_date.isoformat()  

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

            self.item_date = wx.DateTime()
            self.item_date.ParseISODate(self.item_data['Date'])

            self.entries['DATE'].SetValue(self.item_date)

            time_str = self.item_data['Time']  # The time string, e.g., "15:30" or "03:30 PM"
            time_dt = wx.DateTime()  # Create an empty wx.DateTime object

            # Parse the time string into the wx.DateTime object
            if time_dt.ParseTime(time_str):
                self.entries['TIME'].SetValue(time_dt)
                        
            self.entries['COMMENTS'].SetValue(self.item_data['Comments'])
            self.currentRowid = self.item_data['Rowid']

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
            if wx.MessageBox("Are you sure you want to delete this appointment?", "Confirm", wx.ICON_QUESTION | wx.YES_NO) != wx.YES:
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
                month_year = date_obj.strftime("%B %Y")  # Format as "Month Year", e.g., "March 2023"
                date_formatted = date_obj.strftime("%d/%m/%Y")  # Format date as "dd/mm/yyyy"
                
                # Check if the month_year is already a key in the data dictionary
                if month_year not in self.data:
                    self.data[month_year] = {}  # Initialize a new dict for this month_year if not present
                
                # Check if the date is already a key under the month_year
                if date_formatted not in self.data[month_year]:
                    self.data[month_year][date_formatted] = []  # Initialize a new list for this date if not present
                
                # Append a dictionary of the booking details to the list associated with the date under the month_year
                self.data[month_year][date_formatted].append({
                    'Clinic': clinic,
                    'ClinicNumber': clinic_number,
                    'FirstName': first_name,
                    'LastName': last_name,
                    'Gender': gender,
                    'PhoneNumber': phone_number,
                    'Date': date,
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

    def onClearClick(self, parent, event=None):  # Adjust the signature to include parent after event
        # Iterate through all children of the parent panel
        self.book_button.Enable()
        for child in parent.GetChildren():
            # Determine the type of each child and clear its value as appropriate
            if child == self.genderComboBox:
                child.SetSelection(-1)  # Reset combo box selection
            elif isinstance(child, wx.TextCtrl):
                child.SetValue('')  # Clear text fields

        clinic_focus = self.entries['CLINIC NUMBER']
        clinic_focus.SetFocus()

    def onEdit(self, event):
        clinic = self.entries['CLINIC'].GetValue()
        self.prepareData()

        data = {
                'clinic': clinic,
                'clinic_number': self.entries['CLINIC NUMBER'].GetValue().strip(),
                'first_name': self.entries['FIRST NAME'].GetValue().strip(),
                'last_name': self.entries['LAST NAME'].GetValue().strip(),
                'gender': self.entries['GENDER'].GetValue(),
                'phone_number': self.entries["PHONE NUMBER"].GetValue().strip(),
                'date': self.iso_date,
                'time': self.iso_time,
                'comments': self.entries['COMMENTS'].GetValue().strip(),
                'rowid': self.currentRowid
            }
        
        validation_result = self.validate_data(data)
        if validation_result is not None:
            dialog = wx.MessageDialog(self, validation_result, "Validation Error", wx.OK | wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()
            return
        
        current_clinic = self.item_data['Clinic']
        current_clinic_number = self.item_data['ClinicNumber']
        current_date = self.item_data['Date']

            # Connect to your SQLite database
        conn = sqlite3.connect('appointments.db')
        cursor = conn.cursor()
        if (self.item_data['Clinic'] != data['clinic'] or 
            self.item_data['ClinicNumber'] != data['clinic_number'] or
            self.item_date != data['date']):

               with conn:
                   cursor.execute(''' UPDATE bookings
                                  SET Clinic = :clinic,
                                    ClinicNumber= :clinic_number,
                                    Date= :date 
                                  WHERE Clinic = :current_clinic 
                                    AND ClinicNumber = :current_clinic_number 
                                    AND Date = :current_date ''',
                                  {'clinic': data['clinic'], 'clinic_number': data['clinic_number'],
                                    'date': data['date'], 'current_clinic': current_clinic, 
                                    'current_clinic_number': current_clinic_number,
                                    'current_date': current_date})
        
        
        if (self.item_data['FirstName'] != data['first_name'] or
            self.item_data['LastName'] != data['last_name'] or
            self.item_data['PhoneNumber'] != data['phone_number'] or
            self.item_data['Gender'] != data['gender'] or
            self.item_data['Time'] != data['time'] or
            self.item_data['Comments'] != data['comments']
            ):
        
            with conn:
                sql = '''UPDATE bookings
                        SET FirstName= :first_name,
                        LastName= :last_name,
                        PhoneNumber= :phone_number,
                        Gender= :gender, 
                        Time= :time,     
                        Comments= :comments
                    WHERE Clinic= :clinic AND ClinicNumber = :clinic_number
                    AND Date= :date
                        '''
                cursor.execute(sql, data)
       
        #self.on_clear_click
        message = "Appointment edited successfully!"
        # Show success message
        self.loadAppointments()
        self.updateModel(self.data)
        self.expandAllNodes()

        # Get the RowID of the newly updated item
        item = self.model.getItemByRowid(self.currentRowid)
        if item:
            self.dvc.Select(item)
            self.dvc.EnsureVisible(item)
            self.dvc.Refresh()

        self.main_frame.setStatus(message)

    
        conn.close()
        self.onClearClick(self.formPanel)
        self.book_button.Enable()
        self.edit_button.Disable()


    def submitForm(self, event):
        
        clinic = self.entries['CLINIC'].GetValue()
        self.prepareData()

        data = {
                'clinic': clinic,
                'clinic_number': self.entries['CLINIC NUMBER'].GetValue().strip(),
                'first_name': self.entries['FIRST NAME'].GetValue().strip(),
                'last_name': self.entries['LAST NAME'].GetValue().strip(),
                'gender': self.entries['GENDER'].GetValue(),
                'phone_number': self.entries["PHONE NUMBER"].GetValue().strip(),
                'date': self.iso_date,
                'time': self.iso_time,
                'comments': self.entries['COMMENTS'].GetValue().strip()
            }
            
        if (clinic, data['clinic_number'], data['date']):
            validation_result = self.validate_data(data)
            if validation_result is not None:
                dialog = wx.MessageDialog(self, validation_result, "Validation Error", wx.OK | wx.ICON_ERROR)
                dialog.ShowModal()
                dialog.Destroy()

                return
        
            # Connect to your SQLite database
            conn = sqlite3.connect('appointments.db')
            cursor = conn.cursor()

            try:
                with conn: # Using the connection as a context manager to auto-commit/rollback
                        sql = '''INSERT INTO bookings(Clinic, ClinicNumber, FirstName, LastName, PhoneNumber,
                                 Gender, Date, Time, Comments)
                                VALUES(:clinic, :clinic_number, :first_name, :last_name, :phone_number, :gender,
                                :date, :time, :comments)'''

        
                cursor.execute(sql, data)
                conn.commit() 
                
                message = "Successfully booked!"
                # Show success message
                self.loadAppointments()
                self.updateModel(self.data)
                self.expandAllNodes()


                self.rowid = cursor.lastrowid
                self.clinicLastRowid[clinic] = self.rowid
                self.item = self.model.getItemByRowid(self.rowid)
                if self.item.IsOk():
                    self.dvc.Select(self.item)
                    self.dvc.EnsureVisible(self.item)
                    self.dvc.Refresh()

                self.main_frame.setStatus(message)
                wx.MessageBox(f"TCA {data['date']}, {data['time']}, {data['clinic']}")

            except sqlite3.IntegrityError:
             wx.MessageBox("Failed to book: Appointment already exists!", "Error", wx.OK | wx.ICON_ERROR)
            finally:
                conn.close()

    
    def validate_data(self, data):
        self.data = data
        current_date = datetime.now().date() #date component only, ignore time as it considers only midnight as valid
        #since string date cannot be compared to a datetime object, convert
        input_date_str = self.data['date']
        input_date = datetime.strptime(input_date_str, '%Y-%m-%d').date()
    # Clinic Number: Must be an integer and not empty
        try:
            clinic_number = int(self.data['clinic_number'])
            if clinic_number < 1: 
                return "Clinic number must be a positive number."
        except ValueError:
            return "Clinic number cannot be empty!"

        # First Name and Last Name: Cannot be null (empty)
        if not self.data['first_name']:
            return "First name cannot be empty."
        if not self.data['last_name']:
            return "Last name cannot be empty."

        # Validation of phone numbers
        if not self.data['phone_number']:
            return "Supply patient's or next of kin's phone number."
        if not (self.data['phone_number'].isdigit()):
                return "Phone number must be 10 digits!"
        if not len(self.data['phone_number'])==10:
                return "Phone number must be 10 digits"

        if not (self.data['gender']):
            return "Patient's gender is required"

        # Clinic: Must also be filled
        if not self.data['clinic']:
            return "Clinic must be selected."

        if self.data['clinic'] == 'GOPC' and self.data['gender'] == 'Male':
            return "Male patients cannot be booked for GOPC!"
        
        if not self.data['date']:
            return "Appointment date must be selected"
        if input_date < current_date: #date component only, ignore time as it considers only midnight as valid
            return "You cannot book an appointment at a past date; please select a future one!"
        
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

   