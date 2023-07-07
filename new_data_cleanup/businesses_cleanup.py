import pandas as pd

FILENAME = '../original_data/business-licences.csv'

print("Loading Data")
licences = pd.read_csv(FILENAME, delimiter=';')
print(f"Starting Data: {licences.shape[0]}")

# Keep only issued licences
licences = licences[licences['Status'] == 'Issued']
print(f"Removed unissued licences: {licences.shape[0]}")

# Keep only licences in the city of vancouver
licences = licences[licences['City'] == 'Vancouver']
print(f"Removed businesses outside Vancouver: {licences.shape[0]}")

# Keep licences with location information
licences = licences[licences['geo_point_2d'].notna()]
print(f"Removed businesses without a location: {licences.shape[0]}")

# Remove licences without issued date information
licences = licences[licences['IssuedDate'].notna()]
print(f"Removed licences without an issue date: {licences.shape[0]}")

# Convert the IssuedDate to datetime type
dates = pd.to_datetime(licences['IssuedDate'])
licences.loc[:, 'IssuedDate'] = dates

# Remove duplicate records
duplicate_columns = ['BusinessName', 'BusinessTradeName', 'BusinessType', 'BusinessSubType', 'Street', 'LocalArea', 'geo_point_2d']
licences.sort_values('IssuedDate', ascending=False, inplace=True)
licences.drop_duplicates(subset=duplicate_columns, keep='first', inplace=True)
print(f"Removed duplicates: {licences.shape[0]}")

# Set the expiry date to the end of the issued year if null
licences.loc[:, 'ExpiredDate'] = pd.to_datetime(licences['ExpiredDate'], errors='coerce')
last_day_of_year = licences['IssuedDate'].apply(lambda x: pd.Timestamp(year=x.year, month=12, day=31)) 
licences.loc[:, 'ExpiredDate'].fillna(last_day_of_year, inplace=True)

# Remove any licences expired before 2021
licences = licences[licences['ExpiredDate'] > pd.Timestamp(year=2020, month=12, day=31)]
print(f"Removed expired licences: {licences.shape[0]}")

# Only keep licences that have a commercial type
ctypes = [
    'Bingo Hall', 'Motel', 'Auctioneer', 'Piano Tuner', 'Steam Bath', 'Liquor Delivery Services', 'Livery & Feed Stables', 
    'Model Agency', 'Carpet/Upholstery Cleaner', 'Horse Racing', 'Public Market Operator-Annual', 'Equipment Operator', 
    'Lumber Yard', 'Social Escort Services', 'Plumber & Sprinkler Contractor', 'Amusement Park', 'Machinery Dealer', 
    'Wholesale Dealer - Food with Anc. Retail', 'Auto Wholesaler', 'Dating Services', 'Window Cleaner', 'Bowling Alley', 
    'Sheet Metal Works', 'Christmas Tree Lot', 'Casino', 'Junk Dealer', 'Live-aboards', 'Power/ Pressure Washing', 
    'Family Sports & Entertain Ctr', 'Pest Control/Exterminator', 'Psychic/Fortune Teller', 'Sprinkler Contractor', 
    'Soliciting For Charity', 'U-Brew/U-Vin', 'Plumber Sprinkler & Gas Contractor', 'Booking Agency', 'Arcade', 'Pawnbroker', 
    'Warehouse Operator - Food', 'Billiard Room Keeper', 'Scavenging', 'Roofer', 'Private Hospital', 'Tanning Salon', 
    'Entertainment Centre', 'Funeral Services', 'Dance Hall', 'Laundry (w/equipment)', 'Retail Dealer - Market Outlet', 
    'Plumber', 'Adult Entertainment Store', 'Marina Operator', 'Marine Services', 'Business Services', 'Pet Store', 
    'Photo Services', 'Locksmith', 'Gas Contractor', 'Product Assembly', 'Recycling Depot', 'Auto Washer', 'Painter', 
    'Photographer', 'Assembly Hall', 'Boat Charter Services', 'Laundry Depot', 'Talent Agency', 'Rooming House', 
    'Electrical-Security Alarm Installation', 'Landscape Gardener', 'Boot & Shoe Repairs', 'Wholesale Dealer w/ Anc. Retail', 
    'Theatre', 'Restaurant Class 2', 'Food Processing', 'Plumber & Gas Contractor', 'Manufacturer with Anc. Retail', 
    'Auto Detailing', 'Venue', 'Manufacturer - Food with Anc. Retail', 'Animal Clinic/Hospital', 'Club', 
    'Moving/Transfer Service', 'Laundry-Coin Operated Services', 'Janitorial Services', 'Bed and Breakfast', 
    'Entertainment Services', 'Seamstress/Tailor', 'Dry Cleaner', 'ESL Instruction', 'Electrical Contractor', 
    'Postal Rental Agency', 'Auto Painter & Body Shop', 'Temp Liquor Licence Amendment', 'Warehouse Operator', 
    'Gasoline Station', 'Jeweller', 'Animal Services', 'Personal Services', 'Tattoo Parlour', 
    'Liquor Establishment Standard', 'Retail Dealer - Grocery', 'Exhibitions/Shows/Concerts', 'Laboratory', 
    'Printing Services', 'Beauty Services', 'Money Services', 'Hotel', 'Liquor Retail Store', 'Employment Agency', 
    'Liquor Establishment Extended', 'Auto Dealer', 'Wholesale Dealer - Food', 'Secondhand Dealer', 
    'Referral Services', 'Contractor - Special Trades', 'Travel Agent', 'Studio', 'Repair/ Service/Maintenance', 
    'Financial Institution', 'Fitness Centre', 'Caterer', 'Instruction', 'Production Company', 'Auto Repairs', 
    'Residential/Commercial', 'Cosmetologist', 'Manufacturer - Food', 'Real Estate Dealer', 'Manufacturer', 
    'Physical Therapist', 'Contractor', 'Auto Parking Lot/Parkade', 'Community Association', 'Wholesale  Dealer', 
    'Massage Therapist', 'Computer Services', 'Retail Dealer - Food', 'Health and Beauty', 'Financial Services', 
    'Ltd Service Food Establishment', 'Restaurant Class 1', 'Retail Dealer', 'Health Services'
]
licences = licences[licences['BusinessType'].isin(ctypes)]
print(f"Removed non-commercial businesses: {licences.shape[0]}")

# Give licences a tag indicating whether they are retail type
retailTypes = ['Wholesale Dealer - Food with Anc. Retail', 'Retail Dealer - Market Outlet', 'Wholesale Dealer w/ Anc. Retail', 'Manufacturer with Anc. Retail', 'Manufacturer - Food with Anc. Retail', 'Retail Dealer - Grocery', 'Liquor Retail Store', 'Wholesale Dealer - Food', 'Wholesale  Dealer', 'Retail Dealer - Food', 'Retail Dealer', 'Ltd Service Food Establishment']
licences['retail'] = licences['BusinessType'].isin(retailTypes)
licences = licences[licences['retail']]
print(f"Removed non-retail businesses: {licences.shape[0]}")

licences['latitude'] = licences['geo_point_2d'].apply(lambda p: float(p.split(',')[0]))
licences['longitude'] = licences['geo_point_2d'].apply(lambda p: float(p.split(',')[1]))

licences.drop('FOLDERYEAR', inplace=True, axis=1)
licences.drop('LicenceRevisionNumber', inplace=True, axis=1)
licences.drop('Status', inplace=True, axis=1)
licences.drop('Unit', inplace=True, axis=1)
licences.drop('UnitType', inplace=True, axis=1)
licences.drop('City', inplace=True, axis=1)
licences.drop('Province', inplace=True, axis=1)
licences.drop('Country', inplace=True, axis=1)
licences.drop('FeePaid', inplace=True, axis=1)
licences.drop('ExtractDate', inplace=True, axis=1)
licences.drop('Geom', inplace=True, axis=1)
licences.drop('geo_point_2d', inplace=True, axis=1)

licences.rename(columns={
    'LicenceRSN': 'licence_rsn',
    'LicenceNumber': 'licence_number',
    'BusinessName': 'name',
    'BusinessTradeName': 'trade_name',
    'BusinessSubType': 'sub_type',
    'NumberofEmployees': 'employees_count',
    'IssuedDate': 'issued_date',
    'ExpiredDate': 'expired_date',
    'BusinessType': 'business_type',
    'House': 'house',
    'Street': 'street',
    'PostalCode': 'postal_code',
    'LocalArea': 'local_area',
    'NumberOfEmployees': 'number_of_employees',
}, inplace=True)

licences.reset_index(inplace=True, drop=True)
licences.index.name = "id"

print(f"Final count: {licences.shape[0]}")

licences.to_csv('../temp/businesses.csv')