import json
from datetime import datetime

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Campus Cafeteria",
    page_icon="🍽️",
    layout="wide"
)


# =========================================================
# FIREBASE CONNECTION
# =========================================================

@st.cache_resource
def initialize_firebase():

    try:
        firebase_json = json.loads(st.secrets["firebase_json"])

        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_json)
            firebase_admin.initialize_app(cred)

        return firestore.client(), True

    except Exception as e:
        return None, False


db, firebase_connected = initialize_firebase()


# =========================================================
# MENU
# =========================================================

MENU = {
    "Tea": {
        "price": 15,
        "status": "Ready"
    },
    "Sandwich": {
        "price": 40,
        "status": "Prepared"
    },
    "Maggi": {
        "price": 35,
        "status": "Prepared"
    },
    "Cold Coffee": {
        "price": 30,
        "status": "Ready"
    },
    "Veg Roll": {
        "price": 45,
        "status": "Prepared"
    },
    "Water Bottle": {
        "price": 20,
        "status": "Ready"
    }
}


# =========================================================
# SESSION STATE
# =========================================================

if "page" not in st.session_state:
    st.session_state.page = "home"

if "cart" not in st.session_state:
    st.session_state.cart = {}

if "order_id" not in st.session_state:
    st.session_state.order_id = None

if "last_order" not in st.session_state:
    st.session_state.last_order = None


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def add_to_cart(item):

    if item not in st.session_state.cart:
        st.session_state.cart[item] = 1
    else:
        st.session_state.cart[item] += 1


def remove_from_cart(item):

    if item in st.session_state.cart:

        st.session_state.cart[item] -= 1

        if st.session_state.cart[item] <= 0:
            del st.session_state.cart[item]


def cart_total():

    total = 0

    for item, quantity in st.session_state.cart.items():
        total += MENU[item]["price"] * quantity

    return total


def clear_cart():

    st.session_state.cart = {}


# =========================================================
# HOME PAGE
# =========================================================

def home_page():

    st.title("🍽️ Campus Cafeteria")

    st.subheader("Skip the queue. Order before you reach the cafeteria.")

    st.write(
        "Choose your portal below."
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("### 🎓 Student Portal")

        st.write(
            "Browse the menu, place your order and collect it using your Order ID."
        )

        if st.button(
            "Order Food →",
            use_container_width=True
        ):
            st.session_state.page = "student"
            st.rerun()

    with col2:

        st.markdown("### 👨‍🍳 Cafeteria Portal")

        st.write(
            "View today's orders and manage order collection."
        )

        if st.button(
            "Cafeteria Dashboard →",
            use_container_width=True
        ):
            st.session_state.page = "cafeteria"
            st.rerun()


# =========================================================
# STUDENT PAGE
# =========================================================

def student_page():

    st.title("🎓 Student Ordering")

    if st.button("← Back to Home"):
        st.session_state.page = "home"
        st.rerun()

    st.divider()

    # -----------------------------------------------------
    # STUDENT DETAILS
    # -----------------------------------------------------

    st.subheader("1. Student Details")

    col1, col2 = st.columns(2)

    with col1:
        student_name = st.text_input(
            "Student Name",
            placeholder="Enter your name"
        )

    with col2:
        student_id = st.text_input(
            "Student ID",
            placeholder="Enter your student ID"
        )

    # -----------------------------------------------------
    # ORDER TYPE
    # -----------------------------------------------------

    st.subheader("2. Order Type")

    order_type = st.radio(
        "Choose how you want to order",
        [
            "Break Order",
            "Regular Order"
        ],
        horizontal=True
    )

    break_time = None

    if order_type == "Break Order":

        break_time = st.selectbox(
            "Select Break",
            [
                "Break 1 — 1:00 PM to 1:30 PM",
                "Break 2 — 4:00 PM to 4:30 PM"
            ]
        )

        st.info(
            "💡 Break orders are prepared in advance. "
            "Once confirmed, simply collect them during your selected break."
        )

    else:

        st.info(
            "💡 Regular orders follow the full preparation workflow."
        )

    # -----------------------------------------------------
    # MENU
    # -----------------------------------------------------

    st.subheader("3. Menu")

    menu_items = list(MENU.keys())

    for i in range(0, len(menu_items), 3):

        cols = st.columns(3)

        for j, col in enumerate(cols):

            if i + j >= len(menu_items):
                continue

            item = menu_items[i + j]

            with col:

                st.markdown(
                    f"""
                    ### {item}

                    **₹{MENU[item]["price"]}**

                    Preparation: {MENU[item]["status"]}
                    """
                )

                if item in st.session_state.cart:

                    quantity = st.session_state.cart[item]

                    c1, c2, c3 = st.columns(3)

                    with c1:
                        if st.button(
                            "−",
                            key=f"minus_{item}",
                            use_container_width=True
                        ):
                            remove_from_cart(item)
                            st.rerun()

                    with c2:
                        st.markdown(
                            f"<h3 style='text-align:center'>{quantity}</h3>",
                            unsafe_allow_html=True
                        )

                    with c3:
                        if st.button(
                            "+",
                            key=f"plus_{item}",
                            use_container_width=True
                        ):
                            add_to_cart(item)
                            st.rerun()

                else:

                    if st.button(
                        "Add to Cart",
                        key=f"add_{item}",
                        use_container_width=True
                    ):
                        add_to_cart(item)
                        st.rerun()

    # -----------------------------------------------------
    # CART
    # -----------------------------------------------------

    st.divider()

    st.subheader("🛒 Your Cart")

    if not st.session_state.cart:

        st.info("Your cart is empty. Add something from the menu.")

    else:

        for item, quantity in st.session_state.cart.items():

            item_total = MENU[item]["price"] * quantity

            col1, col2, col3 = st.columns([4, 2, 2])

            with col1:
                st.write(f"**{item}**")

            with col2:
                st.write(f"× {quantity}")

            with col3:
                st.write(f"₹{item_total}")

        st.divider()

        total = cart_total()

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Total")

        with col2:
            st.markdown(f"### ₹{total}")

        if st.button(
            "🗑️ Clear Cart",
            use_container_width=True
        ):
            clear_cart()
            st.rerun()

    # -----------------------------------------------------
    # PLACE ORDER
    # -----------------------------------------------------

    st.divider()

    if st.session_state.cart:

        if st.button(
            "🍽️ Place Order",
            type="primary",
            use_container_width=True
        ):

            if not student_name.strip():

                st.error("Please enter your name.")

            elif not student_id.strip():

                st.error("Please enter your Student ID.")

            else:

                # Temporary Order ID
                # We will replace this with a proper daily
                # sequential Firestore counter later.

                order_id = datetime.now().strftime("%H%M%S")

                order_data = {

                    "order_id": order_id,

                    "student_name": student_name,

                    "student_id": student_id,

                    "order_type": order_type,

                    "break_time": break_time,

                    "items": dict(st.session_state.cart),

                    "total": cart_total(),

                    "status": (
                        "Confirmed"
                        if order_type == "Break Order"
                        else "Ready"
                        if all(
                            MENU[item]["status"] == "Ready"
                            for item in st.session_state.cart
                        )
                        else "Confirmed"
                    ),

                    "date": datetime.now().strftime("%Y-%m-%d"),

                    "created_at": datetime.now()
                }

                # Save to Firestore

                try:

                    if db is not None:

                        db.collection("orders").add(order_data)

                    st.session_state.order_id = order_id

                    st.session_state.last_order = order_data

                    clear_cart()

                    st.session_state.page = "confirmation"

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Could not place order: {e}"
                    )


# =========================================================
# CONFIRMATION PAGE
# =========================================================

def confirmation_page():

    order = st.session_state.last_order

    st.title("✅ Order Confirmed!")

    if order:

        st.success(
            f"Your Order ID is **#{order['order_id']}**"
        )

        st.markdown(
            "### Show this Order ID at the cafeteria counter."
        )

        st.divider()

        st.subheader("Order Details")

        st.write(
            f"**Student:** {order['student_name']}"
        )

        st.write(
            f"**Order Type:** {order['order_type']}"
        )

        if order["break_time"]:
            st.write(
                f"**Break:** {order['break_time']}"
            )

        st.divider()

        st.subheader("Items")

        for item, quantity in order["items"].items():

            price = MENU[item]["price"] * quantity

            st.write(
                f"{item} × {quantity} — ₹{price}"
            )

        st.divider()

        st.markdown(
            f"## Total: ₹{order['total']}"
        )

        st.info(
            f"📌 Your Order ID: **#{order['order_id']}**"
        )

    if st.button(
        "Place Another Order",
        use_container_width=True
    ):

        st.session_state.page = "student"
        st.rerun()

    if st.button(
        "Back to Home",
        use_container_width=True
    ):

        st.session_state.page = "home"
        st.rerun()


# =========================================================
# CAFETERIA DASHBOARD
# =========================================================

def cafeteria_page():

    st.title("👨‍🍳 Cafeteria Dashboard")

    if st.button("← Back to Home"):
        st.session_state.page = "home"
        st.rerun()

    st.divider()

    if firebase_connected:

        st.success(
            "🟢 Firebase connected successfully"
        )

    else:

        st.error(
            "🔴 Firebase connection failed"
        )

    st.subheader("Today's Orders")

    try:

        orders_ref = db.collection("orders").stream()

        orders = []

        today = datetime.now().strftime("%Y-%m-%d")

        for doc in orders_ref:

            data = doc.to_dict()

            if data.get("date") == today:

                orders.append(data)

        if not orders:

            st.info("No orders yet today.")

        else:

            for order in orders:

                st.markdown(
                    f"""
                    ### #{order.get("order_id")}

                    **Student:** {order.get("student_name")}

                    **Items:** {order.get("items")}

                    **Total:** ₹{order.get("total")}

                    **Status:** {order.get("status")}
                    """
                )

                st.divider()

    except Exception as e:

        st.error(
            f"Could not load orders: {e}"
        )


# =========================================================
# PAGE ROUTING
# =========================================================

if st.session_state.page == "home":

    home_page()

elif st.session_state.page == "student":

    student_page()

elif st.session_state.page == "confirmation":

    confirmation_page()

elif st.session_state.page == "cafeteria":

    cafeteria_page()
