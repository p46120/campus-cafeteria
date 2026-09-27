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
# REGULAR COLLECTION TIMES
# =========================================================

REGULAR_COLLECTION_TIMES = [
    "As soon as ready",

    "10:00 AM – 10:30 AM",
    "10:30 AM – 11:00 AM",
    "11:00 AM – 11:30 AM",

    "12:00 PM – 12:30 PM",
    "12:30 PM – 1:00 PM",
    "1:00 PM – 1:30 PM",

    "2:00 PM – 2:30 PM",
    "2:30 PM – 3:00 PM",
    "3:00 PM – 3:30 PM",

    "4:00 PM – 4:30 PM",
    "4:30 PM – 5:00 PM",
    "5:00 PM – 5:30 PM",

    "6:00 PM – 6:30 PM",
    "6:30 PM – 7:00 PM",
    "7:00 PM – 7:30 PM",

    "8:00 PM – 8:30 PM",
    "8:30 PM – 9:00 PM",
    "9:00 PM – 9:30 PM",

    "9:30 PM – 10:00 PM"
]


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


def cart_count():

    return sum(st.session_state.cart.values())


def clear_cart():

    st.session_state.cart = {}


# =========================================================
# DAILY SEQUENTIAL ORDER ID
# =========================================================

def generate_daily_order_id():

    """
    Creates:
    001
    002
    003
    ...

    Counter automatically starts from 001
    on a new date.
    """

    if db is None:
        return datetime.now().strftime("%H%M%S")

    today = datetime.now().strftime("%Y-%m-%d")

    counter_ref = db.collection("counters").document(today)

    transaction = db.transaction()

    @firestore.transactional
    def update_counter(transaction):

        snapshot = counter_ref.get(transaction=transaction)

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

    number = update_counter(transaction)

    return f"{number:03d}"


# =========================================================
# HOME PAGE
# =========================================================

def home_page():

    st.title("🍽️ Campus Cafeteria")

    st.subheader(
        "Skip the queue. Order before you reach the cafeteria."
    )

    st.write(
        "Pre-order your food and collect it quickly during your break "
        "or whenever the cafeteria is open."
    )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("## 🎓 Student Portal")

        st.write(
            "Browse the menu, pre-order food and collect it "
            "using your Order ID."
        )

        if st.button(
            "🍔 Order Food",
            use_container_width=True,
            type="primary"
        ):

            st.session_state.page = "student"

            st.rerun()

    with col2:

        st.markdown("## 👨‍🍳 Cafeteria Portal")

        st.write(
            "Manage today's orders, preparation and collection."
        )

        if st.button(
            "📋 Cafeteria Dashboard",
            use_container_width=True
        ):

            st.session_state.page = "cafeteria"

            st.rerun()

    st.divider()

    st.markdown("### ⭐ Quick Features")

    f1, f2, f3 = st.columns(3)

    with f1:
        st.info("⚡ Pre-order from your room")

    with f2:
        st.info("🎫 Daily Order ID")

    with f3:
        st.info("📦 Collect at cafeteria")


# =========================================================
# STUDENT PAGE
# =========================================================

def student_page():

    st.title("🎓 Student Ordering")

    col1, col2 = st.columns([5, 1])

    with col1:

        st.caption(
            f"🛒 {cart_count()} item(s) in cart"
        )

    with col2:

        if st.button("← Home"):

            st.session_state.page = "home"

            st.rerun()

    st.divider()

    # =====================================================
    # STUDENT DETAILS
    # =====================================================

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

    # =====================================================
    # ORDER TYPE
    # =====================================================

    st.subheader("2. Order Type")

    order_type = st.radio(
        "How would you like to order?",
        [
            "Break Order",
            "Regular Order"
        ],
        horizontal=True
    )

    break_time = None
    regular_source = None
    collection_time = None

    # =====================================================
    # BREAK ORDER
    # =====================================================

    if order_type == "Break Order":

        st.markdown("#### 🕐 Select your break")

        break_time = st.selectbox(
            "Choose your batch and break time",
            BREAK_OPTIONS
        )

        st.info(
            "💡 Your food will be prepared in advance. "
            "Collect it during your selected break using your Order ID."
        )

    # =====================================================
    # REGULAR ORDER
    # =====================================================

    else:

        st.markdown("#### 🏠 Where are you ordering from?")

        regular_source = st.radio(
            "Order source",
            [
                "Room / Hostel — Pre-order",
                "On Campus — Order Now"
            ],
            horizontal=True
        )

        collection_time = st.selectbox(
            "Preferred collection time",
            REGULAR_COLLECTION_TIMES
        )

        st.info(
            "📦 Your order will be collected at the "
            "cafeteria counter using your Order ID."
        )

    # =====================================================
    # POPULAR ITEMS
    # =====================================================

    st.divider()

    st.subheader("🔥 Popular Picks")

    st.caption(
        "Quick choices for students who want to order fast."
    )

    popular = [
        ("Tea", "☕"),
        ("Veg Roll", "🌯"),
        ("Sandwich", "🥪")
    ]

    p1, p2, p3 = st.columns(3)

    for col, (item, emoji) in zip(
        [p1, p2, p3],
        popular
    ):

        with col:

            st.markdown(
                f"**{emoji} {item}** — ₹{MENU[item]['price']}"
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

    for i in range(0, len(menu_items), 3):

        cols = st.columns(3)

        for j, col in enumerate(cols):

            if i + j >= len(menu_items):
                continue

            item = menu_items[i + j]

            with col:

                st.markdown(
                    f"### {item}"
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

    # =====================================================
    # CART
    # =====================================================

    st.divider()

    st.subheader(
        f"🛒 Your Cart ({cart_count()} items)"
    )

    if not st.session_state.cart:

        st.info(
            "Your cart is empty. Add something from the menu."
        )

    else:

        for item, quantity in st.session_state.cart.items():

            item_total = (
                MENU[item]["price"] * quantity
            )

            col1, col2, col3 = st.columns(
                [4, 2, 2]
            )

            with col1:

                st.write(
                    f"**{item}**"
                )

            with col2:

                st.write(
                    f"× {quantity}"
                )

            with col3:

                st.write(
                    f"₹{item_total}"
                )

        st.divider()

        total = cart_total()

        col1, col2 = st.columns(2)

        with col1:

            st.markdown("### Total")

        with col2:

            st.markdown(
                f"### ₹{total}"
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

                    # Generate proper daily ID

                    order_id = generate_daily_order_id()

                    # Determine initial status

                    if order_type == "Break Order":

                        initial_status = "Confirmed"

                    else:

                        all_ready = all(
                            MENU[item]["status"] == "Ready"
                            for item in st.session_state.cart
                        )

                        if all_ready:

                            initial_status = "Ready"

                        else:

                            initial_status = "Confirmed"

                    order_data = {

                        "order_id": order_id,

                        "student_name": student_name.strip(),

                        "student_id": student_id.strip(),

                        "order_type": order_type,

                        "break_time": break_time,

                        "regular_source": regular_source,

                        "collection_time": collection_time,

                        "items": dict(
                            st.session_state.cart
                        ),

                        "total": cart_total(),

                        "status": initial_status,

                        "date": datetime.now().strftime(
                            "%Y-%m-%d"
                        ),

                        "created_at": datetime.now(),

                        "feedback_submitted": False
                    }

                    if db is None:

                        st.error(
                            "Firebase is not connected."
                        )

                    else:

                        db.collection(
                            "orders"
                        ).add(order_data)

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

    st.title("🎉 Order Confirmed!")

    if order:

        st.success(
            f"Your Order ID is **#{order['order_id']}**"
        )

        st.markdown(
            "### 🎫 Show this Order ID at the cafeteria counter."
        )

        st.divider()

        # Order information

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Order ID",
                f"#{order['order_id']}"
            )

        with col2:

            st.metric(
                "Total",
                f"₹{order['total']}"
            )

        with col3:

            st.metric(
                "Status",
                order["status"]
            )

        st.divider()

        st.subheader("📋 Order Summary")

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

        if order["regular_source"]:

            st.write(
                f"**Ordered from:** {order['regular_source']}"
            )

        if order["collection_time"]:

            st.write(
                f"**Collection:** {order['collection_time']}"
            )

        st.divider()

        st.subheader("🍽️ Items")

        for item, quantity in order["items"].items():

            price = (
                MENU[item]["price"] * quantity
            )

            st.write(
                f"**{item}** × {quantity} — ₹{price}"
            )

        st.divider()

        if order["order_type"] == "Break Order":

            st.info(
                "🕐 Please collect your order during "
                f"**{order['break_time']}**."
            )

        else:

            st.info(
                "📦 Collect your order at the cafeteria "
                f"during **{order['collection_time']}**."
            )

        st.markdown(
            f"## 🎫 Order #{order['order_id']}"
        )

    st.divider()

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "🍔 Place Another Order",
            use_container_width=True
        ):

            st.session_state.page = "student"

            st.rerun()

    with col2:

        if st.button(
            "🏠 Back to Home",
            use_container_width=True
        ):

            st.session_state.page = "home"

            st.rerun()


# =========================================================
# UPDATE ORDER STATUS
# =========================================================

def update_order_status(doc_id, new_status):

    try:

        db.collection("orders").document(
            doc_id
        ).update(
            {
                "status": new_status,
                "updated_at": datetime.now()
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

        return

    # =====================================================
    # LOAD ORDERS
    # =====================================================

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    orders = []

    try:

        orders_ref = db.collection(
            "orders"
        ).stream()

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
    # DASHBOARD METRICS
    # =====================================================

    total_orders = len(orders)

    confirmed = sum(
        1
        for o in orders
        if o.get("status") == "Confirmed"
    )

    preparing = sum(
        1
        for o in orders
        if o.get("status") == "Preparing"
    )

    ready = sum(
        1
        for o in orders
        if o.get("status") == "Ready"
    )

    collected = sum(
        1
        for o in orders
        if o.get("status") == "Collected"
    )

    st.subheader("📊 Today's Overview")

    m1, m2, m3, m4, m5 = st.columns(5)

    with m1:
        st.metric("Orders", total_orders)

    with m2:
        st.metric("Confirmed", confirmed)

    with m3:
        st.metric("Preparing", preparing)

    with m4:
        st.metric("Ready", ready)

    with m5:
        st.metric("Collected", collected)

    # =====================================================
    # FILTERS
    # =====================================================

    st.divider()

    st.subheader("🔎 Manage Orders")

    col1, col2 = st.columns(2)

    with col1:

        search_id = st.text_input(
            "Search Order ID",
            placeholder="Example: 004"
        ).strip()

    with col2:

        status_filter = st.selectbox(
            "Filter by Status",
            [
                "All",
                "Confirmed",
                "Preparing",
                "Ready",
                "Collected"
            ]
        )

    filtered_orders = orders

    if search_id:

        filtered_orders = [
            o
            for o in filtered_orders
            if o.get("order_id", "").lower()
            == search_id.lower()
        ]

    if status_filter != "All":

        filtered_orders = [
            o
            for o in filtered_orders
            if o.get("status") == status_filter
        ]

    # Newest order first

    filtered_orders.reverse()

    # =====================================================
    # ORDERS
    # =====================================================

    st.subheader(
        f"🍽️ Orders ({len(filtered_orders)})"
    )

    if not filtered_orders:

        st.info(
            "No orders match the selected filter."
        )

    else:

        for order in filtered_orders:

            status = order.get(
                "status",
                "Unknown"
            )

            order_id = order.get(
                "order_id",
                "---"
            )

            order_type = order.get(
                "order_type",
                ""
            )

            if status == "Confirmed":

                status_icon = "🟡"

            elif status == "Preparing":

                status_icon = "🔵"

            elif status == "Ready":

                status_icon = "🟢"

            elif status == "Collected":

                status_icon = "⚫"

            else:

                status_icon = "⚪"

            with st.container(border=True):

                col1, col2 = st.columns(
                    [5, 2]
                )

                with col1:

                    st.markdown(
                        f"## #{order_id}"
                    )

                    st.write(
                        f"**Student:** {order.get('student_name', '')}"
                    )

                    st.write(
                        f"**Student ID:** {order.get('student_id', '')}"
                    )

                    st.write(
                        f"**Order Type:** {order_type}"
                    )

                    if order.get("break_time"):

                        st.write(
                            f"**Break:** {order.get('break_time')}"
                        )

                    if order.get("regular_source"):

                        st.write(
                            f"**Source:** {order.get('regular_source')}"
                        )

                    if order.get("collection_time"):

                        st.write(
                            f"**Collection:** {order.get('collection_time')}"
                        )

                    st.write(
                        f"**Items:** {order.get('items')}"
                    )

                    st.write(
                        f"**Total:** ₹{order.get('total', 0)}"
                    )

                with col2:

                    st.markdown(
                        f"### {status_icon} {status}"
                    )

                    # -------------------------------------
                    # BREAK ORDER
                    # -------------------------------------

                    if order_type == "Break Order":

                        if status == "Confirmed":

                            if st.button(
                                "✓ Mark Collected",
                                key=f"collect_break_{order['_doc_id']}",
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
                                key=f"prepare_{order['_doc_id']}",
                                use_container_width=True
                            ):

                                update_order_status(
                                    order["_doc_id"],
                                    "Preparing"
                                )

                        elif status == "Preparing":

                            if st.button(
                                "✓ Mark Ready",
                                key=f"ready_{order['_doc_id']}",
                                use_container_width=True
                            ):

                                update_order_status(
                                    order["_doc_id"],
                                    "Ready"
                                )

                        elif status == "Ready":

                            if st.button(
                                "🎫 Mark Collected",
                                key=f"collect_{order['_doc_id']}",
                                use_container_width=True
                            ):

                                update_order_status(
                                    order["_doc_id"],
                                    "Collected"
                                )

    # =====================================================
    # FEEDBACK DASHBOARD
    # =====================================================

    st.divider()

    st.subheader("⭐ Customer Feedback")

    feedbacks = []

    try:

        feedback_ref = db.collection(
            "feedbacks"
        ).stream()

        for doc in feedback_ref:

            data = doc.to_dict()

            feedbacks.append(data)

    except Exception:

        feedbacks = []

    if not feedbacks:

        st.info(
            "No feedback submitted yet."
        )

    else:

        ratings = [
            int(f.get("rating", 0))
            for f in feedbacks
            if f.get("rating")
        ]

        if ratings:

            average_rating = sum(
                ratings
            ) / len(ratings)

            f1, f2, f3 = st.columns(3)

            with f1:

                st.metric(
                    "Average Rating",
                    f"{average_rating:.1f} ⭐"
                )

            with f2:

                st.metric(
                    "Feedback Responses",
                    len(feedbacks)
                )

            with f3:

                five_star = sum(
                    1
                    for r in ratings
                    if r == 5
                )

                st.metric(
                    "5-Star Responses",
                    five_star
                )

        st.markdown("### Recent Feedback")

        recent_feedback = feedbacks[-5:]

        for feedback in reversed(
            recent_feedback
        ):

            rating = feedback.get(
                "rating",
                0
            )

            comment = feedback.get(
                "comment",
                ""
            )

            order_id = feedback.get(
                "order_id",
                "---"
            )

            st.markdown(
                f"""
                **Order #{order_id}** — {'⭐' * int(rating)}

                {comment}
                """
            )

            st.divider()


# =========================================================
# FEEDBACK PAGE
# =========================================================

def feedback_page():

    st.title("⭐ Give Feedback")

    st.write(
        "Your feedback helps the cafeteria improve food quality "
        "and service."
    )

    order_id = st.text_input(
        "Order ID",
        placeholder="Example: 005"
    )

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
        placeholder="Tell us what we can improve..."
    )

    if st.button(
        "Submit Feedback",
        type="primary",
        use_container_width=True
    ):

        if not order_id.strip():

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

                    "order_id": order_id.strip(),

                    "rating": rating,

                    "food_quality": food_quality,

                    "service": service,

                    "comment": comment.strip(),

                    "created_at": datetime.now()
                }

                db.collection(
                    "feedbacks"
                ).add(feedback_data)

                st.success(
                    "Thank you! Your feedback has been recorded. ⭐"
                )

            except Exception as e:

                st.error(
                    f"Could not submit feedback: {e}"
                )

    st.divider()

    if st.button(
        "← Back to Home",
        use_container_width=True
    ):

        st.session_state.page = "home"

        st.rerun()


# =========================================================
# HOME EXTRA BUTTON
# =========================================================

# Add feedback option to home through a small modification
# to routing below.


# =========================================================
# PAGE ROUTING
# =========================================================

if st.session_state.page == "home":

    home_page()

    st.divider()

    st.subheader("⭐ Help us improve")

    if st.button(
        "Give Feedback",
        use_container_width=True
    ):

        st.session_state.page = "feedback"

        st.rerun()

elif st.session_state.page == "student":

    student_page()

elif st.session_state.page == "confirmation":

    confirmation_page()

elif st.session_state.page == "cafeteria":

    cafeteria_page()

elif st.session_state.page == "feedback":

    feedback_page()
