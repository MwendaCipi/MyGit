import sqlite3
#creating the database
conn = sqlite3.connect('appointments.db')

# Create a cursor object using the connection
mycursor = conn.cursor()

#mycursor.execute('drop table bookings')
#print("dropped")

#Create the Appointments table

mycursor.execute("""
                 CREATE TABLE IF NOT EXISTS bookings(
                 Clinic TEXT NOT NULL,
                 ClinicNumber TEXT NOT NULL,
                 FirstName TEXT NOT NULL, 
                 LastName TEXT NOT NULL,
                 PhoneNumber TEXT NOT NULL,
                 Residence TEXT,
                 Dob Date NOT NULL,
                 Gender TEXT NOT NULL,
                 Date DATE NOT NULL,
                 Time TIME NOT NULL,
                 Urgency TEXT NOT NULL,
                 PRIMARY KEY (ClinicNumber, Clinic, Date)
                 )
""")

mycursor.execute("""
    CREATE TABLE IF NOT EXISTS users(username VARCHAR NOT NULL, email TEXT NOT NULL PRIMARY KEY,
                 password TEXT NOT NULL, IsAdmin BOOLEAN NOT NULL CHECK(IsAdmin IN(0, 1)))
                 """)

"""mysql='SELECT * FROM users'
mycursor.execute(mysql)
result = mycursor.fetchall()
print(result)""" 

mycursor.execute("""
    CREATE TABLE IF NOT EXISTS history(
                 Clinic TEXT NOT NULL,
                 ClinicNumber TEXT NOT NULL,
                 FirstName TEXT NOT NULL, 
                 LastName TEXT NOT NULL,
                 PhoneNumber TEXT NOT NULL,
                 Gender TEXT,
                 Date DATE NOT NULL,
                 Time TIME NOT NULL,
                 Attendance BOOLEAN NOT NULL CHECK (Attendance IN(0, 1)),
                 Seen BOOLEAN NOT NULL CHECK(Seen IN(0, 1)),
                 COMMENTS TEXT,
                 PRIMARY KEY (ClinicNumber, Date, Clinic)
                    )


""")

# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database and tables created successfully.")

