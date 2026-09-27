import json
from datetime import datetime

import streamlit as st
import pandas as pd

import firebase_admin
from firebase_admin import credentials, firestore


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Campus Cafeteria",
    page_icon="🍽️",
    layout="wide"
)


# ============================================================
# FIREBASE CONNECTION
# ============================================================

@st.cache_resource
def initialize_firebase():
    firebase_data = json.loads(st.secrets["firebase_json"])

    if not firebase_admin._apps:
        cred = credentials.Certificate(firebase_data)
        firebase_admin.initialize_app(cred)

    return firestore.client()


try:
    db = initialize_firebase()
    firebase_connected = True
except Exception as e:
    db = None
    firebase_connected = False
    firebase_error = str(e)


# ============================================================
# SESSION STATE
# ============================================================

if "page" not in st.session_state:
    st.session_state.page = "home"

if "cart" not in st.session_state:
    st.session_state.cart = []

if "order_confirmed" not in st.session_state:
    st.session_state.order_confirmed = False

if "order_id" not in st.session_state:
    st.session_state.order_id = None


# ============================================================
# SAMPLE MENU
# ============================================================

MENU = [
    {
        "name": "Tea",
        "price": 15,
        "type": "Ready"
    },
    {
        "name": "Sandwich",
        "price": 40,
        "type": "Prepared"
    },
    {
        "name": "Maggi",
        "price": 35,
        "type": "Prepared"
    },
    {
        "name": "Cold Coffee",
        "price": 30,
        "type": "Ready"
    },
    {
        "name": "Veg Roll",
        "price": 45,
        "type": "Prepared"
    },
    {
        "name": "Water Bottle",
        "price": 20,
        "type": "Ready"
    }
]


# ============================================================
# HOME PAGE
# ============================================================

if st.session_state.page == "home":

    st.title("🍽️ Campus Cafeteria")
    st.subheader("Pre-Order & Queue Management System")

    st.divider()

    st.header("👋 Welcome")
    st.write(
        "Order your food before reaching the cafeteria, "
        "avoid unnecessary waiting and collect your order easily."
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.header("👨‍🎓 Student Portal")
        st.write(
            "View today's menu, place an order and receive your Order ID."
        )

        if st.button(
            "🍽️ Order Food",
            type="primary",
            use_container_width=True
        ):
            st.session_state.page = "student"
            st.rerun()

    with col2:
        st.header("👨‍🍳 Cafeteria Portal")
        st.write(
            "Cafeteria staff can manage orders and the menu."
        )

        if st.button(
            "👨‍🍳 Cafeteria Dashboard",
            use_container_width=True
        ):
            st.session_state.page = "cafeteria"
            st.rerun()


# ============================================================
# STUDENT PORTAL
# ============================================================

elif st.session_state.page == "student":

    st.title("🍽️ Student Ordering")

    if st.button("← Back to Home"):
        st.session_state.page = "home"
        st.rerun()

    st.divider()

    # Student details
    st.subheader("Student Details")

    student_name = st.text_input(
        "Student Name"
    )

    student_id = st.text_input(
        "Student ID"
    )

    # Order type
    order_type = st.radio(
        "Order Type",
        [
            "Break Order",
            "Regular Order"
        ],
        horizontal=True
    )

    # Break selection
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
            "Your order will be prepared for the selected break. "
            "Once confirmed, simply collect it using your Order ID."
        )

    else:

        st.info(
            "Regular orders can be placed whenever the cafeteria is open."
        )

    st.divider()

    # Menu
    st.subheader("Today's Menu")

    for item in MENU:

        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.write(f"**{item['name']}**")

            if item["type"] == "Ready":
                st.caption("Ready item")
            else:
                st.caption("Prepared item")

        with col2:
            st.write(f"₹{item['price']}")

        with col3:

            if st.button(
                "Add",
                key=f"add_{item['name']}"
            ):

                st.session_state.cart.append(item)
                st.success(f"{item['name']} added")

    st.divider()

    # Cart
    st.subheader("🛒 Your Cart")

    if len(st.session_state.cart) == 0:

        st.info("Your cart is empty.")

    else:

        total = 0

        for item in st.session_state.cart:

            st.write(
                f"- {item['name']} — ₹{item['price']}"
            )

            total += item["price"]

        st.markdown(f"### Total: ₹{total}")

        if st.button(
            "Clear Cart"
        ):
            st.session_state.cart = []
            st.rerun()

        st.divider()

        if st.button(
            "✅ Confirm Order",
            type="primary",
            use_container_width=True
        ):

            if not student_name or not student_id:

                st.error(
                    "Please enter your Student Name and Student ID."
                )

            else:

                # Temporary Order ID
                temporary_order_id = datetime.now().strftime(
                    "%H%M%S"
                )

                st.session_state.order_id = temporary_order_id

                # Regular ready items can directly become Ready
                if order_type == "Regular Order":

                    all_ready = all(
                        item["type"] == "Ready"
                        for item in st.session_state.cart
                    )

                    initial_status = (
                        "Ready"
                        if all_ready
                        else "Confirmed"
                    )

                else:

                    # Break orders only use Confirmed
                    initial_status = "Confirmed"

                # Create order data
                order_data = {

                    "order_id": temporary_order_id,

                    "date": datetime.now().strftime(
                        "%Y-%m-%d"
                    ),

                    "student_name": student_name,

                    "student_id": student_id,

                    "order_type": order_type,

                    "break_time": break_time,

                    "items": [
                        {
                            "name": item["name"],
                            "price": item["price"]
                        }
                        for item in st.session_state.cart
                    ],

                    "amount": total,

                    "status": initial_status,

                    "created_at": firestore.SERVER_TIMESTAMP
                }

                # Save order to Firestore
                try:

                    db.collection("orders").add(order_data)

                    st.session_state.order_confirmed = True

                    # IMPORTANT:
                    # Move to confirmation page
                    # so the student doesn't remain
                    # on the ordering page.
                    st.session_state.page = "confirmation"

                    st.rerun()

                except Exception as e:

                    st.error(
                        "Could not place the order."
                    )

                    st.error(
                        f"Firebase error: {e}"
                    )


# ============================================================
# ORDER CONFIRMATION
# ============================================================

elif st.session_state.page == "confirmation":

    st.title("🎉 Order Confirmed!")

    st.success(
        "Your order has been successfully placed."
    )

    st.divider()

    st.metric(
        "Your Order ID",
        st.session_state.order_id
    )

    st.info(
        "Please remember your Order ID and show it at "
        "the cafeteria when collecting your food."
    )

    if st.button(
        "🍽️ Place Another Order",
        use_container_width=True
    ):

        st.session_state.cart = []
        st.session_state.order_confirmed = False
        st.session_state.order_id = None
        st.session_state.page = "student"

        st.rerun()

    if st.button(
        "← Back to Home",
        use_container_width=True
    ):

        st.session_state.cart = []
        st.session_state.order_confirmed = False
        st.session_state.order_id = None
        st.session_state.page = "home"

        st.rerun()


# ============================================================
# CAFETERIA PORTAL
# ============================================================

elif st.session_state.page == "cafeteria":

    st.title("👨‍🍳 Cafeteria Dashboard")

    if st.button("← Back to Home"):
        st.session_state.page = "home"
        st.rerun()

    st.divider()

    # Firebase connection status
    if firebase_connected:

        st.success(
            "🟢 Firebase connected successfully"
        )

    else:

        st.error(
            "🔴 Firebase connection failed"
        )

        st.code(
            firebase_error
        )

    st.subheader("Today's Orders")

    # Get orders from Firestore
    try:

        orders_ref = db.collection("orders")

        orders = orders_ref.stream()

        order_list = []

        for doc in orders:

            order = doc.to_dict()

            order_list.append({

                "Order ID": order.get(
                    "order_id",
                    ""
                ),

                "Student": order.get(
                    "student_name",
                    ""
                ),

                "Student ID": order.get(
                    "student_id",
                    ""
                ),

                "Order Type": order.get(
                    "order_type",
                    ""
                ),

                "Amount": order.get(
                    "amount",
                    0
                ),

                "Status": order.get(
                    "status",
                    ""
                )

            })

        if order_list:

            df = pd.DataFrame(
                order_list
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

        else:

            st.info(
                "No orders have been placed yet."
            )

    except Exception as e:

        st.error(
            f"Could not load orders: {e}"
        )
