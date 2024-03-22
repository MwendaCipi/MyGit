import wx
import wx.aui as aui
import wx.adv  # For wx.DatePickerCtrlqq
import sqlite3
from datetime import datetime
from datetime import date
import wx.dataview as dv
import wx.lib.agw.aui
import model

class BookAppointments(wx.Panel):
    def __init__(self, parent=None, main_frame=None):
        super(BookAppointments, self).__init__(parent)
        self.maxChars = 20
        self.main_frame = main_frame
        self.entries = {}

        # Initialize the SplitterWindow
        self.splitter = wx.SplitterWindow(self)

        # Panel for the form fields (left)
        self.formPanel = wx.Panel(self.splitter, style = wx.SUNKEN_BORDER)
        self.formPanel.SetBackgroundColour('#E7E7F7')
        #self.formPanel.SetBackgroundColour('#D7D7F7')
        self.setupFormFields(self.formPanel)
        
        # Panel for the DataViewCtrl (right)
        self.dvcPanel = wx.Panel(self.splitter, style = wx.SUNKEN_BORDER)
        self.dvcPanel.SetBackgroundColour('#C5C5C5')

        # Menubar
        menubar = wx.MenuBar()
        # Manage Menu
        manage_menu = wx.Menu()
         # Add a menu item for truncating the bookings table
        delete_item = manage_menu.Append(wx.ID_ANY, "Delete Bookings", "Empty the bookings table")
        self.main_frame.Bind(wx.EVT_MENU, self.onDeleteBookings, delete_item)

        menubar.Append(manage_menu, "Manage")
        self.main_frame.SetMenuBar(menubar)  # Set the menubar on the main frame directly

        self.dataViewCtrl()
        self.expandAllNodes()

        self.dvc.Bind(dv.EVT_DATAVIEW_ITEM_CONTEXT_MENU, self.onRightClick)
        self.dvc.Bind(dv.EVT_DATAVIEW_ITEM_ACTIVATED, self.onItemActivated)
    
        # Split the window vertically with the form on the left and tree view on the right
        self.splitter.SplitVertically(self.formPanel, self.dvcPanel)

        self.splitter.SetMinimumPaneSize(20)  # Minimum size of a pane
        
        # Layout management for the BookAppointments panel to include the splitter
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.splitter, 1, wx.EXPAND)
        self.SetSizer(sizer)

         # Bind the resize event of the frame to adjust the sash position
        self.Bind(wx.EVT_SIZE, self.adjustSashPosition)

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
        self.found_appointment = False
        self.cancel_booking = False

    def onDeleteBookings(self, event):
        dlg = wx.MessageDialog(self, "Are you sure you want to empty the bookings table? This cannot be undone.",
                            "Confirm Truncate", wx.YES_NO | wx.ICON_WARNING)
        
        if dlg.ShowModal() == wx.ID_YES:
            try:
                conn = sqlite3.connect('appointments.db')
                cursor = conn.cursor()
                
                # SQLite does not have a TRUNCATE TABLE command, so we use DELETE FROM
                cursor.execute("DELETE FROM bookings")
                conn.commit()
                self.dvc.Refresh()
                
                wx.MessageBox("The bookings table has been emptied.", "Success", wx.OK | wx.ICON_INFORMATION)
                self.dvc.Refresh()
                

            except sqlite3.Error as e:
                wx.MessageBox(f"Error emptying bookings table: {e}", "Error", wx.OK | wx.ICON_ERROR)
            finally:
                conn.close()
        dlg.Destroy()

    def adjustSashPosition(self, event):
        # Adjust the sash position to 1/3 of the frame's current width
        newSashPosition = int(self.GetSize().GetWidth() / 3)
        self.splitter.SetSashPosition(newSashPosition)
        
        # Important: Call the default event handler to ensure the window is resized properly
        event.Skip()

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
        fields = [("CLINIC", ["DOPC", "GOPC", "HOPC", "SOPC", "MOPC"]),
                  ("CLINIC NUMBER", []),
                  ("FIRST NAME", []),
                  ("LAST NAME", []),
                  ("PHONE NUMBER", []),
                  ("RESIDENCE", []),
                  ("DOB", []),
                  ("GENDER", ["Male", "Female", "Other"]),
                  ("DATE", []),
                  ("TIME", [])]

        font = wx.Font(12, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        # Group fields by rows
        rows = [fields[i:i + 2] for i in range(0, len(fields), 2)]
        
        for row in rows:
            row_sizer = wx.BoxSizer(wx.HORIZONTAL)
            for field, choices in row:
                field_sizer = wx.BoxSizer(wx.VERTICAL)
                label = wx.StaticText(parent, label=f"{field}:")
                label.SetFont(font)
                field_sizer.Add(label, 0, wx.ALL, 5)
                
                if choices:  # For ComboBoxes
                    input_field = wx.ComboBox(parent, choices=choices, style=wx.CB_READONLY)
                    if field == "CLINIC":
                        self.clinicComboBox = input_field  # Store in a separate variable
                        self.clinicComboBox.SetSelection(0)  # Set "DOPC" as default selection
                        self.clinicComboBox.Bind(wx.EVT_COMBOBOX, self.onClinicSelected)
                    elif field == "GENDER":
                        self.genderComboBox = input_field  # Store in a separate variable
                elif field == "CLINIC NUMBER":
                        input_field = wx.TextCtrl(parent)
                        self.entries[field] = input_field
                        input_field.Bind(wx.EVT_CHAR, self.onTypeChar)
                        self.clinic_number_field = input_field
                        self.clinic_number_field.Bind(wx.EVT_TEXT, self.onTypeClinicNumber)
                elif field == "FIRST NAME" or field == "LAST NAME" or field == "RESIDENCE":
                    input_field = wx.TextCtrl(parent)
                    self.entries[field] = input_field
                    input_field.Bind(wx.EVT_TEXT, self.onTextChange)
                    input_field.Bind(wx.EVT_TEXT, self.onTypeName)
                    first_name_field = input_field      
                elif field == "PHONE NUMBER":
                    input_field = wx.TextCtrl(parent)
                    input_field.Bind(wx.EVT_CHAR, self.onTypeChar)
                    self.entries[field] = input_field
                    self.phone_field = input_field
                    self.phone_field.Bind(wx.EVT_TEXT, self.onTypeDigit)
                elif field == "DOB":
                     input_field = wx.adv.DatePickerCtrl(parent, style=wx.adv.DP_DROPDOWN | wx.adv.DP_ALLOWNONE)
                elif field == "DATE":
                    input_field = wx.adv.DatePickerCtrl(parent, style=wx.adv.DP_DROPDOWN | wx.adv.DP_ALLOWNONE)
                elif field == "TIME":
                    input_field = wx.adv.TimePickerCtrl(parent)
                    # Set default time to 8:00:00
                    input_field.SetTime(8, 0, 0)
                    self.entries[field] = input_field
                else:
                    input_field = wx.TextCtrl(parent)
                
                input_field.SetFont(font)
                field_sizer.Add(input_field, 0, wx.ALL | wx.EXPAND, 5)
                row_sizer.Add(field_sizer, 1, wx.EXPAND)

                # Add the input field to the entries dictionary for later access
                self.entries[field] = input_field

            main_sizer.Add(row_sizer, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)

        intermediate_section = wx.Panel(parent)
        intermediate_section.SetBackgroundColour(wx.Colour(240, 240, 240))
        intermediate_section_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        intermediate_section = wx.Panel(parent)
        intermediate_section.SetBackgroundColour(wx.Colour(240, 240, 240))
        intermediate_section_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        intermediate_section_font = wx.Font(12, wx.FONTFAMILY_DECORATIVE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)

        # Patient Urgency Section with Label
        urgency_panel = wx.Panel(intermediate_section)
        urgency_sizer = wx.BoxSizer(wx.VERTICAL)
        urgency_label = wx.StaticText(urgency_panel, label="Patient urgency")
        urgency_label.SetFont(intermediate_section_font)  # Apply the font to the label
        urgency_sizer.Add(urgency_label, 0, wx.ALL | wx.LEFT, 5)
        self.urgency_radio_buttons = []  # Initialize an empty list to hold the radio buttons
        urgency_choices = ["Very urgent", "Urgent", "Moderate", "Low"]
        for choice in urgency_choices:
            radio_button = wx.RadioButton(urgency_panel, label=choice, style=wx.RB_GROUP if choice == "Very urgent" else 0)
            radio_button.SetFont(intermediate_section_font)  # Apply the font
            self.urgency_radio_buttons.append(radio_button)  # Add the radio button to the list
            urgency_sizer.Add(radio_button, 0, wx.ALL | wx.EXPAND, 10)
        urgency_panel.SetSizer(urgency_sizer)

            # TCA Section with Label
        tca_panel = wx.Panel(intermediate_section)
        tca_sizer = wx.BoxSizer(wx.VERTICAL)
        tca_label = wx.StaticText(tca_panel, label="TCA")
        tca_label.SetFont(font)  # Apply the font to the label
        tca_sizer.Add(tca_label, 0, wx.ALL | wx.LEFT, 5)

        tca_fields = ["Days", "Weeks", "Months"]
        max_label_width = 0
        labels = []
        spin_controls = []

        # Determine the maximum width needed for the labels
        for field in tca_fields:
            label = wx.StaticText(tca_panel, label=f"{field}:")
            label.SetFont(intermediate_section_font)  # Apply the font
            labels.append((label, field))  # Store both label and field name
            # Temporarily set label size for measurement
            label.SetSize(label.GetBestSize())
            max_label_width = max(max_label_width, label.GetSize().GetWidth())

        # Create the entries with aligned labels and SpinCtrls
        for label, field_name in labels:
            label.SetMinSize(wx.Size(max_label_width, -1))  # Ensure all labels have the same width for alignment

            # Initialize SpinCtrl based on field name
            if field_name == "Days":
                spin_ctrl = wx.SpinCtrl(tca_panel, min=0, max=7, initial=0)
            elif field_name == "Weeks":
                spin_ctrl = wx.SpinCtrl(tca_panel, min=0, max=52, initial = 0)
            elif field_name == "Months":
                spin_ctrl = wx.SpinCtrl(tca_panel, min=0, max=12, initial = 0)

            spin_ctrl.SetFont(intermediate_section_font)  # Apply the font to the SpinCtrl
            spin_controls.append(spin_ctrl)  # Store the spin control for potential future use

            horizontal_field_sizer = wx.BoxSizer(wx.HORIZONTAL)
            horizontal_field_sizer.Add(label, 0, wx.RIGHT, 8)  # Add some spacing to the right of the label
            horizontal_field_sizer.Add(spin_ctrl, 1, wx.EXPAND)

            tca_sizer.Add(horizontal_field_sizer, 0, wx.ALL | wx.EXPAND, 10)  # Increase vertical spacing for clarity

        tca_panel.SetSizer(tca_sizer)

        # Add both sections to the additional_section_sizer with a line for demarcation
        intermediate_section_sizer.Add(urgency_panel, 1, wx.ALL | wx.EXPAND, 5)
        
        # Vertical line for visual separation
        line = wx.StaticLine(intermediate_section, style=wx.LI_VERTICAL)
        intermediate_section_sizer.Add(line, 0, wx.ALL | wx.EXPAND, 5)
        
        intermediate_section_sizer.Add(tca_panel, 1, wx.ALL | wx.EXPAND, 5)
        
        intermediate_section.SetSizer(intermediate_section_sizer)


        main_sizer.Add(intermediate_section, 0, wx.ALL | wx.EXPAND, 5)

       # Setup for buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # Create each button and assign it to a class variable
        self.reset_button = wx.Button(parent, label="RESET")
        self.search_button = wx.Button(parent, label="SEARCH")
        self.edit_button = wx.Button(parent, label="EDIT")
        self.book_button = wx.Button(parent, label="BOOK")

        # Set the font for each button
        self.reset_button.SetFont(font)
        self.search_button.SetFont(font)
        self.edit_button.SetFont(font)
        self.book_button.SetFont(font)

        # Add each button to the button_sizer
        button_sizer.Add(self.reset_button, 0, wx.ALL, 5)
        button_sizer.Add(self.search_button, 0, wx.ALL, 5) 
        button_sizer.Add(self.edit_button, 0, wx.ALL, 5)
        button_sizer.Add(self.book_button, 0, wx.ALL, 5)

         # Bind the buttons to their event handlers
        self.reset_button.Bind(wx.EVT_BUTTON, lambda evt: self.onResetClick(parent, evt))
        self.edit_button.Bind(wx.EVT_BUTTON, self.onEditClick)
        self.book_button.Bind(wx.EVT_BUTTON, self.submitForm)
        self.search_button.Bind(wx.EVT_BUTTON, self.onSearchClick)

        # Add the button_sizer to the main_sizer
        main_sizer.Add(button_sizer, 0, wx.ALIGN_CENTER)


        parent.SetSizer(main_sizer)

    def getSelectedUrgency(self):
        for button in self.urgency_radio_buttons:
            if button.GetValue():  # If this radio button is selected
                return button.GetLabel()  # Return the label of the selected radio button
        return None  # Return None if no button is selected (should not happen if a group is correctly set up)

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
        self.model = model.AppointmentsModel(self.loadAppointments())
        self.dvc.AssociateModel(self.model)
        

        # Add columns to the DataViewCtrl
        self.dvc.AppendTextColumn("VISIT DATE", 0, width=100)
        self.dvc.AppendTextColumn("CLINIC", 1, width = 50)
        self.dvc.AppendTextColumn("CLINIC NUMBER", 2, width = 100)
        self.dvc.AppendTextColumn("FIRST NAME", 3, width = 100)
        self.dvc.AppendTextColumn("LAST NAME", 4, width=100)
        self.dvc.AppendTextColumn("PHONE NUMBER", 5, width = 100)
        self.dvc.AppendTextColumn("RESIDENCE", 6, width = 100)
        self.dvc.AppendTextColumn("AGE", 7, width = 70)
        self.dvc.AppendTextColumn("GENDER", 8, width = 100)
        self.dvc.AppendTextColumn("DATE", 9, width = 100)
        self.dvc.AppendTextColumn("TIME", 10, width = 100)
        self.dvc.AppendTextColumn("URGENCY", 11, width = 100)

        # Layout for the DataViewCtrl panel
        dvcSizer = wx.BoxSizer(wx.VERTICAL)
        dvcSizer.Add(self.dvc, 1, wx.EXPAND | wx.ALL, 5)
        self.dvcPanel.SetSizer(dvcSizer)

    def prepareData(self):
        wx_date = self.entries['DATE'].GetValue()
        wx_dob = self.entries['DOB'].GetValue()
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

        if wx_dob.IsValid():
            year = wx_dob.GetYear()
            # wx.DateTime month is zero-based, so add 1
            month = wx_dob.GetMonth() + 1
            day = wx_dob.GetDay()
            # Convert to Python's datetime.date
            python_dob = date(year, month, day)
            # ISO format

            self.iso_dob = python_dob.isoformat()
        else:
            self.iso_dob = None

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
        
        # Check if 'event' is the type that would have a 'GetItem' method
        # This assumes 'event' would be a wx.Event or similar when it's not a direct item
        if hasattr(event, 'GetItem'):
            item = event.GetItem()
            self.edit_button.Disable()
            self.book_button.Enable()
        else:
            # If 'event' itself is the item or 'event' doesn't have 'GetItem',
            # use 'event' directly as the item
            item = event
        if item.IsOk():
            self.item_data = self.model.GetItemData(item)  # Retrieve data for the selected item

            # Update form fields based on retrieved data
            self.entries['CLINIC NUMBER'].SetValue(str(self.item_data['ClinicNumber']))
            self.entries['CLINIC NUMBER'].SetInsertionPointEnd()

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

        add_appointment = menu.Append(wx.ID_ANY, 'Add appointment')
        edit_appointment = menu.Append(wx.ID_ANY, 'Edit appointment')
        delete_item = menu.Append(wx.ID_ANY, 'Delete appointment')
       
         # Bind the menu item selection events to methods
        self.Bind(wx.EVT_MENU, self.onDeleteItem, delete_item)
        self.Bind(wx.EVT_MENU, self.onAddAppointment, add_appointment)
        self.Bind(wx.EVT_MENU, self.onEditAppointment, edit_appointment)

        # Show the context menu at the position of the mouse cursor
        self.PopupMenu(menu)
        #cleanUp
        menu.Destroy()

    def onAddAppointment(self, event):
        item = self.dvc.GetSelection()
        self.edit_button.Disable()
        self.book_button.Enable()
        self.onItemActivated(item)

    def onEditAppointment(self, event):
        item = self.dvc.GetSelection()
        self.book_button.Disable()
        self.edit_button.Enable()
        self.onItemActivated(item)

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
        
                clinic = obj.get('Clinic')
                clinic_number = obj.get('ClinicNumber')
                date = obj.get('Date')

                if clinic and clinic_number and date:
                    date = datetime.strptime(date, "%d/%m/%Y")
                    date = date.strftime("%Y-%m-%d")  
                    try:
                        conn = sqlite3.connect('appointments.db')
                        cursor = conn.cursor()
                        # Delete the appointment from the database using its RowID
                        cursor.execute("DELETE FROM bookings WHERE Clinic = ? AND ClinicNumber = ? \
                                      AND Date = ?", (clinic, clinic_number, date))
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
                        FirstName, LastName, PhoneNumber, Residence, Dob, Gender, \
                        Date, Time, Urgency, ROWID as Rowid FROM bookings \
                           WHERE Date >= date('now') AND Clinic = \
                            :clinic ORDER BY Date", {'clinic': clinic})
            bookings = cursor.fetchall()
            
            for booking in bookings:
                clinic, clinic_number, first_name, last_name, phone_number, residence, dob, gender,\
                date, time, urgency, rowid = booking

                dob_date = datetime.strptime(dob, "%Y-%m-%d").date() 
                age = self.calculate_age(dob_date)

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
                    'PhoneNumber': phone_number,
                    'Residence': residence,
                    'Age': age,
                    'Gender': gender,
                    'Date': self.date_formatted,
                    'Time': time,
                    'Urgency': urgency,
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

    def calculate_age(self, dob):

        today = datetime.today().date()
        age_years = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        age_months = (today.year - dob.year) * 12 + today.month - dob.month
        if (today.day < dob.day):
            age_months -= 1
        age_days = (today - dob).days

        if age_years > 0:
            return f"{age_years} years"
        elif age_months > 0:
            return f"{age_months} months"
        else:
            return f"{age_days} days"
        

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

        #self.updateModel(self.data)
        self.edit_button.Disable()
        #self.expandAllNodes()
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
            query_parts = ["SELECT Clinic, ClinicNumber, FirstName, LastName, PhoneNumber, Gender, Date, Time, ROWID as Rowid FROM bookings"]
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
                        date, time, rowid = booking
                        
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
                            'Rowid': rowid
                        })

                    self.updateModel(self.search_data)
                    self.edit_button.Disable()
                    self.entries['CLINIC NUMBER'].SetFocus()
                    self.entries['CLINIC NUMBER'].SetInsertionPointEnd()
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
        selected_urgency = self.getSelectedUrgency()

        conn = sqlite3.connect('appointments.db')
        cursor = conn.cursor()

       
        data = {
                'clinic': self.entries['CLINIC'].GetValue(),
                'clinic_number': self.entries['CLINIC NUMBER'].GetValue().strip(),
                'first_name': self.entries['FIRST NAME'].GetValue().strip(),
                'last_name': self.entries['LAST NAME'].GetValue().strip(),
                'phone_number': self.entries["PHONE NUMBER"].GetValue().strip(),
                'residence': self.entries["RESIDENCE"].GetValue().strip(),
                'dob': self.iso_dob,
                'gender': self.entries['GENDER'].GetValue(),        
                'date': self.iso_date,
                'time': self.iso_time,
                'urgency': selected_urgency
            }
            
        with conn:
            cursor.execute("SELECT * FROM bookings")
            result = cursor.fetchone()

        if result:
            self.check_duplication(data)
            if self.found_appointment == True:
                return
        self.check_holiday()
        if self.cancel_booking == True:
            return
        validation_result = self.validate_booking(data)
        if validation_result is not None:
            dialog = wx.MessageDialog(self, validation_result, "Validation Error", wx.OK | wx.ICON_ERROR)
            dialog.ShowModal()
            dialog.Destroy()
            return 
        
        try:
            with conn: # Using the connection as a context manager to auto-commit/rollback
                    sql = '''INSERT INTO bookings(Clinic, ClinicNumber, FirstName, LastName, PhoneNumber,
                                                    Residence, Dob, Gender, Date, Time, Urgency)
                                        VALUES(:clinic, :clinic_number, :first_name, :last_name,
                                            :phone_number, :residence, :dob, :gender, :date, :time, :urgency)'''

            cursor.execute(sql, data)
            conn.commit() 
            
            message = "Successfully booked!"

            self.rowid = cursor.lastrowid
            self.clinicLastRowid[data['clinic']] = cursor.lastrowid

            #retrieve the newly added appointment using lastrowid
            sql_select = '''SELECT * FROM bookings WHERE rowid = ?'''
            cursor.execute(sql_select, (self.rowid,))
            appointment = cursor.fetchone()

            dob_date = datetime.strptime(appointment[6], "%Y-%m-%d").date() 
            age = self.calculate_age(dob_date)

            appointment_dict = {
                'Clinic': appointment[0], 
                'ClinicNumber': appointment[1], 
                'FirstName': appointment[2], 
                'LastName': appointment[3], 
                'PhoneNumber': appointment[4],
                'Residence': appointment[5],
                'Age': age, 
                'Gender': appointment[7], 
                'Date': appointment[8], 
                'Time': appointment[9],
                'Urgency': appointment[10]}

            if appointment_dict:

                self.model.addToDataviewctrl(appointment_dict, self.dvc)

            
            self.expandAllNodes()

            self.main_frame.setStatus(message)
            #wx.MessageBox(f"TCA {data['date']}, {data['time']}, {data['clinic']}")
            self.onResetClick(self.formPanel)

        except sqlite3.IntegrityError:
            wx.MessageBox("Failed to book: The patient already has an appointment on the selected date!", "Error", wx.OK | wx.ICON_ERROR)
            return
        finally:
            conn.close()
        self.entries['CLINIC NUMBER'].SetFocus()


    def validate_booking(self, data):
        validation_data = data
        current_date = datetime.now().date() #date component only, ignore time as it considers only midnight as valid
        #since string date cannot be compared to a datetime object, convert
        input_date_str = validation_data['date']
        input_dob_str = validation_data['dob']

        if input_date_str != None:
            input_date = datetime.strptime(input_date_str, '%Y-%m-%d').date()

        if input_dob_str != None:
            input_dob = datetime.strptime(input_dob_str, '%Y-%m-%d').date()
    
        try:
            clinic_number = int(validation_data['clinic_number'])
            if clinic_number < 0: 
                self.entries['CLINIC NUMBER'].SetFocus()
                return "Clinic number must be a positive number!"
        except ValueError:
            self.entries['CLINIC NUMBER'].SetFocus()
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
        
        if validation_data['date']  == None:
            self.entries['DATE'].SetFocus()
            return "Appointment date must be selected"
        if input_date < current_date: #date component only, ignore time as it considers only midnight as valid
            return "You cannot book an appointment on a past date; please select a current or future one!"
        
        if input_dob > current_date:
            return "Please enter a valid date of birth that is not in the future"
          
        # If all validations pass
        return None
    
    def check_holiday(self):
        self.cancel_booking = False
        selected_date = self.entries['DATE'].GetValue()
        if selected_date.IsValid():
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
                    self.cancel_booking = True
                    
        
    def check_duplication(self, data):
        self.found_appointment = False
        data = data
        message = 'Right-click on the highlighted appointment and select "Edit appointment"'
        duration = 5000
        colour = wx.BLUE
        # Traverse through the month-year and date hierarchy
        for month_year, dates in self.data.items():
            for date, appointments in dates.items():
                for appointment in appointments:
                    if (appointment['Clinic'] == data['clinic'] and 
                        appointment['ClinicNumber'] == data['clinic_number']):
                        # Found a conflicting appointment
        
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
                                item = self.model.getItemByRowid(this_rowid)
                                self.main_frame.setStatus(message, duration, colour)
                                self.onResetClick(self.formPanel)
                                self.dvc.EnsureVisible(item)
                                self.dvc.Select(item)
                                self.edit_button.Enable()
                                self.book_button.Disable()
                                self.onItemActivated(item) 
                                self.found_appointment = True

                            return

                        else:
                            self.entries['CLINIC'].SetFocus()
                            self.found_appointment = False
                            wx.MessageBox("The appointment could not be booked because another one was found")
                            self.onResetClick(self.formPanel)
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
        