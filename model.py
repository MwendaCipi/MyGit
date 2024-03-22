import wx
import wx.aui as aui
import wx.adv  # For wx.DatePickerCtrl
import wx.lib.mixins.listctrl  # For CheckListCtrlMixin, if needed
import sqlite3
from datetime import datetime
from datetime import date
import wx.dataview as dv
import wx.lib.agw.aui

class AppointmentsModel(dv.PyDataViewModel):
    def __init__(self, data=None):
        super(AppointmentsModel, self).__init__()
        self.data = data or {}  # data is structured as { 'Month Year': { 'DD/MM/YYYY': [appointments] } }
        self.UseWeakRefs(False)

        self.itemMap = {}  # Maps Python objects to DataViewItem IDs and back
        self.nextID = 1  # Start with an ID of 1 for the first item

    def setData(self, data):
        self.data = data
        self.Cleared()
    
    def GetColumnCount(self):
        return 13

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
                return str(obj.get('Residence', ''))
            elif col == 7:
                return str(obj.get('Age', ''))
            elif col == 8:
                return str(obj.get('Gender', ''))
            elif col == 9:
                return str(obj.get('Date', ''))
            elif col == 10:
                return str(obj.get('Time', ''))
            elif col == 11:
                return str(obj.get('Urgency', ''))
            elif col == 12:
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

    def addToDataviewctrl(self, appointment, dvc):
        self.dvc = dvc
        date_str = appointment['Date']  # 'YYYY-MM-DD' format
        date_formatted = self.convert_yyyy_mm_dd_to_dd_mm_yyyy(date_str)
        month_year = datetime.strptime(date_str, "%Y-%m-%d").strftime("%B %Y")
        
            # Ensure the month_year exists in the model
        if month_year not in self.data:
            self.data[month_year] = {}  # If not, initialize it
            # Since this is a new month_year, no need to check for date existence, directly add it
            self.data[month_year][date_formatted] = [appointment]
            # Convert 'None' to a model item for the root of the hierarchy
            month_year_item = self.ObjectToItem(month_year)
            # Notify the DataViewCtrl that a new parent item has been added
            self.ItemAdded(dv.NullDataViewItem, month_year_item)
        else:
            # The month_year exists, check for the specific date
            if date_formatted not in self.data[month_year]:
                self.data[month_year][date_formatted] = [appointment]  # Initialize the date list
                # Convert the month_year to a model item
                month_year_item = self.ObjectToItem(month_year)
                # Since this is a new date, notify the DataViewCtrl that a new child item has been added under the month_year
                date_item = self.ObjectToItem(date_formatted)
                self.ItemAdded(month_year_item, date_item)
            else:
                # Both month_year and date exist, add the appointment to the existing list
                self.data[month_year][date_formatted].append(appointment)
                # In this case, you might want to update or refresh the specific entry without needing to call ItemAdded
                # This could involve refreshing the view or using a more specific method to update the item if necessary
            
            self.Cleared()
            