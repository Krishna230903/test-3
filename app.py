# CrudeTrack - Oil & Gas Shipment and Analytics Platform (Modern UI)
# To run this app:
# 1. Install necessary libraries: pip install streamlit pandas sqlalchemy bcrypt
# 2. Save this code as a Python file (e.g., app.py)
# 3. Run from your terminal: streamlit run app.py

import streamlit as st
import pandas as pd
import sqlite3
import datetime
import bcrypt
import time
import numpy as np

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CrudeTrack",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS FOR MODERN UI ---
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def inject_custom_css():
    st.markdown("""
        <style>
            /* General App Styling */
            .stApp {
                background-color: #F0F2F6;
            }
            
            /* Main content area */
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                padding-left: 5rem;
                padding-right: 5rem;
            }

            /* Custom Cards for Products/KPIs */
            .custom-card {
                background-color: #FFFFFF;
                border-radius: 10px;
                padding: 20px;
                box-shadow: 0 4px 8px 0 rgba(0,0,0,0.1);
                transition: 0.3s;
                margin-bottom: 20px;
                height: 100%;
            }
            .custom-card:hover {
                box-shadow: 0 8px 16px 0 rgba(0,0,0,0.2);
            }

            /* Styling for KPI metrics */
            .stMetric {
                background-color: #FFFFFF;
                border-left: 5px solid #007BFF;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 4px 0 rgba(0,0,0,0.1);
            }

            /* Button styling */
            .stButton>button {
                border-radius: 20px;
                border: 1px solid #007BFF;
                color: #007BFF;
                background-color: transparent;
            }
            .stButton>button:hover {
                border-color: #0056b3;
                color: #0056b3;
            }
            .stButton>button:focus {
                box-shadow: none !important;
            }

            /* Login/Register Form Styling */
            .login-form {
                background: white;
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                max-width: 450px;
                margin: auto;
            }
        </style>
    """, unsafe_allow_html=True)

# --- DATABASE SETUP ---
DB_NAME = "crude_track.db"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    """Initializes the database and creates tables if they don't exist."""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL, role TEXT NOT NULL)''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT,
            source_port TEXT, image_url TEXT)''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, product_id INTEGER,
            destination_city TEXT, quantity_barrels INTEGER, order_date TIMESTAMP, status TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id), FOREIGN KEY (product_id) REFERENCES products (id))''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS shipment_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT, order_id INTEGER, current_location TEXT, timestamp TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders (id))''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS product_interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, product_id INTEGER, view_timestamp TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id), FOREIGN KEY (product_id) REFERENCES products (id))''')

    c.execute("SELECT count(*) FROM products")
    if c.fetchone()[0] == 0:
        products_data = [
            ('Brent Crude', 'A major trading classification of sweet light crude oil from the North Sea. It is used to price two-thirds of the world\'s internationally traded crude oil supplies.', 'Sullom Voe, UK', 'https://placehold.co/600x400/2D3748/FFFFFF?text=Brent+Crude'),
            ('WTI Crude', 'West Texas Intermediate (WTI) is a light, sweet crude oil that is the benchmark for North American oil. It is sourced primarily from the Permian Basin.', 'Cushing, OK, USA', 'https://placehold.co/600x400/2D3748/FFFFFF?text=WTI+Crude'),
            ('Dubai Crude', 'Also known as Fateh, this is a light sour crude oil extracted from Dubai. It is used as a price benchmark for exports of crude oil from the Persian Gulf to Asia.', 'Fateh Terminal, Dubai', 'https://placehold.co/600x400/2D3748/FFFFFF?text=Dubai+Crude')
        ]
        c.executemany("INSERT INTO products (name, description, source_port, image_url) VALUES (?, ?, ?, ?)", products_data)

    c.execute("SELECT count(*) FROM users WHERE username = 'admin'")
    if c.fetchone()[0] == 0:
        admin_pass = "admin123"
        hashed_password = bcrypt.hashpw(admin_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ('admin', hashed_password, 'admin'))

    conn.commit()
    conn.close()

# --- USER AUTHENTICATION & DATA FUNCTIONS (Same as before, for brevity) ---
def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(hashed_password, user_password):
    return bcrypt.checkpw(user_password.encode('utf-8'), hashed_password)

def register_user(username, password, role='customer'):
    conn = get_db_connection()
    c = conn.cursor()
    try:
        hashed_pw = hash_password(password).decode('utf-8')
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", (username, hashed_pw, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def validate_login(username, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    if user and check_password(user['password_hash'].encode('utf-8'), password):
        return {'id': user['id'], 'username': user['username'], 'role': user['role']}
    return None

def get_all_products():
    conn = get_db_connection()
    products = pd.read_sql_query("SELECT * FROM products", conn)
    conn.close()
    return products

def log_product_interaction(user_id, product_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO product_interactions (user_id, product_id, view_timestamp) VALUES (?, ?, ?)",
              (user_id, product_id, datetime.datetime.now()))
    conn.commit()
    conn.close()

def place_order(user_id, product_id, destination, quantity):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, product_id, destination_city, quantity_barrels, order_date, status) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, product_id, destination, quantity, datetime.datetime.now(), 'Placed'))
    order_id = c.lastrowid
    c.execute("INSERT INTO shipment_tracking (order_id, current_location, timestamp) VALUES (?, ?, ?)",
              (order_id, "Order confirmed. Awaiting dispatch from terminal.", datetime.datetime.now()))
    conn.commit()
    conn.close()
    return order_id

def get_user_orders(user_id):
    conn = get_db_connection()
    query = "SELECT o.id, p.name as product_name, o.destination_city, o.quantity_barrels, o.order_date, o.status FROM orders o JOIN products p ON o.product_id = p.id WHERE o.user_id = ? ORDER BY o.order_date DESC"
    return pd.read_sql_query(query, conn, params=(user_id,))

def get_tracking_info(order_id):
    conn = get_db_connection()
    query = "SELECT current_location, timestamp FROM shipment_tracking WHERE order_id = ? ORDER BY timestamp DESC"
    return pd.read_sql_query(query, conn, params=(order_id,))

def get_all_orders_for_admin():
    conn = get_db_connection()
    query = "SELECT o.id, u.username, p.name as product_name, o.destination_city, o.quantity_barrels, o.order_date, o.status FROM orders o JOIN users u ON o.user_id = u.id JOIN products p ON o.product_id = p.id ORDER BY o.order_date DESC"
    return pd.read_sql_query(query, conn)

def get_product_interaction_analytics():
    conn = get_db_connection()
    query = "SELECT p.name, COUNT(pi.id) as view_count FROM product_interactions pi JOIN products p ON pi.product_id = p.id GROUP BY p.name ORDER BY view_count DESC"
    return pd.read_sql_query(query, conn)

def update_shipment_status(order_id, new_location):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO shipment_tracking (order_id, current_location, timestamp) VALUES (?, ?, ?)",
              (order_id, new_location, datetime.datetime.now()))
    c.execute("UPDATE orders SET status = 'In Transit' WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()


# --- UI COMPONENTS ---

def login_register_page():
    """Displays the login and registration forms with a modern look."""
    st.markdown(f'<div class="login-form">', unsafe_allow_html=True)
    st.title("Welcome to CrudeTrack 🚚")
    st.write("Login or create an account to continue.")

    choice = st.radio("", ["Login", "Register"], horizontal=True)

    if choice == "Login":
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="e.g., johndoe")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Login")
            if submitted:
                user = validate_login(username, password)
                if user:
                    st.session_state['logged_in'] = True
                    st.session_state['user_id'] = user['id']
                    st.session_state['username'] = user['username']
                    st.session_state['role'] = user['role']
                    st.rerun()
                else:
                    st.error("Invalid username or password")
    
    elif choice == "Register":
        with st.form("register_form"):
            new_username = st.text_input("Choose a Username")
            new_password = st.text_input("Choose a Password", type="password")
            submitted = st.form_submit_button("Register")
            if submitted:
                if register_user(new_username, new_password):
                    st.success("Registration successful! Please login.")
                else:
                    st.error("Username already exists.")
    st.markdown('</div>', unsafe_allow_html=True)


def customer_portal():
    """The main view for logged-in customers with a modern UI."""
    st.sidebar.title(f"Welcome, {st.session_state['username'].capitalize()}!")
    st.sidebar.markdown("---")
    page = st.sidebar.radio("Navigation", ["📈 Live Market", "🛢️ Products & Orders", "🚚 Track Shipments"])
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    if page == "📈 Live Market":
        st.header("📈 Live Crude Oil Price (WTI)")
        st.write("Real-time simulated price fluctuations for West Texas Intermediate crude oil.")
        price_chart_placeholder = st.empty()
        
        last_price = 78.50
        price_data = pd.DataFrame({'Time': [datetime.datetime.now()], 'Price (USD)': [last_price]})
        
        for i in range(100): # Simulate updates
            new_price = last_price + np.random.randn() * 0.15
            last_price = max(new_price, 60) # Prevent price from going too low
            now = datetime.datetime.now() + datetime.timedelta(seconds=i*2)
            new_row = pd.DataFrame({'Time': [now], 'Price (USD)': [new_price]})
            price_data = pd.concat([price_data, new_row], ignore_index=True)
            with price_chart_placeholder:
                st.line_chart(price_data.rename(columns={'Time':'index'}).set_index('index'))
            time.sleep(0.5)

    elif page == "🛢️ Products & Orders":
        st.header("🛢️ Our Products")
        products = get_all_products()
        
        cols = st.columns(len(products))
        for i, (index, row) in enumerate(products.iterrows()):
            with cols[i]:
                st.markdown(f'<div class="custom-card">', unsafe_allow_html=True)
                st.image(row['image_url'])
                st.subheader(row['name'])
                st.caption(f"Source: {row['source_port']}")
                st.write(row['description'])
                if st.button(f"View {row['name']}", key=f"view_{row['id']}"):
                    log_product_interaction(st.session_state['user_id'], row['id'])
                    st.info(f"Your interest in {row['name']} has been noted by our team.")
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.header("📝 Place a New Order")
        with st.form("order_form"):
            col1, col2 = st.columns(2)
            with col1:
                selected_product_name = st.selectbox("Select Product", products['name'].tolist())
                quantity = st.number_input("Quantity (barrels)", min_value=100, step=100)
            with col2:
                destination = st.text_input("Destination City", placeholder="e.g., Rotterdam")
                st.write("") # Spacer
                st.write("") # Spacer
                submitted = st.form_submit_button("Place Order")

            if submitted:
                product_id = products[products['name'] == selected_product_name]['id'].iloc[0]
                order_id = place_order(st.session_state['user_id'], product_id, destination, quantity)
                st.success(f"🎉 Order placed successfully! Your Order ID is: **{order_id}**")
                st.balloons()

    elif page == "🚚 Track Shipments":
        st.header("🚚 Track Your Shipments")
        my_orders = get_user_orders(st.session_state['user_id'])
        
        if my_orders.empty:
            st.info("You have no active orders. Place one from the Products page!")
        else:
            st.write("Here is a list of your recent orders.")
            st.dataframe(my_orders, use_container_width=True)
            
            order_ids = my_orders['id'].tolist()
            selected_order_id = st.selectbox("Select an Order ID to see detailed tracking:", order_ids)

            if selected_order_id:
                st.subheader(f"Tracking History for Order #{selected_order_id}")
                tracking_history = get_tracking_info(selected_order_id)
                if tracking_history.empty:
                    st.warning("No tracking information available yet.")
                else:
                    for _, row in tracking_history.iterrows():
                        st.markdown(f"**{row['timestamp']}**: `{row['current_location']}`")

def admin_dashboard():
    """The main view for logged-in admins with a modern UI."""
    st.sidebar.title("Admin Panel")
    st.sidebar.markdown(f"Logged in as **{st.session_state['username']}** (Admin)")
    st.sidebar.markdown("---")
    page = st.sidebar.radio("Navigation", ["📊 Dashboard", "⚙️ Manage Shipments"])
    st.sidebar.markdown("---")
    if st.sidebar.button("Logout"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    if page == "📊 Dashboard":
        st.header("📊 Business Analytics Dashboard")
        
        orders_df = get_all_orders_for_admin()
        interactions_df = get_product_interaction_analytics()
        
        total_orders = len(orders_df)
        total_barrels = orders_df['quantity_barrels'].sum() if not orders_df.empty else 0
        most_popular_product = interactions_df['name'].iloc[0] if not interactions_df.empty else "N/A"

        st.markdown("### Key Performance Indicators")
        kpi1, kpi2, kpi3 = st.columns(3)
        with kpi1:
            st.metric("Total Orders Placed", f"{total_orders}")
        with kpi2:
            st.metric("Total Barrels Ordered", f"{total_barrels:,}")
        with kpi3:
            st.metric("Most Viewed Product", most_popular_product)
        
        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Product View Count")
            if not interactions_df.empty:
                st.bar_chart(interactions_df.set_index('name'))
            else:
                st.info("No product interaction data yet.")
        with col2:
            st.subheader("Orders by Status")
            if not orders_df.empty:
                status_counts = orders_df['status'].value_counts()
                st.bar_chart(status_counts)
            else:
                st.info("No order data yet.")

        st.subheader("All Customer Orders")
        st.dataframe(orders_df, use_container_width=True)

    elif page == "⚙️ Manage Shipments":
        st.header("⚙️ Update Shipment Status")
        orders_df = get_all_orders_for_admin()
        
        if orders_df.empty:
            st.info("No orders to manage.")
        else:
            st.dataframe(orders_df[['id', 'username', 'product_name', 'destination_city', 'status']], use_container_width=True)
            
            with st.form("update_shipment_form"):
                col1, col2 = st.columns([1,3])
                with col1:
                    order_ids = orders_df['id'].tolist()
                    selected_order_id = st.selectbox("Order ID", order_ids)
                with col2:
                    new_location = st.text_input("New Location / Status Update", placeholder="e.g., 'Passing through Suez Canal'")
                
                submitted = st.form_submit_button("Update Status")
                if submitted and new_location:
                    update_shipment_status(selected_order_id, new_location)
                    st.success(f"Status for Order #{selected_order_id} updated.")
            
            st.subheader("Current Tracking Info for Selected Order")
            if selected_order_id:
                tracking_info = get_tracking_info(selected_order_id)
                st.dataframe(tracking_info, use_container_width=True)

# --- MAIN APP LOGIC ---
def main():
    """Main function to run the Streamlit app."""
    setup_database()
    inject_custom_css()

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if st.session_state['logged_in']:
        if st.session_state['role'] == 'admin':
            admin_dashboard()
        else:
            customer_portal()
    else:
        login_register_page()

if __name__ == "__main__":
    main()
