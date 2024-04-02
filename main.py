from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

# Function to get a database connection
def get_db_connection():
    conn = sqlite3.connect('ecommerce.db')
    conn.row_factory = sqlite3.Row
    return conn

# Function to create tables and insert limited sample data
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS Users (
                        ID INTEGER PRIMARY KEY,
                        Name TEXT,
                        Email TEXT UNIQUE,
                        HashedPassword TEXT,
                        Address TEXT
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS Products (
                        ProductID INTEGER PRIMARY KEY,
                        Name TEXT,
                        Description TEXT,
                        Price REAL,
                        Stock INTEGER,
                        EcoCertification TEXT,
                        VendorID INTEGER
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS Orders (
                        OrderID INTEGER PRIMARY KEY,
                        Date DATE,
                        TotalPrice REAL,
                        ShippingStatus TEXT
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS OrderDetails (
                        OrderID INTEGER,
                        ProductID INTEGER,
                        Quantity INTEGER,
                        FOREIGN KEY (OrderID) REFERENCES Orders(OrderID),
                        FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
                    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS Ratings_Reviews (
                        ReviewID INTEGER PRIMARY KEY,
                        Rating INTEGER,
                        Comment TEXT,
                        DatePosted DATE
                    )''')

    # Check if the Products table is empty
    cursor.execute("SELECT COUNT(*) FROM Products")
    row = cursor.fetchone()
    if row[0] == 0:  # If the Products table is empty, insert sample data
        # Sample data insertion
        cursor.execute('''INSERT OR IGNORE INTO Users (ID, Name, Email, HashedPassword, Address)
                          VALUES (1, 'Green Eco Supplies', 'contact@greenecosupplies.com', 'hashed_password', '123 Green Street')''')

        cursor.execute('''INSERT INTO Products (Name, Description, Price, Stock, EcoCertification, VendorID)
                          VALUES ('Organic Cotton T-Shirt', 'Made from 100% organic cotton', 19.99, 50, 'GOTS', 1)''')

        cursor.execute('''INSERT INTO Products (Name, Description, Price, Stock, EcoCertification, VendorID)
                          VALUES ('Bamboo Toothbrush', 'Biodegradable bamboo handle', 5.99, 100, 'FSC', 1)''')

        cursor.execute('''INSERT INTO Products (Name, Description, Price, Stock, EcoCertification, VendorID)
                          VALUES ('Recycled Paper Notebook', 'Eco-friendly notebook made from recycled paper', 7.99, 80, 'FSC', 1)''')

        cursor.execute('''INSERT INTO Products (Name, Description, Price, Stock, EcoCertification, VendorID)
                          VALUES ('Reusable Stainless Steel Water Bottle', 'Durable water bottle made from stainless steel', 14.99, 120, 'ISO 14001', 1)''')

        cursor.execute('''INSERT INTO Products (Name, Description, Price, Stock, EcoCertification, VendorID)
                          VALUES ('Recycled Glass Jar Candle', 'Hand-poured candle in a recycled glass jar', 9.99, 60, 'FSC', 1)''')

    conn.commit()
    conn.close()

# Route to display limited number of distinct products
@app.route('/')
def index():
    conn = get_db_connection()
    # Join query to fetch distinct products along with their vendor information (limited to 5 products)
    products = conn.execute('''SELECT DISTINCT Products.*, Users.Name AS VendorName
                               FROM Products
                               INNER JOIN Users ON Products.VendorID = Users.ID
                               WHERE Products.EcoCertification IS NOT NULL
                               GROUP BY Products.Name
                               LIMIT 5''').fetchall()
    conn.close()
    return render_template('index.html', products=products)


# Route to display checkout page
@app.route('/checkout')
def checkout():
    # Retrieve selected product IDs from the query parameters
    selected_product_ids = request.args.getlist('product_id')
    conn = get_db_connection()
    selected_products = []
    for product_id in selected_product_ids:
        # Fetch product details for each selected product
        product = conn.execute('SELECT * FROM Products WHERE ProductID = ?', (product_id,)).fetchone()
        if product:
            selected_products.append(product)
    conn.close()
    return render_template('checkout.html', products=selected_products)

# Route to process the order
@app.route('/process_order', methods=['POST'])
def process_order():
    # Retrieve form data
    name = request.form['name']
    email = request.form['email']
    address = request.form['address']
    product_id = request.form.getlist('product_id')  # Get list of selected product IDs

    # Calculate total price based on the selected products
    conn = get_db_connection()
    total_price = 0.0
    for pid in product_id:
        product = conn.execute('SELECT Price FROM Products WHERE ProductID = ?', (pid,)).fetchone()
        if product:
            total_price += product['Price']
        else:
            # Product not found, handle error or ignore
            pass

    # Insert order into the Orders table
    cursor = conn.cursor()
    cursor.execute('INSERT INTO Orders (Date, TotalPrice, ShippingStatus) VALUES (CURRENT_TIMESTAMP, ?, ?)',
                   (total_price, 'Pending'))

    order_id = cursor.lastrowid  # Get the ID of the inserted order

    # Insert order details into the OrderDetails table
    for pid in product_id:
        cursor.execute('INSERT INTO OrderDetails (OrderID, ProductID, Quantity) VALUES (?, ?, 1)', (order_id, pid))

    conn.commit()
    conn.close()

    # Process the order (e.g., send confirmation email, etc.)
    # For simplicity, let's just print the order details
    print(f"Order received from {name} ({email}) for shipping to {address}")
    print("Selected Products:", product_id)

    # Redirect to a thank you page or home page
    return render_template('thank_you.html')

# Run the app
if __name__ == '__main__':
    create_tables()
    app.run(debug=True)
