import streamlit as st
import mysql.connector
from dbconfig import DB_CONFIG
from datetime import datetime
import re
import pandas as pd


def init_db():

    conn = mysql.connector.connect(**DB_CONFIG)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS mohit (
            id INTEGER PRIMARY KEY AUTO_INCREMENT,
            name TEXT,
            mob TEXT,
            address TEXT,
            items TEXT,
            total FLOAT,
            datetime DATETIME
        )
    """)
    conn.commit()
    conn.close()

def insert_order(name, mob, address, items, total):
    
    
    conn = mysql.connector.connect(**DB_CONFIG)
    c = conn.cursor()

    c.execute("INSERT INTO mohit (name, mob, address, items, total, datetime) VALUES (%s, %s, %s, %s, %s, %s)",
              (name, mob, address, items, total, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_orders():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mohit ORDER BY id DESC")
    fdata = cursor.fetchall()
    conn.close()
    return fdata


def get_latest_order(mob):
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT *
        FROM mohit
        WHERE mob = %s
        ORDER BY datetime DESC
        LIMIT 1
    """, (mob,))  
    row = cursor.fetchone()
    conn.close()
    if row:    
        return {    
            "name": row[1],
            "mob": row[2],
            "address": row[3],
            "items": row[4],
            "total": row[5],
            "datetime": row[6]
        }
    else:
        return None



st.set_page_config(page_title="Restaurant App", layout="wide")
init_db()


col1, col2, col3 = st.columns([1, 3, 1])

with col1:
    st.image(r"hologo.jpg",width="stretch")

with col2:
    st.markdown("<h1 style='text-align: center; color: brown; font-size:50px;'>🍴 DAGAR HOTEL 🍴</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center;font-size:40px;text-decoration:underline;'>Welcome to our restaurant</h4>", unsafe_allow_html=True)

with col3:
    st.image(r"hologo.jpg",width="stretch")

st.markdown("---")

st.sidebar.image(r"fudlogo.jpg")


if "menu" not in st.session_state:
    st.session_state["menu"] = "Menu"


menu_options = ["Menu", "Payment","My Order", "Admin"]
if "user_details" in st.session_state:
    menu_options.insert(2, "Confirm Payment")


st.session_state["menu"] = st.sidebar.radio("Navigate", menu_options, index=menu_options.index(st.session_state["menu"]))


menu = st.session_state["menu"]




with st.sidebar.expander("ℹ️ About Us / Contact"):
    st.write("**🍴 DAGAR HOTEL**")
    st.write("📍 Location:Nuh road,Mandkola")
    st.write("📞 Phone:[+91-8168879243,8295941711]")
    
    st.write("⏰ Timing: 11 AM - 12 PM")




if menu == "Menu":
    st.subheader("📖 Menu Card")

   

    curry_items = {
        "Matar Paneer(Half)":70,
        "Matar Paneer(Full)":130,
        "Kadhai Paneer(Half)":100,
        "Kadhai Paneer(Full)": 180,
        "Mix Veg(Half)":100,
        "Mix Veg(Full)": 180,
        "Shahi Paneer(half)": 80,
        "Shahi Paneer(Full)":150,
        "Butter Paneer Masala(Half)": 130,
        "Butter Paneer Masala(Full)": 230,
        "Paneer Bhurji(Half)": 180,
        "Paneer Bhurji(Full)":300,
        "Matar Mushroom(Half)":70,
        "Matar Mushroom(Full)": 130,
        "Sev Bhurji":120,
        "Dal Makhani(Half)": 70,
        "Dal Makhani(Full)": 120,
        "Dal Tadka(Half)": 50,
        "Dal Tadka(Full)":80,
        "Amritsari Chhole(Half)": 70,
        "Amritsari Chhole(Full)":120,
        "Chana Masala": 180
    }

    roti_items = {
        "Sadha Roti":10,
        "Butter Roti":15,
        "Pyaj Roti": 15,
        "Butter Pyaj Roti": 20,
        "Missi Roti":20,
        "Butter Missi Roti": 25,
        "Garlic Nan":25,
        "Butter Garlic Nan": 30,
        "Butter Nan": 30,
        "Sadha Nan": 20,
        "Aloo Nan": 30,
        "Butter Aloo Nan": 40,
        "Paneer Nan": 50,
        "Butter Paneer Nan":60
    }

    beverage_items = {
        "Raita": 50,
        "Dahi": 50,
        "Water Bottle":20,
        "Cold drink":50,
        "Mix Salad":30,
        "Green Salad": 60
                }
    st.subheader("Select Items")
    selected_items = []
    total = 0

    def show_menu_section(title, items_dict):
        global total
        st.markdown(f"### {title}")
        for item, price in items_dict.items():
            qty = st.number_input(f"{item} (₹{price})", min_value=0, max_value=10, step=1, key=item)
            if qty > 0:
                selected_items.append(f"{item} x{qty}")
                total += price * qty

    
   
    
    col1, col2,col3 = st.columns(3)
    with col1:
        st.image("sahipnr_re.jpg", caption="Matar Mushroom")
    with col2:
        st.image("shipnr.jpg", caption="Sahi Paneer")
    with col3:
        st.image("dal.jpg", caption="Dal")

    show_menu_section("🍛 Curry Items", curry_items)

    st.markdown("----")
    col1, col2,col3 = st.columns(3)
    with col1:
        st.image("roti.jpg", caption="Sadha Roti")
    with col2:
        st.image("tndroti.jpg", caption="Tandoori Roti")
    with col3:
        st.image("prntha.jpg", caption="Parantha")

    show_menu_section("🍞 Roti Items", roti_items)

    st.markdown("----")
    col1, col2,col3 = st.columns(3)
    with col1:
        st.image("dahi.jpg", caption="Lassi")
    with col2:
        st.image("coc.jpg", caption="Cold drink")
    with col3:
        st.image("chai.jpg", caption="Tea")

    show_menu_section("🥤 Beverages", beverage_items)

    st.write(f"### 🧾 Total: ₹{total}")


    
    if total < 200:
        st.warning("⚠️ Minimum order amount is ₹200 to proceed to payment.")
        st.button("Proceed to Payment", disabled=True)
    else:
        if st.button("Proceed to Payment"):
                
            st.session_state["cart"] = {"items": selected_items, "total": total}
             
            st.session_state["menu"] = "Payment"
            st.stop()    
            



elif menu == "Payment":
    st.subheader("💳 Payment")
    if "order_saved" not in st.session_state:
        st.session_state["order_saved"] = False


    if "cart" not in st.session_state:
        st.warning("No items selected. Please go to Menu first.")
    else:
        cart = st.session_state["cart"]
        st.write("### Items Ordered")
        st.write(", ".join(cart["items"]))
        st.write(f"### Total: ₹{cart['total']}")

        st.subheader("Enter Your Details")
        name = st.text_input("Name")
        mob = st.text_input("Mobile")
        address = st.text_area("Address")

        if st.button("Pay & Place Order"):

            if st.session_state.get("order_saved", False):
                st.warning("⚠️ Order already placed. Proceed to payment.")
                st.session_state["menu"] = "Confirm Payment"
                st.stop()

            elif not re.match(r'^[6-9]\d{9}$', mob):
                st.warning("⚠️ Invalid mobile number.")
            else:
                
                if name and mob and address:
                    
                    insert_order(name, mob, address, ", ".join(cart["items"]), cart["total"])
                    st.success("✅ Order details saved. Please proceed to payment.")

                    
                    st.session_state["order_saved"] = True

                    st.session_state["user_details"] = {
                        "name": name,
                        "mob": mob,
                        "address": address,
                    }
                st.session_state["menu"] = "Confirm Payment"
                st.stop()

            st.balloons()


elif menu == "Confirm Payment":
    st.subheader("✅ Confirm Your Payment")

    
    if "cart" not in st.session_state or "user_details" not in st.session_state:
        st.warning("Please complete the payment form first.")
        st.stop()

    st.image("hoscan1.jpg", width=300)
    st.markdown("----")
    st.markdown("**UPI ID:** `paytmqr51bzf8@ptys`")
    st.markdown("---")
    

    if st.button("✅ Done"):
        
        st.success("Thank you for your order.Please wait 30 mins and keep a solid proof of payment")

        
        st.session_state.pop("cart", None)
        st.session_state.pop("user_details", None)

        
        st.session_state["menu"] = "Menu"
        st.stop()

elif menu == "My Order":
    st.subheader("📋 My Latest Order")

    
    mob = st.text_input("Enter your registered mobile number:")

    if mob:
        latest_order = get_latest_order(mob)

        if latest_order:
            st.write(f"🧑‍💼 **Name:** {latest_order['name']}")
            st.write(f"📱 **Mobile:** {latest_order['mob']}")
            st.write(f"🏠 **Address:** {latest_order['address']}")
            st.write(f"🛒 **Items:** {latest_order['items']}")
            st.write(f"💰 **Total:** ₹{latest_order['total']}")
            st.write(f"📍 **DateTime:** {latest_order['datetime']}")
        else:
            st.info("No recent order found for this number.")
    else:
        st.warning("Please enter your mobile number.")



elif menu == "Admin":
    st.subheader("🔑 Admin Login")

    admin_user = "admin"
    admin_pass = "1234"

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == admin_user and password == admin_pass:
            st.success("✅ Logged in as Admin")
            ordrs = get_orders()
            if ordrs:
                df = pd.DataFrame(ordrs, columns=["ID", "Name", "Mobile", "Address", "Items", "Total", "DateTime"])
                df["Items"] = df["Items"].apply(lambda x: ', '.join(x) if isinstance(x, list) else x)

                
                df.set_index("ID", inplace=True)

                st.subheader("📋 All Orders")
                st.dataframe(df, use_container_width=True)


            else:
                st.write("No orders found.")
        else:
            st.error("❌ Invalid credentials")

        st.session_state["menu"] = "Menu"
        st.stop()