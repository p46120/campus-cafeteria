import json
from datetime import datetime
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
# CUSTOM CSS
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
        color: #666;
        margin-bottom: 25px;
    }

    .discount-price {
        font-size: 20px;
        font-weight: 700;
    }

    .old-price {
        color: #888;
        text-decoration: line-through;
        margin-right: 8px;
    }

    .offer-box {
        padding: 10px;
        border-radius: 10px;
        background-color: #fff4e5;
        margin-top: 8px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# FIREBASE
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

    except Exception as e:

        return None, False


db, firebase_connected = initialize_firebase()


# =========================================================
# DEFAULT MENU
# =========================================================

DEFAULT_MENU = {

    "Tea": {
        "price": 15,
        "discount": 0,
        "available": True,
        "emoji": "☕"
    },

    "Sandwich": {
        "price": 40,
        "discount": 0,
        "available": True,
        "emoji": "🥪"
    },

    "Maggi": {
        "price": 35,
        "discount": 0,
        "available": True,
        "emoji": "🍜"
    },

    "Cold Coffee": {
        "price": 30,
        "discount": 0,
        "available": True,
        "emoji": "🥤"
    },

    "Veg Roll": {
        "price": 45,
        "discount": 0,
        "available": True,
        "emoji": "🌯"
    },

    "Water Bottle": {
        "price": 20,
        "discount": 0,
        "available": True,
        "emoji": "💧"
    }
}


# =========================================================
# BREAK SCHEDULE
# =========================================================

BREAK_OPTIONS = [

    "Senior Batch | 12:30 PM – 2:00 PM",

    "First Year / Junior Batch | 1:00 PM – 2:00 PM"
]


# These windows are ONLY used to identify break periods.
# Regular orders are NOT blocked during these periods.

BREAK_WINDOWS = [

    ("Senior Batch", 12, 30, 14, 0),

    ("First Year / Junior Batch", 13, 0, 14, 0)
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
# TIME
# =========================================================

def current_india_time():

    return datetime.now(
        ZoneInfo("Asia/Kolkata")
    )


# =========================================================
# MENU FUNCTIONS
# =========================================================

def load_menu():

    menu = {}

    try:

        docs = (
            db.collection("menu")
            .stream()
        )

        for doc in docs:

            data = doc.to_dict()

            menu[doc.id] = data

    except Exception:

        menu = {}

    if not menu:

        for item, data in DEFAULT_MENU.items():

            try:

                db.collection(
                    "menu"
                ).document(
                    item
                ).set(
                    data
                )

                menu[item] = data

            except Exception:

                pass

    return menu


def discounted_price(item_data):

    price = float(
        item_data.get("price", 0)
    )

    discount = float(
        item_data.get("discount", 0)
    )

    return round(
        price * (1 - discount / 100),
        2
    )


# =========================================================
# CART
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


def cart_total(menu):

    total = 0

    for item, quantity in (
        st.session_state.cart.items()
    ):

        if item in menu:

            total += (
                discounted_price(
                    menu[item]
                )
                * quantity
            )

    return round(total, 2)


# =========================================================
# DAILY ORDER ID
# =========================================================

def generate_daily_order_id():

    today = current_india_time().strftime(
        "%Y-%m-%d"
    )

    counter_ref = (
        db.collection("counters")
        .document(today)
    )

    transaction = db.transaction()

    @firestore.transactional
    def update_counter(transaction):

        snapshot = counter_ref.get(
            transaction=transaction
        )

        if snapshot.exists:

            old_number = snapshot.to_dict().get(
                "last_order_number",
                0
            )

        else:

            old_number = 0

        new_number = old_number + 1

        transaction.set(
            counter_ref,
            {
                "last_order_number":
                    new_number,

                "date":
                    today
            }
        )

        return new_number

    number = update_counter(
        transaction
    )

    return f"{number:03d}"


# =========================================================
# BREAK STATUS
# =========================================================

def current_break():

    now = current_india_time()

    current_minutes = (
        now.hour * 60
        + now.minute
    )

    for (
        name,
        start_h,
        start_m,
        end_h,
        end_m
    ) in BREAK_WINDOWS:

        start = (
            start_h * 60
            + start_m
        )

        end = (
            end_h * 60
            + end_m
        )

        if start <= current_minutes < end:

            return name

    return None


# =========================================================
# HOME
# =========================================================

def home_page():

    st.markdown(
        '<div class="main-title">'
        '🍽️ Campus Cafeteria'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="subtitle">'
        'Skip the queue. Order before you reach the cafeteria.'
        '</div>',
        unsafe_allow_html=True
    )

    c1, c2 = st.columns(2)

    with c1:

        st.subheader(
            "🎓 Student Portal"
        )

        st.write(
            "Order food, track your order "
            "and collect using your Order ID."
        )

        if st.button(
            "🍔 Order Food",
            type="primary",
            use_container_width=True
        ):

            st.session_state.page = "student"

            st.rerun()

    with c2:

        st.subheader(
            "👨‍🍳 Cafeteria Portal"
        )

        st.write(
            "Manage orders, menu, offers "
            "and customer feedback."
        )

        if st.button(
            "📋 Cafeteria Dashboard",
            use_container_width=True
        ):

            st.session_state.page = "cafeteria"

            st.rerun()

    st.divider()

    st.subheader(
        "⚡ Quick Actions"
    )

    q1, q2 = st.columns(2)

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


# =========================================================
# STUDENT ORDER PAGE
# =========================================================

def student_page():

    menu = load_menu()

    st.markdown(
        '<div class="main-title">'
        '🎓 Student Ordering'
        '</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "🏠 Return to Home",
        type="primary"
    ):

        st.session_state.page = "home"

        st.rerun()

    st.divider()

    # -----------------------------------------------------
    # DETAILS
    # -----------------------------------------------------

    st.subheader(
        "1. Student Details"
    )

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

    # -----------------------------------------------------
    # ORDER TYPE
    # -----------------------------------------------------

    st.subheader(
        "2. Order Type"
    )

    order_type = st.radio(
        "Choose your order type",
        [
            "Break Order",
            "Regular Order"
        ],
        horizontal=True
    )

    break_time = None

    if order_type == "Break Order":

        st.markdown(
            "#### 🕐 Select your break"
        )

        break_time = st.selectbox(
            "Batch & Break",
            BREAK_OPTIONS
        )

        st.info(
            "💡 Your food will be prepared "
            "in advance for the selected break."
        )

    else:

        st.markdown(
            "#### 🏠 Room / Hostel Pre-order"
        )

        st.info(
            "Order from your room or hostel. "
            "The cafeteria will prepare it and "
            "you can collect it from the counter."
        )

        st.success(
            "⏱️ Typical preparation time: "
            "around 10–15 minutes."
        )

    # -----------------------------------------------------
    # POPULAR
    # -----------------------------------------------------

    st.divider()

    st.subheader(
        "🔥 Popular Picks"
    )

    available_items = [
        item
        for item, data in menu.items()
        if data.get("available", True)
    ]

    popular = [
        item
        for item in [
            "Tea",
            "Veg Roll",
            "Sandwich"
        ]
        if item in available_items
    ]

    cols = st.columns(
        max(1, len(popular))
    )

    for col, item in zip(
        cols,
        popular
    ):

        with col:

            data = menu[item]

            st.markdown(
                f"### "
                f"{data.get('emoji', '🍽️')} "
                f"{item}"
            )

            price = discounted_price(
                data
            )

            discount = float(
                data.get("discount", 0)
            )

            if discount > 0:

                st.markdown(
                    f'<span class="old-price">'
                    f'₹{data["price"]}'
                    f'</span>'
                    f'<span class="discount-price">'
                    f'₹{price}'
                    f'</span>',
                    unsafe_allow_html=True
                )

            else:

                st.write(
                    f"₹{price:.0f}"
                )

            if st.button(
                "Add",
                key=f"popular_{item}",
                use_container_width=True
            ):

                add_to_cart(item)

                st.rerun()

    # -----------------------------------------------------
    # MENU
    # -----------------------------------------------------

    st.divider()

    st.subheader(
        "3. Menu"
    )

    available_menu = {

        item: data

        for item, data in menu.items()

        if data.get(
            "available",
            True
        )
    }

    if not available_menu:

        st.warning(
            "No menu items are currently available."
        )

    else:

        menu_items = list(
            available_menu.keys()
        )

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

                data = available_menu[item]

                with col:

                    st.markdown(
                        f"### "
                        f"{data.get('emoji', '🍽️')} "
                        f"{item}"
                    )

                    original_price = float(
                        data.get(
                            "price",
                            0
                        )
                    )

                    final_price = discounted_price(
                        data
                    )

                    discount = float(
                        data.get(
                            "discount",
                            0
                        )
                    )

                    if discount > 0:

                        st.markdown(
                            f'<span class="old-price">'
                            f'₹{original_price:.0f}'
                            f'</span>'
                            f'<span class="discount-price">'
                            f'₹{final_price:.0f}'
                            f'</span>',
                            unsafe_allow_html=True
                        )

                        st.caption(
                            f"🔥 {discount:.0f}% OFF"
                        )

                    else:

                        st.write(
                            f"₹{final_price:.0f}"
                        )

                    if item in st.session_state.cart:

                        quantity = (
                            st.session_state.cart[item]
                        )

                        a, b, c = st.columns(3)

                        with a:

                            if st.button(
                                "−",
                                key=f"minus_{item}"
                            ):

                                remove_from_cart(item)

                                st.rerun()

                        with b:

                            st.write(
                                f"**{quantity}**"
                            )

                        with c:

                            if st.button(
                                "+",
                                key=f"plus_{item}"
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

            if item not in menu:

                continue

            price = discounted_price(
                menu[item]
            )

            total = price * quantity

            c1, c2, c3 = st.columns(
                [5, 2, 2]
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
                    f"₹{total:.0f}"
                )

        st.divider()

        st.markdown(
            f"### Total: ₹{cart_total(menu):.0f}"
        )

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

                        status = "Confirmed"

                    else:

                        all_ready = all(

                            item in menu
                            and
                            menu[item].get(
                                "available",
                                True
                            )

                            for item
                            in st.session_state.cart
                        )

                        if all_ready:

                            status = "Ready"

                        else:

                            status = "Confirmed"

                    order_data = {

                        "order_id":
                            order_id,

                        "student_name":
                            student_name.strip(),

                        "student_id":
                            student_id.strip(),

                        "order_type":
                            order_type,

                        "break_time":
                            break_time,

                        "regular_source":
                            (
                                "Room / Hostel — Pre-order"
                                if order_type
                                == "Regular Order"
                                else None
                            ),

                        "items":
                            dict(
                                st.session_state.cart
                            ),

                        "total":
                            cart_total(menu),

                        "status":
                            status,

                        "date":
                            current_india_time().strftime(
                                "%Y-%m-%d"
                            ),

                        "created_at":
                            current_india_time(),

                        "estimated_time":
                            (
                                "Break collection"
                                if order_type
                                == "Break Order"
                                else "10–15 minutes"
                            )
                    }

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
# CONFIRMATION
# =========================================================

def confirmation_page():

    order = st.session_state.last_order

    st.markdown(
        '<div class="main-title">'
        '🎉 Order Confirmed!'
        '</div>',
        unsafe_allow_html=True
    )

    if order:

        st.success(
            f"Your Order ID is "
            f"**#{order['order_id']}**"
        )

        st.markdown(
            "### 🎫 Show this Order ID at the cafeteria counter."
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            st.metric(
                "Order ID",
                f"#{order['order_id']}"
            )

        with c2:

            st.metric(
                "Total",
                f"₹{order['total']:.0f}"
            )

        with c3:

            st.metric(
                "Status",
                order["status"]
            )

        st.divider()

        st.subheader(
            "📋 Order Summary"
        )

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

        if order["order_type"] == "Regular Order":

            st.success(
                "⏱️ Expected preparation time: "
                "approximately 10–15 minutes."
            )

        st.divider()

        for item, quantity in (
            order["items"].items()
        ):

            st.write(
                f"**{item}** × {quantity}"
            )

    st.divider()

    if st.button(
        "🔎 Track This Order",
        use_container_width=True
    ):

        st.session_state.page = "track"

        st.rerun()

    if st.button(
        "🏠 Return to Home",
        type="primary",
        use_container_width=True
    ):

        st.session_state.page = "home"

        st.rerun()


# =========================================================
# TRACK ORDER
# =========================================================

def track_order_page():

    st.markdown(
        '<div class="main-title">'
        '🔎 Track My Order'
        '</div>',
        unsafe_allow_html=True
    )

    order_id = st.text_input(
        "Order ID",
        placeholder="Example: 001"
    ).strip()

    student_id = st.text_input(
        "Student ID"
    ).strip()

    if st.button(
        "🔎 Track Order",
        type="primary",
        use_container_width=True
    ):

        if not order_id or not student_id:

            st.warning(
                "Please enter both fields."
            )

        else:

            try:

                found = None

                docs = (
                    db.collection("orders")
                    .stream()
                )

                for doc in docs:

                    data = doc.to_dict()

                    if (
                        str(
                            data.get("order_id")
                        )
                        == order_id
                        and
                        str(
                            data.get("student_id")
                        )
                        == student_id
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
                        f"Order #{order_id} found."
                    )

                    st.metric(
                        "Current Status",
                        status
                    )

                    if status == "Confirmed":

                        st.info(
                            "🟡 Order confirmed."
                        )

                    elif status == "Preparing":

                        st.info(
                            "🔵 Food is being prepared."
                        )

                    elif status == "Ready":

                        st.success(
                            "🟢 Your order is ready "
                            "for collection!"
                        )

                    elif status == "Collected":

                        st.success(
                            "⚫ Order collected. Enjoy!"
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
# MENU MANAGEMENT
# =========================================================

def menu_management():

    st.subheader(
        "🍽️ Menu Management"
    )

    menu = load_menu()

    st.markdown(
        "### ➕ Add New Item"
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        new_name = st.text_input(
            "Item Name",
            key="new_item_name"
        )

    with c2:

        new_price = st.number_input(
            "Price ₹",
            min_value=1.0,
            step=1.0,
            key="new_item_price"
        )

    with c3:

        new_emoji = st.text_input(
            "Emoji",
            value="🍽️",
            key="new_item_emoji"
        )

    if st.button(
        "➕ Add Item",
        use_container_width=True
    ):

        clean_name = new_name.strip()

        if not clean_name:

            st.error(
                "Enter an item name."
            )

        elif clean_name in menu:

            st.error(
                "This item already exists."
            )

        else:

            db.collection(
                "menu"
            ).document(
                clean_name
            ).set(
                {
                    "price":
                        new_price,

                    "discount":
                        0,

                    "available":
                        True,

                    "emoji":
                        new_emoji
                }
            )

            st.success(
                f"{clean_name} added to menu."
            )

            st.rerun()

    st.divider()

    st.markdown(
        "### ✏️ Manage Existing Items"
    )

    for item, data in menu.items():

        with st.container(
            border=True
        ):

            c1, c2, c3, c4 = st.columns(
                [3, 2, 2, 2]
            )

            with c1:

                st.markdown(
                    f"### "
                    f"{data.get('emoji', '🍽️')} "
                    f"{item}"
                )

            with c2:

                new_price = st.number_input(
                    "Price",
                    min_value=1.0,
                    value=float(
                        data.get(
                            "price",
                            0
                        )
                    ),
                    key=f"price_{item}"
                )

            with c3:

                new_discount = st.number_input(
                    "Discount %",
                    min_value=0.0,
                    max_value=90.0,
                    value=float(
                        data.get(
                            "discount",
                            0
                        )
                    ),
                    step=5.0,
                    key=f"discount_{item}"
                )

            with c4:

                available = st.checkbox(
                    "Available",
                    value=data.get(
                        "available",
                        True
                    ),
                    key=f"available_{item}"
                )

            b1, b2 = st.columns(2)

            with b1:

                if st.button(
                    "💾 Save Changes",
                    key=f"save_{item}",
                    use_container_width=True
                ):

                    db.collection(
                        "menu"
                    ).document(
                        item
                    ).update(
                        {
                            "price":
                                new_price,

                            "discount":
                                new_discount,

                            "available":
                                available
                        }
                    )

                    st.success(
                        f"{item} updated."
                    )

                    st.rerun()

            with b2:

                if st.button(
                    "🗑️ Remove Item",
                    key=f"delete_{item}",
                    use_container_width=True
                ):

                    db.collection(
                        "menu"
                    ).document(
                        item
                    ).delete()

                    if item in st.session_state.cart:

                        del st.session_state.cart[
                            item
                        ]

                    st.success(
                        f"{item} removed."
                    )

                    st.rerun()


# =========================================================
# CAFETERIA DASHBOARD
# =========================================================

def cafeteria_page():

    st.markdown(
        '<div class="main-title">'
        '👨‍🍳 Cafeteria Dashboard'
        '</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "🏠 Return to Home",
        type="primary"
    ):

        st.session_state.page = "home"

        st.rerun()

    st.divider()

    if not firebase_connected:

        st.error(
            "Firebase connection failed."
        )

        return

    st.success(
        "🟢 Firebase connected successfully"
    )

    # -----------------------------------------------------
    # MENU
    # -----------------------------------------------------

    with st.expander(
        "🍽️ Manage Menu & Discounts",
        expanded=False
    ):

        menu_management()

    st.divider()

    # -----------------------------------------------------
    # LOAD ORDERS
    # -----------------------------------------------------

    today = current_india_time().strftime(
        "%Y-%m-%d"
    )

    orders = []

    try:

        docs = (
            db.collection("orders")
            .stream()
        )

        for doc in docs:

            data = doc.to_dict()

            if data.get("date") == today:

                data["_doc_id"] = doc.id

                orders.append(data)

    except Exception as e:

        st.error(
            f"Could not load orders: {e}"
        )

        return

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    total_orders = len(orders)

    pending = sum(
        1
        for o in orders
        if o.get("status")
        in [
            "Confirmed",
            "Preparing"
        ]
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

    m1, m2, m3, m4 = st.columns(4)

    with m1:

        st.metric(
            "Today's Orders",
            total_orders
        )

    with m2:

        st.metric(
            "Pending",
            pending
        )

    with m3:

        st.metric(
            "Ready",
            ready
        )

    with m4:

        st.metric(
            "Sales",
            f"₹{revenue:.0f}"
        )

    # -----------------------------------------------------
    # SEARCH
    # -----------------------------------------------------

    st.divider()

    c1, c2 = st.columns(2)

    with c1:

        search = st.text_input(
            "🔎 Search Order ID"
        ).strip()

    with c2:

        filter_status = st.selectbox(
            "Filter Status",
            [
                "All",
                "Confirmed",
                "Preparing",
                "Ready",
                "Collected"
            ]
        )

    filtered = orders.copy()

    if search:

        filtered = [

            o

            for o in filtered

            if str(
                o.get(
                    "order_id",
                    ""
                )
            )
            == search
        ]

    if filter_status != "All":

        filtered = [

            o

            for o in filtered

            if o.get(
                "status"
            )
            == filter_status
        ]

    filtered.reverse()

    # -----------------------------------------------------
    # ORDERS
    # -----------------------------------------------------

    st.subheader(
        f"🍽️ Today's Orders ({len(filtered)})"
    )

    if not filtered:

        st.info(
            "No matching orders."
        )

    else:

        for order in filtered:

            status = order.get(
                "status",
                "Unknown"
            )

            order_type = order.get(
                "order_type",
                ""
            )

            with st.container(
                border=True
            ):

                c1, c2 = st.columns(
                    [5, 2]
                )

                with c1:

                    st.markdown(
                        f"## "
                        f"#{order.get('order_id')}"
                    )

                    st.write(
                        f"**Student:** "
                        f"{order.get('student_name')}"
                    )

                    st.write(
                        f"**Student ID:** "
                        f"{order.get('student_id')}"
                    )

                    st.write(
                        f"**Type:** "
                        f"{order_type}"
                    )

                    if order.get(
                        "break_time"
                    ):

                        st.write(
                            f"**Break:** "
                            f"{order.get('break_time')}"
                        )

                    st.write(
                        f"**Items:** "
                        f"{order.get('items')}"
                    )

                    st.write(
                        f"**Total:** "
                        f"₹{order.get('total', 0):.0f}"
                    )

                with c2:

                    st.markdown(
                        f"### "
                        f"{status}"
                    )

                    # BREAK ORDER
                    if order_type == "Break Order":

                        st.caption(
                            "Break order: "
                            "no preparation-status "
                            "updates required."
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

                                update_status(
                                    order["_doc_id"],
                                    "Collected"
                                )

                    # REGULAR ORDER
                    else:

                        if status == "Confirmed":

                            if st.button(
                                "▶ Start Preparing",
                                key=(
                                    "start_"
                                    + order["_doc_id"]
                                ),
                                use_container_width=True
                            ):

                                update_status(
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

                                update_status(
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

                                update_status(
                                    order["_doc_id"],
                                    "Collected"
                                )

    # -----------------------------------------------------
    # FEEDBACK
    # -----------------------------------------------------

    st.divider()

    st.subheader(
        "⭐ Customer Feedback"
    )

    feedbacks = []

    try:

        docs = (
            db.collection(
                "feedbacks"
            ).stream()
        )

        for doc in docs:

            feedbacks.append(
                doc.to_dict()
            )

    except Exception:

        pass

    if not feedbacks:

        st.info(
            "No feedback yet."
        )

    else:

        ratings = [

            int(
                f.get(
                    "rating",
                    0
                )
            )

            for f in feedbacks

            if f.get(
                "rating"
            )
        ]

        if ratings:

            average = (
                sum(ratings)
                / len(ratings)
            )

            a, b = st.columns(2)

            with a:

                st.metric(
                    "Average Rating",
                    f"{average:.1f} ⭐"
                )

            with b:

                st.metric(
                    "Responses",
                    len(ratings)
                )

        for feedback in reversed(
            feedbacks[-5:]
        ):

            st.write(
                f"**Order #{feedback.get('order_id')}** "
                f"{'⭐' * int(feedback.get('rating', 0))}"
            )

            if feedback.get("comment"):

                st.write(
                    f"_{feedback.get('comment')}_"
                )

            st.divider()


# =========================================================
# UPDATE STATUS
# =========================================================

def update_status(
    doc_id,
    status
):

    try:

        db.collection(
            "orders"
        ).document(
            doc_id
        ).update(
            {
                "status":
                    status,

                "updated_at":
                    current_india_time()
            }
        )

        st.rerun()

    except Exception as e:

        st.error(
            f"Could not update status: {e}"
        )


# =========================================================
# FEEDBACK PAGE
# =========================================================

def feedback_page():

    st.markdown(
        '<div class="main-title">'
        '⭐ Feedback'
        '</div>',
        unsafe_allow_html=True
    )

    order_id = st.text_input(
        "Order ID"
    ).strip()

    rating = st.slider(
        "Overall Experience",
        1,
        5,
        5
    )

    food = st.select_slider(
        "Food Quality",
        [
            "Poor",
            "Average",
            "Good",
            "Very Good",
            "Excellent"
        ]
    )

    service = st.select_slider(
        "Service",
        [
            "Poor",
            "Average",
            "Good",
            "Very Good",
            "Excellent"
        ]
    )

    comment = st.text_area(
        "Comments",
        placeholder="Tell us what we can improve."
    )

    if st.button(
        "⭐ Submit Feedback",
        type="primary",
        use_container_width=True
    ):

        if not order_id:

            st.error(
                "Please enter Order ID."
            )

        else:

            db.collection(
                "feedbacks"
            ).add(
                {
                    "order_id":
                        order_id,

                    "rating":
                        rating,

                    "food_quality":
                        food,

                    "service":
                        service,

                    "comment":
                        comment.strip(),

                    "created_at":
                        current_india_time()
                }
            )

            st.success(
                "Thank you for your feedback! ⭐"
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
# ROUTING
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
