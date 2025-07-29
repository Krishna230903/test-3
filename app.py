# CrudeTrack - Oil & Gas Shipment and Analytics Platform (Modern UI v2 - Final)
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

# --- CUSTOM CSS FOR MODERN UI (v2) ---
def inject_custom_css():
    st.markdown("""
        <style>
            /* --- General App Styling --- */
            .stApp {
                background-color: #0E1117;
                color: #FAFAFA;
            }

            /* --- Main Content Area --- */
            .main .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
                padding-left: 3rem;
                padding-right: 3rem;
            }

            /* --- Sidebar Styling --- */
            .st-emotion-cache-16txtl3 {
                background-color: rgba(38, 39, 48, 0.4); /* Semi-transparent sidebar */
            }
            .st-emotion-cache-16txtl3 h1 {
                color: #00A9FF;
            }

            /* --- Glassmorphism Card Effect --- */
            .custom-card {
                background: rgba(38, 39, 48, 0.6);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.18);
                padding: 25px;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
                margin-bottom: 20px;
                height: 100%;
                color: #FAFAFA;
            }
            .custom-card h3, .custom-card .st-emotion-cache-10trblm {
                color: #FAFAFA !important;
            }
            .custom-card .stImage > img {
                border-radius: 10px;
            }

            /* --- KPI Metric Styling --- */
            .stMetric {
                background: rgba(38, 39, 48, 0.6);
                backdrop-filter: blur(5px);
                -webkit-backdrop-filter: blur(5px);
                border-left: 6px solid #00A9FF;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 15px 0 rgba(0, 0, 0, 0.2);
                color: #FAFAFA !important;
            }
            .stMetric .st-emotion-cache-1wivap2, .stMetric .st-emotion-cache-1g8m2i9 {
                 color: #FAFAFA !important;
            }


            /* --- Button Styling --- */
            .stButton>button {
                border-radius: 8px;
                border: 1px solid #00A9FF;
                color: #00A9FF;
                background-color: transparent;
                padding: 10px 20px;
                font-weight: bold;
                transition: all 0.3s ease;
            }
            .stButton>button:hover {
                background-color: #00A9FF;
                color: #FFFFFF;
                border-color: #00A9FF;
                box-shadow: 0 0 15px #00A9FF;
            }
            .stButton>button:focus {
                box-shadow: 0 0 15px #00A9FF !important;
            }

            /* Primary Button (e.g., Place Order) */
            .stButton.primary-btn>button {
                background-color: #00A9FF;
                color: #FFFFFF;
            }
            .stButton.primary-btn>button:hover {
                background-color: #0087cc;
                box-shadow: 0 0 20px #00A9FF;
            }


            /* --- Login/Register Form Styling --- */
            .login-container {
                display: flex;
                justify-content: center;
                align-items: flex-start; /* Changed from 'center' to move form to the top */
                padding-top: 10vh;      /* Added padding so it's not at the very top */
                min-height: 90vh;
            }
            .login-form {
                background: rgba(38, 39, 48, 0.7);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                padding: 2.5rem 3rem;
                border-radius: 15px;
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
                border: 1px solid rgba(255, 255, 255, 0.18);
                width: 100%;
                max-width: 450px;
            }
            .login-form h1 {
                text-align: center;
                color: #00A9FF;
            }
            .login-form .stRadio > div {
                justify-content: center;
            }

            /* --- Dataframe Styling --- */
            .stDataFrame {
                background-color: rgba(38, 39, 48, 0.6);
                border-radius: 10px;
            }
            
            /* --- Headers --- */
            h1, h2, h3 {
                color: #FAFAFA;
            }

        </style>
    """, unsafe_allow_html=True)

# --- DATABASE SETUP ---
DB_NAME = "crude_track.db"

@st.cache_resource
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def setup_database():
    """Initializes the database and creates tables if they don't exist."""
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
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

    # Seed initial data for products if table is empty
    c.execute("SELECT count(*) FROM products")
    if c.fetchone()[0] == 0:
        products_data = [
            ('Brent Crude', 'A major trading classification of sweet light crude oil from the North Sea. It is used to price two-thirds of the world\'s internationally traded crude oil supplies.', 'Sullom Voe, UK', 'https://images.unsplash.com/photo-1629115124174-a82d854344a2?q=80&w=1964&auto=format&fit=crop'),
            ('WTI Crude', 'West Texas Intermediate (WTI) is a light, sweet crude oil that is the benchmark for North American oil. It is sourced primarily from the Permian Basin.', 'Cushing, OK, USA', 'https://images.unsplash.com/photo-1622384214138-2cf917637845?q=80&w=1974&auto=format&fit=crop'),
            ('Dubai Crude', 'Also known as Fateh, this is a light sour crude oil extracted from Dubai. It is used as a price benchmark for exports of crude oil from the Persian Gulf to Asia.', 'Fateh Terminal, Dubai', 'https://images.unsplash.com/photo-1623861226131-45c1a742784d?q=80&w=1974&auto=format&fit=crop')
        ]
        c.executemany("INSERT INTO products (name, description, source_port, image_url) VALUES (?, ?, ?, ?)", products_data)

    # Seed admin user if not exists
    c.execute("SELECT count(*) FROM users WHERE username = 'admin'")
    if c.fetchone()[0] == 0:
        admin_pass = "admin123"
        hashed_password = bcrypt.hashpw(admin_pass.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", ('admin', hashed_password, 'admin'))

    conn.commit()

# --- USER AUTHENTICATION & DATA FUNCTIONS ---
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

def validate_login(username, password):
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    if user and check_password(user['password_hash'].encode('utf-8'), password):
        return {'id': user['id'], 'username': user['username'], 'role': user['role']}
    return None

def get_all_products():
    conn = get_db_connection()
    return pd.read_sql_query("SELECT * FROM products", conn)

def log_product_interaction(user_id, product_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO product_interactions (user_id, product_id, view_timestamp) VALUES (?, ?, ?)",
              (user_id, product_id, datetime.datetime.now()))
    conn.commit()

def place_order(user_id, product_id, destination, quantity):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO orders (user_id, product_id, destination_city, quantity_barrels, order_date, status) VALUES (?, ?, ?, ?, ?, ?)",
              (user_id, product_id, destination, quantity, datetime.datetime.now(), 'Placed'))
    order_id = c.lastrowid
    # Log initial tracking status
    c.execute("INSERT INTO shipment_tracking (order_id, current_location, timestamp) VALUES (?, ?, ?)",
              (order_id, "Order confirmed. Awaiting dispatch from terminal.", datetime.datetime.now()))
    conn.commit()
    return order_id

def get_user_orders(user_id):
    conn = get_db_connection()
    query = """
    SELECT o.id, p.name as product_name, o.destination_city, o.quantity_barrels, o.order_date, o.status 
    FROM orders o JOIN products p ON o.product_id = p.id 
    WHERE o.user_id = ? ORDER BY o.order_date DESC
    """
    return pd.read_sql_query(query, conn, params=(user_id,))

def get_tracking_info(order_id):
    conn = get_db_connection()
    query = "SELECT current_location, timestamp FROM shipment_tracking WHERE order_id = ? ORDER BY timestamp DESC"
    return pd.read_sql_query(query, conn, params=(order_id,))

def get_all_orders_for_admin():
    conn = get_db_connection()
    query = """
    SELECT o.id, u.username, p.name as product_name, o.destination_city, o.quantity_barrels, o.order_date, o.status 
    FROM orders o 
    JOIN users u ON o.user_id = u.id 
    JOIN products p ON o.product_id = p.id 
    ORDER BY o.order_date DESC
    """
    return pd.read_sql_query(query, conn)

def get_product_interaction_analytics():
    conn = get_db_connection()
    query = """
    SELECT p.name, COUNT(pi.id) as view_count 
    FROM product_interactions pi 
    JOIN products p ON pi.product_id = p.id 
    GROUP BY p.name 
    ORDER BY view_count DESC
    """
    return pd.read_sql_query(query, conn)

def update_shipment_status(order_id, new_location, new_status):
    """Updates shipment location and status."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create a descriptive tracking message
    tracking_message = f"Status changed to '{new_status}': {new_location}"
    
    c.execute("INSERT INTO shipment_tracking (order_id, current_location, timestamp) VALUES (?, ?, ?)",
              (order_id, tracking_message, datetime.datetime.now()))
    
    # Update the master order status
    c.execute("UPDATE orders SET status = ? WHERE id = ?", (new_status, order_id))
    
    conn.commit()


# --- UI COMPONENTS ---

def login_register_page():
    """Displays the login and registration forms."""
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-form">', unsafe_allow_html=True)
    st.markdown("<h1>CrudeTrack 🚚</h1>", unsafe_allow_html=True)
    st.write(" ")

    choice = st.radio("", ["Login", "Register"], horizontal=True, label_visibility="collapsed")

    if choice == "Login":
        with st.form("login_form__"):
            username = st.text_input("Username", placeholder="Enter your username", label_visibility="collapsed")
            password = st.text_input("Password", type="password", placeholder="Enter your password", label_visibility="collapsed")
            st.write("")
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
        with st.form("register_form_"):
            new_username = st.text_input("Username", placeholder="Choose a username", label_visibility="collapsed")
            new_password = st.text_input("Password", type="password", placeholder="Choose a password", label_visibility="collapsed")
            st.write("")
            submitted = st.form_submit_button("Register")
            if submitted:
                if not new_username or not new_password:
                    st.warning("Please enter both username and password.")
                elif register_user(new_username, new_password):
                    st.success("Registration successful! Please login.")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Username already exists.")
    st.markdown('</div></div>', unsafe_allow_html=True)


def customer_portal():
    """The main view for logged-in customers."""
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
        
        # Initialize price data in session state to persist
        if 'price_data' not in st.session_state:
            st.session_state.price_data = pd.DataFrame({'Time': [datetime.datetime.now()], 'Price (USD)': [78.50]})

        last_price = st.session_state.price_data['Price (USD)'].iloc[-1]
        new_price = last_price + np.random.randn() * 0.15
        last_price = max(new_price, 60)
        new_row = pd.DataFrame({'Time': [datetime.datetime.now()], 'Price (USD)': [last_price]})
        st.session_state.price_data = pd.concat([st.session_state.price_data, new_row], ignore_index=True).tail(100)
        
        with price_chart_placeholder:
            st.line_chart(st.session_state.price_data.rename(columns={'Time':'index'}).set_index('index'))
        time.sleep(1)
        st.rerun()


    elif page == "🛢️ Products & Orders":
        st.header("🛢️ Our Products")
        
        products = get_all_products()
        
        # Log product views once per session to populate analytics data
        if 'products_viewed' not in st.session_state:
            for pid in products['id']:
                log_product_interaction(st.session_state['user_id'], pid)
            st.session_state['products_viewed'] = True

        cols = st.columns(len(products))
        for i, (_, row) in enumerate(products.iterrows()):
            with cols[i]:
                st.markdown('<div class="custom-card">', unsafe_allow_html=True)
                st.image(row['image_url'])
                st.subheader(row['name'])
                st.caption(f"Source: {row['source_port']}")
                st.write(row['description'])
                st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.header("📝 Place a New Order")
        st.markdown('<div class="custom-card">', unsafe_allow_html=True)
        with st.form("order_form"):
            col1, col2 = st.columns(2)
            with col1:
                selected_product_name = st.selectbox("Select Product", products['name'].tolist())
                quantity = st.number_input("Quantity (barrels)", min_value=100, step=100)
            with col2:
                destination = st.text_input("Destination City", placeholder="e.g., Rotterdam")
            
            # Use a div with a class to style the button
            st.markdown('<div class="stButton primary-btn" style="display: flex; justify-content: flex-end;">', unsafe_allow_html=True)
            submitted = st.form_submit_button("Place Your Order")
            st.markdown('</div>', unsafe_allow_html=True)

            if submitted:
                if not destination:
                    st.warning("Please enter a destination city.")
                else:
                    product_id = products[products['name'] == selected_product_name]['id'].iloc[0]
                    order_id = place_order(st.session_state['user_id'], product_id, destination, quantity)
                    st.success(f"🎉 Order placed successfully! Your Order ID is: **{order_id}**")
                    st.balloons()
        st.markdown('</div>', unsafe_allow_html=True)


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
    """The main view for logged-in admins."""
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
        kpi1.metric("Total Orders Placed", f"{total_orders}")
        kpi2.metric("Total Barrels Ordered", f"{total_barrels:,}")
        kpi3.metric("Most Viewed Product", most_popular_product)
        
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
            
            st.markdown('<div class="custom-card">', unsafe_allow_html=True)
            with st.form("update_shipment_form"):
                col1, col2, col3 = st.columns([1, 2, 1])
                with col1:
                    order_ids = orders_df['id'].tolist()
                    selected_order_id = st.selectbox("Order ID", order_ids, label_visibility="collapsed")
                with col2:
                    new_location = st.text_input("New Location / Status Update", placeholder="e.g., 'Passing through Suez Canal'", label_visibility="collapsed")
                with col3:
                    status_options = ['Placed', 'In Transit', 'Delayed', 'Delivered', 'Cancelled']
                    new_status = st.selectbox("Status", status_options, label_visibility="collapsed")
                
                submitted = st.form_submit_button("Update Status")
                if submitted:
                    if not new_location:
                        st.warning("Please provide a location/status update message.")
                    else:
                        update_shipment_status(selected_order_id, new_location, new_status)
                        st.success(f"Status for Order #{selected_order_id} updated.")
                        st.rerun() # Rerun to show updated table
            st.markdown('</div>', unsafe_allow_html=True)

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
