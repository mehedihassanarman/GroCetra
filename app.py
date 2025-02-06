from flask import Flask, jsonify, render_template, request,redirect, url_for, session,send_file
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patheffects import withStroke
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.cm as cm
import io
import base64
import os
from PIL import Image, ImageDraw, ImageFont
import qrcode
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management

# Load required datasets for the App
USER_EXCEL_FILE = 'Datasets/User_Information/User_data.xlsx'
PURCHASE_HISTORY_EXCEL_FILE='Datasets/Purchase_History/Purchase_History.xlsx'
FULL_ITEM_INFO_EXCEL_FILE = 'Static/Files/Full_Item_Info.xlsx'
WEB_SCRAPING_EXCEL_FILE = 'Datasets/Web_Scraping/Web_Scraping.xlsx'  
data = pd.read_excel(FULL_ITEM_INFO_EXCEL_FILE, sheet_name='Sheet1')

# Create the user database with the required columns if it does not exist
os.makedirs(os.path.dirname(USER_EXCEL_FILE), exist_ok=True)

if not os.path.exists(USER_EXCEL_FILE):
    columns = [
        'Customer_ID', 'FirstName', 'LastName', 'Gender', 'DateOfBirth',
        'Country', 'City', 'Address', 'Email', 'Username', 'Password', 'Points','Image'
    ]
    df = pd.DataFrame(columns=columns)
    df.to_excel(USER_EXCEL_FILE, index=False)


# Convert Item's informaion to a dictionary for easy access
items = data.to_dict(orient='records')

# Initiate an empty cart
cart_items = []

# Function to generate the chart for the variable price across different supermarket
def generate_chart_inline(total_prices):
    supermarkets = list(total_prices.keys())
    prices = list(total_prices.values())

    plt.figure(figsize=(10, 6))
    bars = plt.bar(supermarkets, prices, color=['#6c3483', '#2980b9', '#27ae60', '#f39c12', '#e74c3c'])

    for bar, price in zip(bars, prices):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1, f"€{price:.2f}", ha='center', fontsize=10)


    plt.ylabel('Total Price (€)', fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    # Convert the plot to a base64-encoded image
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()

    return plot_url


# Default route for the App
@app.route('/')
def login_page():
    return render_template('login.html')


# Route for Login Page
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username').strip()  # Remove extra spaces
    password = data.get('password').strip()  # Remove extra spaces

    print(f"Login attempt: Username={username}, Password={password}")  # Debug: Print login attempt

    if os.path.exists(USER_EXCEL_FILE):
        user_data = pd.read_excel(USER_EXCEL_FILE)

        # To ensure Username and Password columns are strings and strip any extra whitespace
        user_data['Username'] = user_data['Username'].astype(str).str.strip()
        user_data['Password'] = user_data['Password'].astype(str).str.strip()

        # To validate username and password
        user = user_data[(user_data['Username'] == username) & (user_data['Password'] == password)]

        if not user.empty:
            session['user'] = user.iloc[0].to_dict()
            print(f"Login successful for user: {username}")  # Debug: Print successful login
            return jsonify({'success': True, 'message': 'Login successful! '})

        print(f"Invalid login attempt for Username: {username}, Password: {password}")  # Debug: Print failed login
        return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

    print("User database not found.")  # Debug: File not found
    return jsonify({'success': False, 'message': 'User database was not found'}), 500


# Route for Home Page
@app.route('/home')
def home():
    if 'user' in session:
        return render_template('home.html', user=session['user'])
    return redirect(url_for('login_page'))

# Logout Action
@app.route('/logout')
def logout():
    session.pop('user', None)
 
    return redirect(url_for('login_page'))


# Route for Signup Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        # Extract form data
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        gender = request.form.get('gender')
        dob = request.form.get('dob')
        country = request.form.get('country')
        city = request.form.get('city')
        address = request.form.get('address')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')

        # Load existing user data
        df = pd.read_excel(USER_EXCEL_FILE)

        # Check for duplicate email or username
        if email in df['Email'].values:
            return jsonify({'success': False, 'message': 'Email already taken!'}), 400
        if username in df['Username'].values:
            return jsonify({'success': False, 'message': 'Username already taken!'}), 400

        # Generate new Customer_ID
        customer_id = df['Customer_ID'].max() + 1 if not df.empty else 48561001

        # Geberate QR Code for new customer
        qr_data = f"https://www.example.com\nGroCetra\nCustomer ID : {customer_id}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)

        qr_image = qr.make_image(fill_color="black", back_color="white").convert("RGB")

        # Add text below the QR code
        width, height = qr_image.size
        new_height = height + 150  # Increase height for text
        img_with_text = Image.new("RGB", (width, new_height), "white")
        img_with_text.paste(qr_image, (0, 0))

        draw = ImageDraw.Draw(img_with_text)
        font = ImageFont.truetype("arial.ttf", size=20)
        text = f"GroCetra\nCustomer ID: {customer_id}"

        # Calculate text size using textbbox()
        text_bbox = draw.multiline_textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]  # Text width
        text_height = text_bbox[3] - text_bbox[1]  # Text height

        # Center the text below the QR code
        text_x = (width - text_width) // 2
        text_y = height + 10
        draw.multiline_text((text_x, text_y), text, fill="black", font=font, align="center")

        # Save the QR code image
        qr_file_path = f"static/images/customers/{customer_id}.png"
        os.makedirs(os.path.dirname(qr_file_path), exist_ok=True)
        img_with_text.save(qr_file_path)


        # Create new user 
        new_user = pd.DataFrame([{
            'Customer_ID': customer_id,
            'FirstName': first_name,
            'LastName': last_name,
            'Gender': gender,
            'DateOfBirth': dob,
            'Country': country,
            'City': city,
            'Address': address,
            'Email': email,
            'Username': username,
            'Password': password,
            'Points': 0,
            'Image': qr_file_path  # Store QR code path in the Excel file
        }])

        # Concatenate the new user data with the existing DataFrame
        df = pd.concat([df, new_user], ignore_index=True)

        # Save the updated data back to the user database
        df.to_excel(USER_EXCEL_FILE, index=False)

        return jsonify({'success': True, 'message': 'Welcome! Your account has been created successfully.'}), 200

    return render_template('signup.html')


# Check Duplicate Email or Username
@app.route('/api/check-duplicate', methods=['POST'])
def check_duplicate():
    data = request.json
    email = data.get('email')
    username = data.get('username')

    # Load existing data
    df = pd.read_excel(USER_EXCEL_FILE)

    if email in df['Email'].values:
        return jsonify({'success': False, 'message': 'This Email has already taken!'}), 400

    if username in df['Username'].values:
        return jsonify({'success': False, 'message': 'This Username hase already taken!'}), 400

    return jsonify({'success': True}), 200


# Get Item Details
@app.route('/api/items')
def get_items():
    """API endpoint to fetch all items."""
    formatted_items = [
        {
            'item_code':item['Item_Code'],
            'name': item['Item_name_in_English'],
            'category': item['Category'],
            'uom': item['UOM'],
            'today_price': item['Rewe'],
            'tomorrow_price': item['Price_for_Tomorrow'],
            'next_week_price': item['Price_After_7_Days'],
            'next_month_price': item['Price_After_1_Month'],
            'image': item['Image'],
            'plot_image': item['Plot_Image'],            
            'Rewe': item['Rewe'],
            'Netto': item['Netto'],
            'Penny': item['Penny'],
            'Kaufland': item['Kaufland'],
            'ALDI': item['AlDI'],            
            'description': item['Description'] if pd.notna(item['Description']) else 'No description available.',
            'benefits': item['Benefits'] if pd.notna(item['Benefits']) else 'No benefits information available.'
        }
        for item in items
    ]
    return jsonify(formatted_items)


# Add Items to Cart Action
@app.route('/api/add-to-cart', methods=['POST'])
def add_to_cart():
    """API endpoint to add items to the cart."""
    data = request.json
    print("Received data for adding to cart:", data)  # Debugging
    if 'item_code' in data:
        # Check if the item already exists in the cart
        existing_item = next((item for item in cart_items if item['item_code'] == data['item_code']), None)
        if existing_item:
            existing_item['quantity'] += 1  # Increment quantity if item exists
        else:
            # Find the item in `items` from `get_items` and add it to the cart
            item = next((item for item in items if item['Item_Code'] == data['item_code']), None)
            if item:
                cart_items.append({
                    'item_code': item['Item_Code'],
                    'name': item['Item_name_in_English'],
                    'category': item['Category'],
                    'uom': item['UOM'],
                    'image': item['Image'],
                    'Rewe': item['Rewe'],
                    'Netto': item['Netto'],
                    'Penny': item['Penny'],
                    'Kaufland': item['Kaufland'],
                    'AlDI': item['AlDI'],
                    'quantity': 1,  # Default value = 1
                })
        print("Cart items after adding:", cart_items)  # Debugging
        return jsonify({'message': 'Item added to cart successfully!'}), 200
    return jsonify({'error': 'Invalid request data'}), 400

# Update Cart Items Action
@app.route('/api/update-quantity', methods=['POST'])
def update_quantity():
    data = request.json
    item_code = int(data['item_code'])
    change = int(data['change'])

    # Update the item quantity
    for item in cart_items:
        if item['item_code'] == item_code:
            item['quantity'] += change
            if item['quantity'] <= 0:
                cart_items.remove(item)
            break

    # Recalculate the total prices and generate the updated chart
    total_prices = {
        'Rewe': sum(item['Rewe'] * item['quantity'] for item in cart_items),
        'Netto': sum(item['Netto'] * item['quantity'] for item in cart_items),
        'Penny': sum(item['Penny'] * item['quantity'] for item in cart_items),
        'Kaufland': sum(item['Kaufland'] * item['quantity'] for item in cart_items),
        'AlDI': sum(item['AlDI'] * item['quantity'] for item in cart_items),
    }

    chart_url = generate_chart_inline(total_prices)
    lowest_price_supermarket = min(total_prices, key=total_prices.get)
    lowest_price = total_prices[lowest_price_supermarket]
    

    return jsonify({
        'message': 'Quantity updated successfully!',
        'new_chart_url': chart_url,
        'lowest_price_supermarket': lowest_price_supermarket,
        'lowest_price': lowest_price
    }), 200

# Remove Items from Cart
@app.route('/api/remove-from-cart', methods=['POST'])
def remove_from_cart():
    try:
        data = request.json
        print("Request to remove item:", data)  # Debugging log
        item_code = int(data['item_code'])

        # Remove the item from the cart
        cart_items[:] = [item for item in cart_items if item['item_code'] != item_code]

        # Recalculate the total prices and generate the updated chart and text
        total_prices = {
            'Rewe': sum(item['Rewe'] * item['quantity'] for item in cart_items),
            'Netto': sum(item['Netto'] * item['quantity'] for item in cart_items),
            'Penny': sum(item['Penny'] * item['quantity'] for item in cart_items),
            'Kaufland': sum(item['Kaufland'] * item['quantity'] for item in cart_items),
            'AlDI': sum(item['AlDI'] * item['quantity'] for item in cart_items),
        }

        chart_url = generate_chart_inline(total_prices)
        lowest_price_supermarket = min(total_prices, key=total_prices.get)
        lowest_price = total_prices[lowest_price_supermarket]

        print("Updated cart items:", cart_items)  # Debugging log

        return jsonify({
            'message': 'Item removed successfully!',
            'new_chart_url': chart_url,
            'lowest_price_supermarket': lowest_price_supermarket,
            'lowest_price': lowest_price
        }), 200

    except Exception as e:
        print("Error while removing item from cart:", str(e))  # Debugging log
        return jsonify({'message': 'An error occurred while removing the item.'}), 500

# Check Cart Status
@app.route('/api/cart-status', methods=['GET'])
def cart_status():
    """API endpoint to check if the cart is empty."""
    return jsonify({'is_cart_empty': len(cart_items) == 0})

# Route for Cart Page
@app.route('/cart')
def cart():
    # Generate detailed cart items
    detailed_cart_items = []
    for cart_item in cart_items:
        matching_item = next((item for item in items if item['Item_Code'] == cart_item['item_code']), None)
        if matching_item:
            detailed_cart_items.append({
                'item_code': cart_item['item_code'],
                'name': matching_item['Item_name_in_English'],
                'category': matching_item['Category'],
                'uom': matching_item['UOM'],
                'image': matching_item['Image'],
                'quantity': cart_item['quantity'],
                'Rewe': matching_item['Rewe'],
                'Netto': matching_item['Netto'],
                'Penny': matching_item['Penny'],
                'Kaufland': matching_item['Kaufland'],
                'AlDI': matching_item['AlDI'],
            })

    # Calculate total prices
    total_prices = {
        'Rewe': sum(item['Rewe'] * item['quantity'] for item in detailed_cart_items),
        'Netto': sum(item['Netto'] * item['quantity'] for item in detailed_cart_items),
        'Penny': sum(item['Penny'] * item['quantity'] for item in detailed_cart_items),
        'Kaufland': sum(item['Kaufland'] * item['quantity'] for item in detailed_cart_items),
        'AlDI': sum(item['AlDI'] * item['quantity'] for item in detailed_cart_items),
    }

    # Generate the comparison chart
    chart_url = generate_chart_inline(total_prices)

    # Find the lowest price
    lowest_price_supermarket = min(total_prices, key=total_prices.get)
    lowest_price = total_prices[lowest_price_supermarket]

    # Debugging
    print("Chart URL:", chart_url[:50])
    print("Lowest Price Supermarket:", lowest_price_supermarket)
    print("Lowest Price:", lowest_price)

    return render_template('cart.html',
                           cart_items=detailed_cart_items,
                           chart_url=chart_url,
                           lowest_price_supermarket=lowest_price_supermarket,
                           lowest_price=lowest_price)


# Clear All Items from Cart
@app.route('/api/clear-cart', methods=['POST'])
def clear_cart():
    """Clear all items from the cart."""
    global cart_items
    cart_items = []  # Reset the cart to an empty list
    print("Cart cleared. Current cart items:", cart_items)  # Debugging log
    return jsonify({'message': 'Cart cleared successfully!'}), 200

# Pass the information of Cart Items to Purchase History Database
@app.route('/api/save-cart', methods=['POST'])
def save_cart():
    """Save cart items to PURCHASE_HISTORY_EXCEL_FILE."""
    global cart_items

    # Load the existing purchase history data
    if os.path.exists(PURCHASE_HISTORY_EXCEL_FILE):
        purchase_history = pd.read_excel(PURCHASE_HISTORY_EXCEL_FILE)
    else:
        # Create a new DataFrame if the file doesn't exist
        columns = ['Customer_ID', 'Item_Code', 'Quantity', 'Total Price', 'Date']
        purchase_history = pd.DataFrame(columns=columns)

    # Get the current user
    user = session.get('user')
    if not user:
        return jsonify({'success': False, 'message': 'User not logged in.'}), 401

    customer_id = user.get('Customer_ID')
    if not customer_id:
        return jsonify({'success': False, 'message': 'Customer ID not found in session.'}), 400


        # Recalculate the total prices and generate the updated chart and text
    total_prices = {
        'Rewe': sum(item['Rewe'] * item['quantity'] for item in cart_items),
        'Netto': sum(item['Netto'] * item['quantity'] for item in cart_items),
        'Penny': sum(item['Penny'] * item['quantity'] for item in cart_items),
        'Kaufland': sum(item['Kaufland'] * item['quantity'] for item in cart_items),
        'AlDI': sum(item['AlDI'] * item['quantity'] for item in cart_items),
    }


    lowest_price_supermarket = min(total_prices, key=total_prices.get)
    new_points = int(float(total_prices[lowest_price_supermarket]))
    print("Supermarket Name : ",lowest_price_supermarket)
    print("New Points : ",new_points)

    # Update the Points in User Database
    user_data = pd.read_excel(USER_EXCEL_FILE)
    if customer_id in user_data['Customer_ID'].values:
        user_data.loc[user_data['Customer_ID'] == customer_id, 'Points'] += new_points
        updated_points = user_data.loc[user_data['Customer_ID'] == customer_id, 'Points'].values[0]
        user_data.to_excel(USER_EXCEL_FILE, index=False)

        # Update the session with the new points
        session['user']['Points'] = updated_points
    else:
        return jsonify({'success': False, 'message': 'User not found in the database.'}), 400



    # Add cart items to the purchase history
    today_date = datetime.now().strftime('%Y-%m-%d')
    new_entries = []

    for item in cart_items:
        # Calculate the total price for each item
        total_price = item['quantity'] * item[lowest_price_supermarket] 
        new_entries.append({
            'Customer_ID': customer_id,
            'Item_Code': item['item_code'],
            'Item_Name': item['name'],
            'Category': item['category'],
            'UOM': item['uom'],
            'Quantity': item['quantity'],
            'Unit Price': item[lowest_price_supermarket],
            'Total Price': total_price,
            'Date': today_date
        })

    # Append the new entries to the existing DataFrame
    new_entries_df = pd.DataFrame(new_entries)
    purchase_history = pd.concat([purchase_history, new_entries_df], ignore_index=True)

    # Save the updated purchase history back to the Excel file
    purchase_history.to_excel(PURCHASE_HISTORY_EXCEL_FILE, index=False)

    # Clear the cart after saving
    cart_items = []

    return jsonify({'success': True, 'message': f'Thank you for providing the information. You will receive {new_points} points. Please scan your QR code at the Supermarket terminal to collect your points.'})


# Refresh User Session
@app.route('/api/refresh-session', methods=['GET'])
def refresh_session():
    if 'user' in session:
        user_data = pd.read_excel(USER_EXCEL_FILE)
        customer_id = session['user']['Customer_ID']
        updated_user = user_data[user_data['Customer_ID'] == customer_id].iloc[0].to_dict()
        session['user'] = updated_user  # Update the session with fresh data
        return jsonify({'success': True, 'user': session['user']})
    return jsonify({'success': False, 'message': 'User not logged in.'}), 401


#Route for QR Code
@app.route('/qr_code')
def qr_code():
    if 'user' in session:
        qr_code_path = session['user'].get('Image')  # Get the QR code path from the session
        return render_template('qr_code.html', qr_code_path=qr_code_path)
    return redirect(url_for('login_page'))


# Load User Details
@app.route('/user')
def user_dashboard():
    if 'user' in session:
        session['user']['ProfileImage'] = f"/static/images/customers/profile_image/{session['user']['Customer_ID']}.png"
        return render_template('user.html', user=session['user'])
    return redirect(url_for('login_page'))

# To show the User expenditure over the time.
@app.route('/user/line-chart')
def user_line_chart():
    customer_id = session['user'].get('Customer_ID')
    data= pd.read_excel(PURCHASE_HISTORY_EXCEL_FILE)
    if customer_id:
        customer_data = data[data['Customer_ID'] == customer_id].copy()
        if not customer_data.empty:
            customer_data['Date'] = pd.to_datetime(customer_data['Date'])
            customer_data['Month_Year'] = customer_data['Date'].dt.strftime('%B %Y')
            monthly_totals = customer_data.groupby('Month_Year')['Total Price'].sum()
            monthly_totals = monthly_totals.reindex(
                pd.to_datetime(monthly_totals.index, format='%B %Y').sort_values().strftime('%B %Y')
            )
            monthly_totals.index = pd.to_datetime(monthly_totals.index, format='%B %Y')

            fig, ax = plt.subplots(figsize=(14, 8), constrained_layout=True)
            x_values = monthly_totals.index
            y_values = monthly_totals.values
            colors = plt.cm.viridis(np.linspace(0, 1, len(y_values)))

            for i in range(len(x_values) - 1):
                ax.plot(x_values[i:i+2], y_values[i:i+2], color=colors[i], linewidth=3)
            ax.scatter(x_values, y_values, c=np.arange(len(y_values)), cmap='viridis', s=100, edgecolor='black')

            for x, y in zip(x_values, y_values):
                ax.text(x, y + max(y_values) * 0.02, f"€{y:.2f}", fontsize=10, ha='center', color='black')

            ax.grid(axis='y', linestyle='--', alpha=0.6)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            #ax.set_title('Total Spending Over Time', fontsize=18, fontweight='bold')
            ax.set_ylabel('Total Spending (in €)', fontsize=14, labelpad=10)

            # Customize the x-axis for better readability
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
            plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
            plt.xticks(rotation=0, fontsize=12)

            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plt.close()
            return send_file(img, mimetype='image/png')
    return "No data available", 400

#To show the montly purchase history on different categories
@app.route('/user/bar-chart')
def user_bar_chart():
    customer_id = session['user'].get('Customer_ID')
    data= pd.read_excel(PURCHASE_HISTORY_EXCEL_FILE)
    if customer_id:
        customer_data = data[data['Customer_ID'] == customer_id].copy()
        if not customer_data.empty:
            customer_data['Date'] = pd.to_datetime(customer_data['Date'])
            customer_data['Month_Year'] = customer_data['Date'].dt.strftime('%B %Y')
            monthly_data = customer_data.groupby(['Month_Year', 'Category'])['Total Price'].sum().unstack()
            monthly_data = monthly_data.reindex(
                pd.to_datetime(monthly_data.index, format='%B %Y').sort_values().strftime('%B %Y'), axis=0
            )

            fig, ax = plt.subplots(figsize=(14, 8), constrained_layout=True)
            num_months = len(monthly_data.index)
            colors = cm.viridis(np.linspace(0.2, 0.9, num_months))
            monthly_data.T.plot(kind='bar', ax=ax, width=0.75, color=colors, edgecolor='black')

            #ax.set_title('Your Monthly Purchase History on Grocery Items', fontsize=18, fontweight='bold')
            ax.set_ylabel('Total Purchases (in €)', fontsize=14, labelpad=10)
            ax.set_xticks(range(len(monthly_data.columns)))
            ax.set_xticklabels(monthly_data.columns, rotation=0, fontsize=12)
            ax.grid(axis='y', linestyle='--', alpha=0.6)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)

            # Annotate bars with their values
            for bar_group in ax.containers:
                ax.bar_label(
                    bar_group,
                    fmt='€%.2f',
                    fontsize=10,
                    padding=3,
                    color='black'
                )

            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plt.close()
            return send_file(img, mimetype='image/png')
    return "No data available", 400

# To show the user habits on grocery items
@app.route('/user/pie-chart')
def user_pie_chart():
    customer_id = session['user'].get('Customer_ID')
    data= pd.read_excel(PURCHASE_HISTORY_EXCEL_FILE)
    if customer_id:
        customer_data = data[data['Customer_ID'] == customer_id].copy()
        if not customer_data.empty:
            category_data = customer_data.groupby('Category')['Total Price'].sum()

            fig, ax = plt.subplots(figsize=(10, 10), constrained_layout=True)
            wedges, texts, autotexts = ax.pie(
                category_data, labels=category_data.index, autopct='%1.0f%%',
                startangle=90, colors=plt.cm.Set2.colors, textprops={'fontsize': 12},
                pctdistance=0.8, wedgeprops={'edgecolor': 'white', 'linewidth': 2} 
            )
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')

            centre_circle = plt.Circle((0, 0), 0.60, fc='white')
            ax.add_artist(centre_circle)
            #ax.set_title('Your Spending Distribution on Grocery Products', fontsize=16, fontweight='bold')

            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            plt.close()
            return send_file(img, mimetype='image/png')
    return "No data available", 400


# To show the top 6 products
def get_top_products_by_quantity(PURCHASE_HISTORY_EXCEL_FILE, top_n=6):
    purchase_history_data = pd.read_excel(PURCHASE_HISTORY_EXCEL_FILE)
    top_products = purchase_history_data.groupby('Item_Code', as_index=False)['Quantity'].sum()
    top_products = top_products.sort_values(by='Quantity', ascending=False).head(top_n)
    return top_products


# Route for Market Analysis Page
@app.route('/market_analysis')
def market_analysis():
    top_products_data = get_top_products_by_quantity(PURCHASE_HISTORY_EXCEL_FILE, top_n=6)
    top_items = top_products_data['Item_Code'].tolist()

    # Get item details from `items` data
    top_products = []
    for item_code in top_items:
        item = next((i for i in items if i['Item_Code'] == item_code), None)  
        if item:
            top_products.append({
                'item_code': item_code,
                'name': item['Item_name_in_English'],
                'image': item['Image'],
                'quantity': int(top_products_data[top_products_data['Item_Code'] == item_code]['Quantity'].iloc[0])
            })

    return render_template('market_analysis.html', top_products=top_products)

#To show price variation in different supermarket
@app.route('/plot/<int:item_code>')
def get_price_trend_plot(item_code):
    web_scraping_data = pd.read_excel(WEB_SCRAPING_EXCEL_FILE)

    # Filter web scraping data for the provided item code
    item_price_history_data = web_scraping_data[web_scraping_data['Item_Code'] == item_code]

    if item_price_history_data.empty:
        return "No data found for the given Item Code.", 404

    item_name = item_price_history_data['Item_name_in_English'].iloc[0]

    # Plot price trends
    plt.figure(figsize=(10, 6))
    for market in ['Rewe', 'Netto', 'Penny', 'Kaufland', 'AlDI']:
        if market in item_price_history_data.columns:
            plt.plot(
                item_price_history_data['Date'],
                item_price_history_data[market],
                label=market,
                marker='o',
                markersize=8,
                linewidth=2
            )

    plt.title(f'Price Trends for {item_name}', fontsize=18, fontweight='bold')
    #plt.xlabel('Date', fontsize=14)
    plt.ylabel('Price (€)', fontsize=14)
    plt.xticks(rotation=90)
    plt.legend(title="Markets", fontsize=12, loc='upper left', bbox_to_anchor=(1, 1))
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Annotate max and min prices
    for market in ['Rewe', 'Netto', 'Penny', 'Kaufland', 'AlDI']:
        if market in item_price_history_data.columns:
            max_price = item_price_history_data[market].max()
            min_price = item_price_history_data[market].min()
            max_date = item_price_history_data['Date'][item_price_history_data[market].idxmax()]
            min_date = item_price_history_data['Date'][item_price_history_data[market].idxmin()]

            plt.text(
                max_date, max_price, f'High: €{max_price:.2f}',
                color='red', fontsize=10, ha='center', va='bottom',
                path_effects=[withStroke(linewidth=2, foreground='white')]
            )
            plt.text(
                min_date, min_price, f'Low: €{min_price:.2f}',
                color='green', fontsize=10, ha='center', va='top',
                path_effects=[withStroke(linewidth=2, foreground='white')]
            )

    plt.tight_layout()

    # Save the plot to a BytesIO object and encode as base64
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    return base64.b64encode(img.getvalue()).decode('utf-8')

# To show the Market Size
@app.route('/market-analysis-bar-chart')
def market_analysis_bar_chart():
    market_data = pd.read_excel(PURCHASE_HISTORY_EXCEL_FILE)

    # Convert the 'Date' column to datetime format to extract month-year
    market_data['Date'] = pd.to_datetime(market_data['Date'])
    market_data['Month_Year'] = market_data['Date'].dt.strftime('%B %Y')  # Extract "Month Year"

    # Aggregate Total Price by Month-Year
    monthly_totals = market_data.groupby('Month_Year')['Total Price'].sum()

    # Sort months chronologically
    monthly_totals = monthly_totals.reindex(
        pd.to_datetime(monthly_totals.index, format='%B %Y').sort_values().strftime('%B %Y')
    )

    # Convert Month-Year back to datetime for plotting
    monthly_totals.index = pd.to_datetime(monthly_totals.index, format='%B %Y')

    # Calculate growth trends (percentage change)
    growth_trends = monthly_totals.pct_change() * 100

    # Generate the bar chart
    plt.figure(figsize=(14, 8))
    x_values = monthly_totals.index
    y_values = monthly_totals.values

    # Create bars with gradient color
    bar_colors = plt.cm.viridis(np.linspace(0, 1, len(y_values)))
    bars = plt.bar(x_values, y_values, color=bar_colors, edgecolor='black', width=20)

    # Add data labels to each bar
    for bar, y in zip(bars, y_values):
        plt.text(bar.get_x() + bar.get_width()/2, y + max(y_values)*0.02, f"€{y:.2f}", 
                 ha='center', fontsize=10, color='black')

    # Add growth trend labels
    for i, (x, y, growth) in enumerate(zip(x_values, y_values, growth_trends)):
        if not pd.isna(growth):
            trend_color = 'lime' if growth > 0 else 'red'
            plt.text(x, y - max(y_values)*0.1, f"{growth:+.1f}%", 
                     ha='center', fontsize=10, color=trend_color)

    # Customize the grid and spines
    plt.grid(axis='y', linestyle='--', alpha=0.6, color='gray')
    plt.gca().spines['top'].set_visible(False)
    plt.gca().spines['right'].set_visible(False)

    # Customize the x-axis for better readability
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.xticks(rotation=0, fontsize=12)

    # Add titles and labels
    #plt.title('Total Spending Over Time with Growth Trends', fontsize=18, fontweight='bold', color='#333333')
    plt.xlabel('', fontsize=14, labelpad=10)
    plt.ylabel('Total Value (in €)', fontsize=14, labelpad=10)

    # Add background gradient
    plt.gca().set_facecolor('#f7f7f7')

    # Serve as PNG
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    return send_file(img, mimetype='image/png')

# To show customer's spending nature
@app.route('/market-analysis-pie-chart')
def market_analysis_pie_chart():
    # Load data
    market_data = pd.read_excel(PURCHASE_HISTORY_EXCEL_FILE)

    # Summarize data by Category and Total Price
    category_summary = market_data.groupby('Category')['Total Price'].sum()

    # Custom color palette
    colors = plt.cm.Paired(range(len(category_summary)))

    # Create a pie chart with visual effects
    plt.figure(figsize=(10, 10))
    explode = [0.05] * len(category_summary)  # Slightly explode all slices

    # Custom autopct function to show only the percentage
    def autopct_only_percentage(pct):
        return f"{pct:.1f}%"

    # Plot the pie chart
    plt.pie(
        category_summary,
        labels=[f"{category}\n(${value:.2f})" for category, value in category_summary.items()],
        autopct=autopct_only_percentage,
        startangle=90,
        shadow=True,
        explode=explode,
        colors=colors,
    )

    #plt.title('Buying Nature of Customers')

    # Serve as PNG
    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plt.close()

    return send_file(img, mimetype='image/png')


if __name__ == '__main__':
    app.run(debug=True)
