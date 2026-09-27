import json
from datetime import datetime, time
from zoneinfo import ZoneInfo

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
# CUSTOM STYLE
# =========================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 18px;
        color: #666666;
        margin-bottom: 25px;
    }

    .order-card {
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #dddddd;
        margin-bottom: 15px;
    }

    .small-muted {
        color: #777777;
        font-size: 14px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# FIREBASE CONNECTION
# =========================================================

@st.cache_resource
def initialize_firebase():

    try:

        firebase_json = json.loads(
            st.secrets["firebase_json"]
        )

        if not firebase_admin._apps:

            cred = credentials.Certificate(
                firebase_json
            )

            firebase_admin.initialize_app(
                cred
            )

        return firestore.client(), True

    except Exception:

        return None, False


db, firebase_connected = initialize_firebase()


# =========================================================
# MENU
# =========================================================

MENU = {

    "Tea": {
        "price": 15,
        "status": "Ready",
        "emoji": "☕"
    },

    "Sandwich": {
        "price": 40,
        "status": "Prepared",
        "emoji": "🥪"
    },

    "Maggi": {
        "price": 35,
        "status": "Prepared",
        "emoji": "🍜"
    },

    "Cold Coffee": {
        "price": 30,
        "status": "Ready",
        "emoji": "🥤"
    },

    "Veg Roll": {
        "price": 45,
        "status": "Prepared",
        "emoji": "🌯"
    },

    "Water Bottle": {
        "price": 20,
        "status": "Ready",
        "emoji": "💧"
    }
}


# =========================================================
# BREAK SCHEDULE
# =========================================================

BREAK_OPTIONS = [

    "2nd Year | 10:30 AM – 11:00 AM",
    "1st Year | 11:00 AM – 11:30 AM",

    "2nd Year | 12:30 PM – 1:00 PM",
    "1st Year | 1:00 PM – 1:30 PM",

    "2nd Year | 2:30 PM – 3:00 PM",
    "1st Year | 3:00 PM – 3:30 PM",

    "2nd Year | 4:30 PM – 5:00 PM",
    "1st Year | 5:00 PM – 5:30 PM",

    "2nd Year | 6:30 PM – 7:00 PM",
    "1st Year | 7:00 PM – 7:30 PM",

    "2nd Year | 8:30 PM – 9:00 PM",
    "1st Year | 9:00 PM – 9:30 PM"
]


# =========================================================
# ACTUAL BREAK WINDOWS
# =========================================================

BREAK_WINDOWS = [

    (time(10, 30), time(11, 0)),
    (time(11, 0), time(11, 30)),

    (time(12, 30), time(13, 0)),
    (time(13, 0), time(13, 30)),

    (time(14, 30), time(15, 0)),
    (time(15, 0), time(15, 30)),

    (time(16, 30), time(17, 0)),
    (time(17, 0), time(17, 30)),

    (time(18, 30), time(19, 0)),
    (time(19, 0), time(19, 30)),

    (time(20, 30), time(21, 0)),
    (time(21, 0), time(21, 30))
]


# =========================================================
# CHECK WHETHER CURRENT TIME IS BREAK TIME
# =========================================================

def is_break_time():

    now = datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).time()

    for start, end in BREAK_WINDOWS:

        if start <= now < end:

            return True

    return False


# =========================================================
# SESSION STATE
# =========================================================

if "page" not in st.session_state:

    st.session_state.page = "home"


if "cart" not in st.session_state:

    st.session_state.cart = {}


if "last_order" not in st.session_state:

    st.session_state.last_order = None


# =========================================================
# CART FUNCTIONS
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


def clear_cart():

    st.session_state.cart = {}


def cart_count():

    return sum(
        st.session_state.cart.values()
    )


def cart_total():

    total = 0

    for item, quantity in st.session_state.cart.items():

        total += (
            MENU[item]["price"] *
            quantity
        )

    return total


# =========================================================
# DAILY ORDER ID
# =========================================================

def generate_daily_order_id():

    if db is None:

        return datetime.now().strftime(
            "%H%M%S"
        )

    today = datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).strftime("%Y-%m-%d")

    counter_ref = db.collection(
        "counters"
    ).document(today)

    transaction = db.transaction()

    @firestore.transactional
    def update_counter(transaction):

        snapshot = counter_ref.get(
            transaction=transaction
        )

        if snapshot.exists:

            data = snapshot.to_dict()

            last_number = data.get(
                "last_order_number",
                0
            )

        else:

            last_number = 0

        new_number = last_number + 1

        transaction.set(
            counter_ref,
            {
                "last_order_number": new_number,
                "date": today
            }
        )

        return new_number

    number = update_counter(
        transaction
    )

    return f"{number:03d}"


# =========================================================
# HOME PAGE
# =========================================================

def home_page():

    st.markdown(
        '<div class="main-title">🍽️ Campus Cafeteria</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Skip the queue. Order before you reach the cafeteria.'
        '</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("## 🎓 Student Portal")

        st.write(
            "Pre-order food, track your order and "
            "collect it using your Order ID."
        )

        if st.button(
            "🍔 Order Food",
            type="primary",
            use_container_width=True
        ):

            st.session_state.page = "student"

            st.rerun()

    with col2:

        st.markdown("## 👨‍🍳 Cafeteria Portal")

        st.write(
            "Manage today's orders, preparation "
            "and collection."
        )

        if st.button(
            "📋 Cafeteria Dashboard",
            use_container_width=True
        ):

            st.session_state.page = "cafeteria"

            st.rerun()

    st.divider()

    st.subheader("⚡ Quick Actions")

    q1, q2, q3 = st.columns(3)

    with q1:

        if st.button(
            "🔎 Track My Order",
            use_container_width=True
        ):

            st.session_state.page = "track"

            st.rerun()

    with q2:

        if st.button(
            "⭐ Give Feedback",
            use_container_width=True
        ):

            st.session_state.page = "feedback"

            st.rerun()

    with q3:

        st.info(
            "🍴 Fresh food • Less waiting"
        )


# =========================================================
# STUDENT PAGE
# =========================================================

def student_page():

    st.markdown(
        '<div class="main-title">🎓 Student Ordering</div>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([5, 1])

    with col1:

        st.caption(
            f"🛒 {cart_count()} item(s) in cart"
        )

    with col2:

        if st.button(
            "🏠 Home",
            type="primary",
            use_container_width=True
        ):

            st.session_state.page = "home"

            st.rerun()

    st.divider()

    # =====================================================
    # STUDENT DETAILS
    # =====================================================

    st.subheader("1. Student Details")

    c1, c2 = st.columns(2)

    with c1:

        student_name = st.text_input(
            "Student Name",
            placeholder="Enter your name"
        )

    with c2:

        student_id = st.text_input(
            "Student ID",
            placeholder="Enter your student ID"
        )

    # =====================================================
    # ORDER TYPE
    # =====================================================

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
    regular_source = None

    # =====================================================
    # BREAK ORDER
    # =====================================================

    if order_type == "Break Order":

        st.markdown(
            "#### 🕐 Select your break"
        )

        break_time = st.selectbox(
            "Batch & Break",
            BREAK_OPTIONS
        )

        st.info(
            "💡 Break orders are prepared in advance. "
            "Collect your order during the selected break."
        )

    # =====================================================
    # REGULAR ORDER
    # =====================================================

    else:

        if is_break_time():

            st.warning(
                "🚨 Regular orders are temporarily "
                "unavailable during the break rush."
            )

            st.info(
                "Please place a Break Order for the "
                "current break or try again after the break."
            )

        else:

            regular_source = (
                "Room / Hostel — Pre-order"
            )

            st.markdown(
                "#### 🏠 Room / Hostel Pre-order"
            )

            st.info(
                "Order from your room or hostel and "
                "collect your food from the cafeteria "
                "when it is ready."
            )

            st.success(
                "⏱️ Estimated preparation time: "
                "approximately 10–15 minutes."
            )

    # =====================================================
    # POPULAR ITEMS
    # =====================================================

    st.divider()

    st.subheader("🔥 Popular Picks")

    popular_items = [
        "Tea",
        "Veg Roll",
        "Sandwich"
    ]

    p1, p2, p3 = st.columns(3)

    for col, item in zip(
        [p1, p2, p3],
        popular_items
    ):

        with col:

            st.markdown(
                f"**{MENU[item]['emoji']} {item}**"
            )

            st.write(
                f"₹{MENU[item]['price']}"
            )

            if st.button(
                f"Add {item}",
                key=f"popular_{item}",
                use_container_width=True
            ):

                add_to_cart(item)

                st.rerun()

    # =====================================================
    # MENU
    # =====================================================

    st.divider()

    st.subheader("3. Menu")

    menu_items = list(MENU.keys())

    for i in range(
        0,
        len(menu_items),
        3
    ):

        cols = st.columns(3)

        for j, col in enumerate(cols):

            if i + j >= len(menu_items):

                continue

            item = menu_items[i + j]

            with col:

                st.markdown(
                    f"### "
                    f"{MENU[item]['emoji']} "
                    f"{item}"
                )

                st.markdown(
                    f"**₹{MENU[item]['price']}**"
                )

                if MENU[item]["status"] == "Ready":

                    st.success(
                        "✓ Usually ready"
                    )

                else:

                    st.warning(
                        "⏱ Prepared on order"
                    )

                if item in st.session_state.cart:

                    quantity = (
                        st.session_state.cart[item]
                    )

                    a, b, c = st.columns(3)

                    with a:

                        if st.button(
                            "−",
                            key=f"minus_{item}",
                            use_container_width=True
                        ):

                            remove_from_cart(item)

                            st.rerun()

                    with b:

                        st.markdown(
                            f"<h3 style='text-align:center'>"
                            f"{quantity}"
                            f"</h3>",
                            unsafe_allow_html=True
                        )

                    with c:

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

    # =====================================================
    # CART
    # =====================================================

    st.divider()

    st.subheader(
        f"🛒 Your Cart ({cart_count()} items)"
    )

    if not st.session_state.cart:

        st.info(
            "Your cart is empty."
        )

    else:

        for item, quantity in (
            st.session_state.cart.items()
        ):

            item_total = (
                MENU[item]["price"] *
                quantity
            )

            c1, c2, c3 = st.columns(
                [4, 2, 2]
            )

            with c1:

                st.write(
                    f"**{item}**"
                )

            with c2:

                st.write(
                    f"× {quantity}"
                )

            with c3:

                st.write(
                    f"₹{item_total}"
                )

        st.divider()

        c1, c2 = st.columns(2)

        with c1:

            st.markdown("### Total")

        with c2:

            st.markdown(
                f"### ₹{cart_total()}"
            )

        if st.button(
            "🗑️ Clear Cart",
            use_container_width=True
        ):

            clear_cart()

            st.rerun()

    # =====================================================
    # PLACE ORDER
    # =====================================================

    st.divider()

    if st.session_state.cart:

        # Regular orders cannot be placed during
        # a break rush.

        regular_blocked = (
            order_type == "Regular Order"
            and is_break_time()
        )

        if regular_blocked:

            st.warning(
                "Regular ordering is currently paused "
                "because the cafeteria is serving the "
                "break rush."
            )

        else:

            if st.button(
                "🍽️ Place Order",
                type="primary",
                use_container_width=True
            ):

                if not student_name.strip():

                    st.error(
                        "Please enter your name."
                    )

                elif not student_id.strip():

                    st.error(
                        "Please enter your Student ID."
                    )

                else:

                    try:

                        order_id = (
                            generate_daily_order_id()
                        )

                        if order_type == "Break Order":

                            initial_status = (
                                "Confirmed"
                            )

                        else:

                            all_ready = all(
                                MENU[item]["status"]
                                == "Ready"
                                for item
                                in st.session_state.cart
                            )

                            if all_ready:

                                initial_status = (
                                    "Ready"
                                )

                            else:

                                initial_status = (
                                    "Confirmed"
                                )

                        order_data = {

                            "order_id": order_id,

                            "student_name":
                                student_name.strip(),

                            "student_id":
                                student_id.strip(),

                            "order_type":
                                order_type,

                            "break_time":
                                break_time,

                            "regular_source":
                                regular_source,

                            "items":
                                dict(
                                    st.session_state.cart
                                ),

                            "total":
                                cart_total(),

                            "status":
                                initial_status,

                            "date":
                                datetime.now(
                                    ZoneInfo(
                                        "Asia/Kolkata"
                                    )
                                ).strftime(
                                    "%Y-%m-%d"
                                ),

                            "created_at":
                                datetime.now(
                                    ZoneInfo(
                                        "Asia/Kolkata"
                                    )
                                ),

                            "estimated_time":
                                "10–15 minutes",

                            "feedback_submitted":
                                False
                        }

                        if db is None:

                            st.error(
                                "Firebase is not connected."
                            )

                        else:

                            db.collection(
                                "orders"
                            ).add(
                                order_data
                            )

                            st.session_state.last_order = (
                                order_data
                            )

                            clear_cart()

                            st.session_state.page = (
                                "confirmation"
                            )

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

    st.markdown(
        '<div class="main-title">🎉 Order Confirmed!</div>',
        unsafe_allow_html=True
    )

    if order:

        st.success(
            f"Your Order ID is "
            f"**#{order['order_id']}**"
        )

        st.markdown(
            "### 🎫 Show this Order ID at the "
            "cafeteria counter."
        )

        st.divider()

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Order ID",
                f"#{order['order_id']}"
            )

        with c2:

            st.metric(
                "Total",
                f"₹{order['total']}"
            )

        with c3:

            st.metric(
                "Status",
                order["status"]
            )

        st.divider()

        st.subheader("📋 Order Summary")

        st.write(
            f"**Student:** "
            f"{order['student_name']}"
        )

        st.write(
            f"**Order Type:** "
            f"{order['order_type']}"
        )

        if order.get("break_time"):

            st.write(
                f"**Break:** "
                f"{order['break_time']}"
            )

        if order.get("regular_source"):

            st.write(
                f"**Order source:** "
                f"{order['regular_source']}"
            )

        st.divider()

        st.subheader("🍽️ Items")

        for item, quantity in (
            order["items"].items()
        ):

            price = (
                MENU[item]["price"] *
                quantity
            )

            st.write(
                f"**{item}** × {quantity} — ₹{price}"
            )

        st.divider()

        if order["order_type"] == "Break Order":

            st.info(
                "🕐 Collect your order during "
                f"**{order['break_time']}**."
            )

        else:

            st.success(
                "⏱️ Your order should be ready "
                "in approximately **10–15 minutes**."
            )

            st.info(
                "📦 Please collect it from the "
                "cafeteria counter using Order ID "
                f"**#{order['order_id']}**."
            )

        st.divider()

        # SIMPLE STATUS JOURNEY

        st.subheader("📍 Order Journey")

        if order["order_type"] == "Break Order":

            st.write(
                "🟡 **Confirmed**  →  "
                "🎫 **Collect during break**"
            )

        else:

            st.write(
                "🟡 **Confirmed**  →  "
                "🔵 **Preparing**  →  "
                "🟢 **Ready**  →  "
                "🎫 **Collected**"
            )

    st.divider()

    c1, c2 = st.columns(2)

    with c1:

        if st.button(
            "🍔 Place Another Order",
            use_container_width=True
        ):

            st.session_state.page = "student"

            st.rerun()

    with c2:

        if st.button(
            "🏠 Return to Home",
            type="primary",
            use_container_width=True
        ):

            st.session_state.page = "home"

            st.rerun()


# =========================================================
# TRACK ORDER PAGE
# =========================================================

def track_order_page():

    st.markdown(
        '<div class="main-title">🔎 Track My Order</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Enter your Order ID and Student ID "
        "to see the latest status."
    )

    order_id = st.text_input(
        "Order ID",
        placeholder="Example: 001"
    ).strip()

    student_id = st.text_input(
        "Student ID",
        placeholder="Enter your Student ID"
    ).strip()

    if st.button(
        "🔎 Track Order",
        type="primary",
        use_container_width=True
    ):

        if not order_id or not student_id:

            st.warning(
                "Please enter both Order ID and Student ID."
            )

        elif db is None:

            st.error(
                "Firebase is not connected."
            )

        else:

            try:

                found = None

                orders_ref = (
                    db.collection("orders")
                    .stream()
                )

                for doc in orders_ref:

                    data = doc.to_dict()

                    if (
                        str(
                            data.get("order_id")
                        ) == order_id
                        and
                        str(
                            data.get("student_id")
                        ) == student_id
                    ):

                        found = data

                        break

                if found is None:

                    st.error(
                        "No matching order found."
                    )

                else:

                    status = found.get(
                        "status",
                        "Unknown"
                    )

                    st.success(
                        f"Order **#{order_id}** found."
                    )

                    st.metric(
                        "Current Status",
                        status
                    )

                    st.write(
                        f"**Student:** "
                        f"{found.get('student_name')}"
                    )

                    st.write(
                        f"**Total:** "
                        f"₹{found.get('total')}"
                    )

                    st.write(
                        f"**Order Type:** "
                        f"{found.get('order_type')}"
                    )

                    st.divider()

                    if (
                        found.get("order_type")
                        == "Break Order"
                    ):

                        st.info(
                            "🎫 Confirmed for your "
                            "selected break. "
                            "Please collect using "
                            f"Order ID **#{order_id}**."
                        )

                    elif status == "Confirmed":

                        st.warning(
                            "🟡 Your order has been confirmed "
                            "and will be prepared shortly."
                        )

                    elif status == "Preparing":

                        st.info(
                            "🔵 Your food is being prepared."
                        )

                    elif status == "Ready":

                        st.success(
                            "🟢 Your order is ready! "
                            "Please collect it from the "
                            "cafeteria counter."
                        )

                    elif status == "Collected":

                        st.success(
                            "⚫ Order collected. "
                            "Enjoy your food!"
                        )

            except Exception as e:

                st.error(
                    f"Could not track order: {e}"
                )

    st.divider()

    if st.button(
        "🏠 Return to Home",
        type="primary",
        use_container_width=True
    ):

        st.session_state.page = "home"

        st.rerun()


# =========================================================
# UPDATE ORDER STATUS
# =========================================================

def update_order_status(
    doc_id,
    new_status
):

    try:

        db.collection(
            "orders"
        ).document(
            doc_id
        ).update(
            {
                "status":
                    new_status,

                "updated_at":
                    datetime.now(
                        ZoneInfo(
                            "Asia/Kolkata"
                        )
                    )
            }
        )

        st.rerun()

    except Exception as e:

        st.error(
            f"Could not update order: {e}"
        )


# =========================================================
# CAFETERIA DASHBOARD
# =========================================================

def cafeteria_page():

    st.markdown(
        '<div class="main-title">👨‍🍳 Cafeteria Dashboard</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "🏠 Return to Home",
        type="primary",
        use_container_width=False
    ):

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

        return

    # =====================================================
    # LOAD TODAY'S ORDERS
    # =====================================================

    today = datetime.now(
        ZoneInfo("Asia/Kolkata")
    ).strftime(
        "%Y-%m-%d"
    )

    orders = []

    try:

        orders_ref = (
            db.collection("orders")
            .stream()
        )

        for doc in orders_ref:

            data = doc.to_dict()

            if data.get("date") == today:

                data["_doc_id"] = doc.id

                orders.append(data)

    except Exception as e:

        st.error(
            f"Could not load orders: {e}"
        )

        return

    # =====================================================
    # METRICS
    # =====================================================

    total_orders = len(orders)

    confirmed = sum(
        1
        for o in orders
        if o.get("status")
        == "Confirmed"
    )

    preparing = sum(
        1
        for o in orders
        if o.get("status")
        == "Preparing"
    )

    ready = sum(
        1
        for o in orders
        if o.get("status")
        == "Ready"
    )

    collected = sum(
        1
        for o in orders
        if o.get("status")
        == "Collected"
    )

    revenue = sum(
        float(
            o.get("total", 0)
        )
        for o in orders
    )

    st.subheader(
        "📊 Today's Overview"
    )

    m1, m2, m3, m4 = st.columns(4)

    with m1:

        st.metric(
            "Total Orders",
            total_orders
        )

    with m2:

        st.metric(
            "Pending",
            confirmed + preparing
        )

    with m3:

        st.metric(
            "Ready",
            ready
        )

    with m4:

        st.metric(
            "Today's Sales",
            f"₹{revenue:.0f}"
        )

    st.divider()

    # =====================================================
    # BREAK RUSH INDICATOR
    # =====================================================

    if is_break_time():

        st.warning(
            "🚨 BREAK RUSH IS CURRENTLY ACTIVE"
        )

        st.caption(
            "Prioritize Break Orders and keep "
            "the collection counter moving quickly."
        )

    else:

        st.info(
            "🟢 Normal operating period"
        )

    # =====================================================
    # FILTERS
    # =====================================================

    st.subheader(
        "🔎 Find Orders"
    )

    c1, c2 = st.columns(2)

    with c1:

        search_id = st.text_input(
            "Search Order ID",
            placeholder="Example: 001"
        ).strip()

    with c2:

        status_filter = st.selectbox(
            "Status",
            [
                "All",
                "Confirmed",
                "Preparing",
                "Ready",
                "Collected"
            ]
        )

    filtered_orders = orders.copy()

    if search_id:

        filtered_orders = [
            o
            for o in filtered_orders
            if str(
                o.get("order_id", "")
            ).lower()
            == search_id.lower()
        ]

    if status_filter != "All":

        filtered_orders = [
            o
            for o in filtered_orders
            if o.get("status")
            == status_filter
        ]

    # Newest first

    filtered_orders.reverse()

    # =====================================================
    # ORDER LIST
    # =====================================================

    st.subheader(
        f"🍽️ Orders ({len(filtered_orders)})"
    )

    if not filtered_orders:

        st.info(
            "No matching orders."
        )

    else:

        for order in filtered_orders:

            order_id = order.get(
                "order_id",
                "---"
            )

            status = order.get(
                "status",
                "Unknown"
            )

            order_type = order.get(
                "order_type",
                ""
            )

            if status == "Confirmed":

                icon = "🟡"

            elif status == "Preparing":

                icon = "🔵"

            elif status == "Ready":

                icon = "🟢"

            elif status == "Collected":

                icon = "⚫"

            else:

                icon = "⚪"

            with st.container(
                border=True
            ):

                c1, c2 = st.columns(
                    [5, 2]
                )

                with c1:

                    st.markdown(
                        f"## #{order_id}"
                    )

                    st.write(
                        f"**Student:** "
                        f"{order.get('student_name', '')}"
                    )

                    st.write(
                        f"**Student ID:** "
                        f"{order.get('student_id', '')}"
                    )

                    st.write(
                        f"**Order Type:** "
                        f"{order_type}"
                    )

                    if order.get(
                        "break_time"
                    ):

                        st.write(
                            f"**Break:** "
                            f"{order.get('break_time')}"
                        )

                    if order.get(
                        "regular_source"
                    ):

                        st.write(
                            f"**Source:** "
                            f"{order.get('regular_source')}"
                        )

                    st.write(
                        f"**Items:** "
                        f"{order.get('items')}"
                    )

                    st.write(
                        f"**Total:** "
                        f"₹{order.get('total', 0)}"
                    )

                with c2:

                    st.markdown(
                        f"### {icon} {status}"
                    )

                    # -------------------------------------
                    # BREAK ORDER
                    # -------------------------------------

                    if (
                        order_type
                        == "Break Order"
                    ):

                        st.caption(
                            "Break orders skip "
                            "the preparation status."
                        )

                        if status == "Confirmed":

                            if st.button(
                                "🎫 Mark Collected",
                                key=(
                                    "break_collect_"
                                    + order["_doc_id"]
                                ),
                                use_container_width=True
                            ):

                                update_order_status(
                                    order["_doc_id"],
                                    "Collected"
                                )

                    # -------------------------------------
                    # REGULAR ORDER
                    # -------------------------------------

                    else:

                        if status == "Confirmed":

                            if st.button(
                                "▶ Start Preparing",
                                key=(
                                    "prepare_"
                                    + order["_doc_id"]
                                ),
                                use_container_width=True
                            ):

                                update_order_status(
                                    order["_doc_id"],
                                    "Preparing"
                                )

                        elif status == "Preparing":

                            if st.button(
                                "✓ Mark Ready",
                                key=(
                                    "ready_"
                                    + order["_doc_id"]
                                ),
                                use_container_width=True
                            ):

                                update_order_status(
                                    order["_doc_id"],
                                    "Ready"
                                )

                        elif status == "Ready":

                            if st.button(
                                "🎫 Mark Collected",
                                key=(
                                    "collect_"
                                    + order["_doc_id"]
                                ),
                                use_container_width=True
                            ):

                                update_order_status(
                                    order["_doc_id"],
                                    "Collected"
                                )

    # =====================================================
    # FEEDBACK SECTION
    # =====================================================

    st.divider()

    st.subheader(
        "⭐ Customer Feedback"
    )

    feedbacks = []

    try:

        feedback_ref = (
            db.collection(
                "feedbacks"
            ).stream()
        )

        for doc in feedback_ref:

            feedbacks.append(
                doc.to_dict()
            )

    except Exception:

        feedbacks = []

    if not feedbacks:

        st.info(
            "No feedback submitted yet."
        )

    else:

        ratings = [

            int(
                f.get("rating", 0)
            )

            for f in feedbacks

            if f.get("rating")
        ]

        if ratings:

            average_rating = (
                sum(ratings)
                / len(ratings)
            )

            f1, f2, f3 = st.columns(3)

            with f1:

                st.metric(
                    "Average Rating",
                    f"{average_rating:.1f} ⭐"
                )

            with f2:

                st.metric(
                    "Responses",
                    len(feedbacks)
                )

            with f3:

                five_star = sum(
                    1
                    for r in ratings
                    if r == 5
                )

                st.metric(
                    "5-Star",
                    five_star
                )

        st.markdown(
            "### Recent Feedback"
        )

        for feedback in reversed(
            feedbacks[-5:]
        ):

            rating = int(
                feedback.get(
                    "rating",
                    0
                )
            )

            comment = feedback.get(
                "comment",
                ""
            )

            order_id = feedback.get(
                "order_id",
                "---"
            )

            st.write(
                f"**Order #{order_id}** "
                f"{'⭐' * rating}"
            )

            if comment:

                st.write(
                    f"_{comment}_"
                )

            st.divider()


# =========================================================
# FEEDBACK PAGE
# =========================================================

def feedback_page():

    st.markdown(
        '<div class="main-title">⭐ Give Feedback</div>',
        unsafe_allow_html=True
    )

    st.write(
        "Your feedback helps the cafeteria "
        "improve food and service."
    )

    order_id = st.text_input(
        "Order ID",
        placeholder="Example: 001"
    ).strip()

    rating = st.slider(
        "Overall Experience",
        1,
        5,
        5
    )

    food_quality = st.select_slider(
        "Food Quality",
        options=[
            "Poor",
            "Average",
            "Good",
            "Very Good",
            "Excellent"
        ],
        value="Good"
    )

    service = st.select_slider(
        "Service",
        options=[
            "Poor",
            "Average",
            "Good",
            "Very Good",
            "Excellent"
        ],
        value="Good"
    )

    comment = st.text_area(
        "Comments",
        placeholder=(
            "What did you like? "
            "What can we improve?"
        )
    )

    if st.button(
        "⭐ Submit Feedback",
        type="primary",
        use_container_width=True
    ):

        if not order_id:

            st.error(
                "Please enter your Order ID."
            )

        elif db is None:

            st.error(
                "Firebase is not connected."
            )

        else:

            try:

                feedback_data = {

                    "order_id":
                        order_id,

                    "rating":
                        rating,

                    "food_quality":
                        food_quality,

                    "service":
                        service,

                    "comment":
                        comment.strip(),

                    "created_at":
                        datetime.now(
                            ZoneInfo(
                                "Asia/Kolkata"
                            )
                        )
                }

                db.collection(
                    "feedbacks"
                ).add(
                    feedback_data
                )

                st.success(
                    "Thank you! Your feedback "
                    "has been recorded. ⭐"
                )

            except Exception as e:

                st.error(
                    f"Could not submit feedback: {e}"
                )

    st.divider()

    if st.button(
        "🏠 Return to Home",
        type="primary",
        use_container_width=True
    ):

        st.session_state.page = "home"

        st.rerun()


# =========================================================
# PAGE ROUTING
# =========================================================

if st.session_state.page == "home":

    home_page()

elif st.session_state.page == "student":

    student_page()

elif st.session_state.page == "confirmation":

    confirmation_page()

elif st.session_state.page == "track":

    track_order_page()

elif st.session_state.page == "cafeteria":

    cafeteria_page()

elif st.session_state.page == "feedback":

    feedback_page()
