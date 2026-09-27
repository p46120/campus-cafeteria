import streamlit as st
from datetime import datetime

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Campus Cafeteria",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --------------------------------------------------
# SAMPLE MENU
# --------------------------------------------------

menu = [
    {
        "id": 1,
        "name": "Tea",
        "price": 15,
        "type": "Ready",
        "description": "Freshly prepared tea"
    },
    {
        "id": 2,
        "name": "Sandwich",
        "price": 40,
        "type": "Prepared",
        "description": "Fresh vegetable sandwich"
    },
    {
        "id": 3,
        "name": "Maggi",
        "price": 35,
        "type": "Prepared",
        "description": "Hot Maggi noodles"
    },
    {
        "id": 4,
        "name": "Cold Coffee",
        "price": 30,
        "type": "Ready",
        "description": "Chilled coffee"
    },
    {
        "id": 5,
        "name": "Veg Roll",
        "price": 45,
        "type": "Prepared",
        "description": "Fresh vegetable roll"
    },
    {
        "id": 6,
        "name": "Water Bottle",
        "price": 20,
        "type": "Ready",
        "description": "Packaged drinking water"
    }
]

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "page" not in st.session_state:
    st.session_state.page = "home"

if "cart" not in st.session_state:
    st.session_state.cart = {}

if "order_confirmed" not in st.session_state:
    st.session_state.order_confirmed = False

if "order_id" not in st.session_state:
    st.session_state.order_id = None

# --------------------------------------------------
# BASIC STYLING
# --------------------------------------------------

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }

    .sub-title {
        font-size: 1.1rem;
        color: #64748b;
    }

    .item-name {
        font-size: 1.2rem;
        font-weight: 650;
    }

    .price {
        font-size: 1.05rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --------------------------------------------------
# HOME PAGE
# --------------------------------------------------

if st.session_state.page == "home":

    st.markdown(
        '<div class="main-title">🍽️ Campus Cafeteria</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub-title">Pre-Order & Queue Management System</div>',
        unsafe_allow_html=True
    )

    st.divider()

    st.markdown("### 👋 Welcome")

    st.write(
        """
        Order your food before reaching the cafeteria,
        avoid unnecessary waiting and collect your order easily.
        """
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 👨‍🎓 Student Portal")
        st.write(
            "View today's menu, place an order and receive your Order ID."
        )

        if st.button(
            "🍽️ Order Food",
            use_container_width=True,
            type="primary"
        ):
            st.session_state.page = "student"
            st.rerun()

    with col2:
        st.markdown("### 👨‍🍳 Cafeteria Portal")
        st.write(
            "Cafeteria staff can manage orders and the menu."
        )

        if st.button(
            "👨‍🍳 Cafeteria Dashboard",
            use_container_width=True
        ):
            st.session_state.page = "cafeteria"
            st.rerun()

# --------------------------------------------------
# STUDENT PORTAL
# --------------------------------------------------

elif st.session_state.page == "student":

    if st.button("← Back to Home"):
        st.session_state.page = "home"
        st.rerun()

    st.markdown(
        '<div class="main-title">🍽️ Student Portal</div>',
        unsafe_allow_html=True
    )

    st.caption("Order your food before reaching the cafeteria.")

    st.divider()

    # --------------------------------------------------
    # STUDENT INFORMATION
    # --------------------------------------------------

    st.markdown("### 👤 Student Information")

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

    st.divider()

    # --------------------------------------------------
    # ORDER TYPE
    # --------------------------------------------------

    st.markdown("### 🕐 Choose Order Type")

    order_type = st.radio(
        "How would you like to order?",
        [
            "🕐 Break Order",
            "🍽️ Regular Order"
        ],
        horizontal=True
    )

    if order_type == "🕐 Break Order":

        st.info(
            """
            **Break Order:** Place your order before the class break.
            Your order will be confirmed and will be available for
            collection during the selected break.
            """
        )

        break_time = st.selectbox(
            "Select Break",
            [
                "Break 1 — 1:00 PM to 1:30 PM",
                "Break 2 — 4:00 PM to 4:30 PM"
            ]
        )

    else:

        st.info(
            """
            **Regular Order:** Place your order whenever the cafeteria
            is open. The cafeteria will prepare the order for collection.
            """
        )

    st.divider()

    # --------------------------------------------------
    # MENU
    # --------------------------------------------------

    st.markdown("### 🍴 Today's Menu")

    for item in menu:

        col1, col2, col3 = st.columns([4, 1.5, 1.5])

        with col1:

            st.markdown(
                f'<div class="item-name">{item["name"]}</div>',
                unsafe_allow_html=True
            )

            st.caption(
                f'{item["description"]} • {item["type"]}'
            )

        with col2:

            st.markdown(
                f'<div class="price">₹{item["price"]}</div>',
                unsafe_allow_html=True
            )

        with col3:

            if st.button(
                "Add",
                key=f"add_{item['id']}",
                use_container_width=True
            ):

                if item["id"] not in st.session_state.cart:
                    st.session_state.cart[item["id"]] = 1
                else:
                    st.session_state.cart[item["id"]] += 1

                st.rerun()

        st.divider()

    # --------------------------------------------------
    # CART
    # --------------------------------------------------

    st.markdown("### 🛒 Your Cart")

    if not st.session_state.cart:

        st.info("Your cart is empty. Add something from the menu.")

    else:

        total = 0

        for item in menu:

            item_id = item["id"]

            if item_id in st.session_state.cart:

                quantity = st.session_state.cart[item_id]

                subtotal = item["price"] * quantity

                total += subtotal

                col1, col2, col3, col4 = st.columns(
                    [4, 1, 1, 1]
                )

                with col1:
                    st.write(
                        f"**{item['name']}**"
                    )

                with col2:
                    st.write(
                        f"₹{item['price']}"
                    )

                with col3:
                    st.write(
                        f"Qty: {quantity}"
                    )

                with col4:

                    if st.button(
                        "Remove",
                        key=f"remove_{item_id}"
                    ):

                        del st.session_state.cart[item_id]
                        st.rerun()

        st.divider()

        st.markdown(
            f"### Total: ₹{total}"
        )

        # --------------------------------------------------
        # CONFIRM ORDER
        # --------------------------------------------------

        if not student_name or not student_id:

            st.warning(
                "Please enter your name and Student ID before placing the order."
            )

        else:

            if st.button(
                "✅ Confirm Order",
                use_container_width=True,
                type="primary"
            ):

                # Temporary order ID.
                # Firebase will handle real daily IDs later.
                current_time = datetime.now()

                temporary_id = current_time.strftime("%H%M%S")

                st.session_state.order_id = temporary_id
                st.session_state.order_confirmed = True

                st.rerun()

# --------------------------------------------------
# ORDER CONFIRMATION
# --------------------------------------------------

elif st.session_state.order_confirmed:

    st.markdown(
        '<div class="main-title">🎉 Order Confirmed!</div>',
        unsafe_allow_html=True
    )

    st.success(
        "Your order has been successfully placed."
    )

    st.divider()

    st.metric(
        "Your Order ID",
        st.session_state.order_id
    )

    st.write(
        """
        Please remember your **Order ID** and show it at the
        cafeteria when collecting your food.
        """
    )

    st.info(
        "This Order ID system is temporary for testing. "
        "We will replace it with a proper daily sequential Order ID "
        "when we connect Firebase."
    )

    st.divider()

    st.markdown("### 📋 Order Details")

    for item in menu:

        item_id = item["id"]

        if item_id in st.session_state.cart:

            quantity = st.session_state.cart[item_id]

            st.write(
                f"**{item['name']} × {quantity}**"
            )

    st.divider()

    if st.button(
        "🏠 Back to Home",
        use_container_width=True
    ):

        st.session_state.cart = {}
        st.session_state.order_confirmed = False
        st.session_state.order_id = None
        st.session_state.page = "home"

        st.rerun()

# --------------------------------------------------
# CAFETERIA PORTAL — TEMPORARY
# --------------------------------------------------

elif st.session_state.page == "cafeteria":

    if st.button("← Back to Home"):
        st.session_state.page = "home"
        st.rerun()

    st.markdown(
        '<div class="main-title">👨‍🍳 Cafeteria Dashboard</div>',
        unsafe_allow_html=True
    )

    st.caption(
        "Order management dashboard — database connection will be added next."
    )

    st.divider()

    st.info(
        """
        The cafeteria dashboard will allow staff to:
        
        • View today's orders  
        • Manage break and regular orders  
        • Update preparation status  
        • Mark orders as collected  
        • Manage the daily menu  
        • Change prices and availability
        """
    )

    st.markdown("### 📦 Sample Orders")

    sample_orders = [
        ["001", "Rahul", "Sandwich + Tea", "Break", "Confirmed"],
        ["002", "Anushka", "Maggi", "Regular", "Preparing"],
        ["003", "Siddhartha", "Roll + Coffee", "Break", "Confirmed"],
        ["004", "Prerana", "Dosa", "Regular", "Ready"]
    ]

    st.dataframe(
        sample_orders,
        use_container_width=True,
        hide_index=True,
        column_config={
            0: "Order ID",
            1: "Student",
            2: "Items",
            3: "Order Type",
            4: "Status"
        }
    )
