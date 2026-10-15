"""Optional demo data for matching the dashboard reference screenshot.
Run after extracting the project with: py seed_demo.py
This script only seeds an empty database; it will not duplicate existing data.
"""
import app

with app.db() as con:
    existing = con.execute('SELECT COUNT(*) FROM vehicles').fetchone()[0]
    if existing:
        print('Demo data was not added because vehicles already exist. Use an empty database to seed demo data.')
    else:
        vehicles = [
            ('MH12AB1001','Tata Starbus',40,'Available'),
            ('MH12AB1002','Ashok Leyland Viking',45,'Available'),
            ('MH12AB1003','Force Traveller',17,'In Service'),
            ('MH12AB1004','Eicher Skyline',32,'Available'),
            ('MH12AB1005','Tata Winger',12,'Maintenance'),
            ('MH12AB1006','Mahindra Bolero Pickup',2,'Available'),
            ('MH12AB1007','Tata Ultra',20,'Available'),
            ('MH12AB1008','Eicher Pro',25,'Available'),
            ('MH12AB1009','BharatBenz 1017',30,'In Service'),
            ('MH12AB1010','Force Urbania',13,'Available'),
            ('MH12AB1011','Tata 407',14,'Available'),
            ('MH12AB1012','Ashok Leyland Dost',2,'Available'),
        ]
        con.executemany('INSERT INTO vehicles(registration_no,model,capacity,status) VALUES (?,?,?,?)', vehicles)
        drivers = [
            ('John Doe','9876500001','DL-MH-10001','On Trip'),
            ('Mary Smith','9876500002','DL-MH-10002','Available'),
            ('Michael Brown','9876500003','DL-MH-10003','Available'),
            ('Priya Sharma','9876500004','DL-MH-10004','Available'),
            ('Rahul Patil','9876500005','DL-MH-10005','On Trip'),
        ]
        con.executemany('INSERT INTO drivers(name,phone,license_no,status) VALUES (?,?,?,?)', drivers)
        routes = [
            (1,1,'New York','Washington D.C.','Ongoing'),
            (2,2,'Chicago','Los Angeles','Completed'),
            (3,3,'Dallas','Houston','Completed'),
            (4,4,'Pune','Mumbai','Completed'),
            (5,5,'Nashik','Pune','Ongoing'),
            (6,1,'Mumbai','Goa','Completed'),
            (7,2,'Nagpur','Pune','Completed'),
            (8,3,'Delhi','Jaipur','Completed'),
            (9,4,'Surat','Ahmedabad','Completed'),
            (10,5,'Pune','Kolhapur','Completed'),
            (11,1,'Bengaluru','Mysuru','Completed'),
            (12,2,'Chennai','Puducherry','Completed'),
            (1,3,'Hyderabad','Vijayawada','Completed'),
            (2,4,'Indore','Bhopal','Completed'),
            (3,5,'Kolkata','Durgapur','Completed'),
            (4,1,'Aurangabad','Pune','Ongoing'),
            (5,2,'Thane','Mumbai','Completed'),
            (6,3,'Panaji','Belgaum','Completed'),
            (7,4,'Vadodara','Surat','Completed'),
            (8,5,'Noida','Agra','Completed'),
        ]
        con.executemany('''INSERT INTO trips(vehicle_id,driver_id,start_location,end_location,trip_date,status)
                           VALUES (?,?,?,?,date('now'),?)''', routes)
        print('Demo data added: 12 vehicles, 5 drivers, 3 ongoing trips and 17 completed trips.')
