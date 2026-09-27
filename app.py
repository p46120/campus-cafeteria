import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
from io import BytesIO
import base64
import json
from PIL import Image


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="Campus Cafeteria",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

.stApp {
    background: #f7f9fc;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #eef3f8;
}

/* Headings */
h1, h2, h3 {
    color: #29384d;
}

/* Main portal header */
.portal-header {
    background: linear-gradient(
        135deg,
        #eaf2fb,
        #f5f8fb
    );
    border: 1px solid #dce5ef;
    border-radius: 18px;
    padding: 24px;
    margin-bottom: 22px;
}

.portal-title {
    font-size: 30px;
    font-weight: 700;
    color: #29435c;
}

.portal-subtitle {
    color: #718096;
    margin-top: 5px;
}

/* General card */
.soft-card {
    background: white;
    border: 1px solid #e4e9ef;
    border-radius: 16px;
    padding: 20px;
    margin-bottom: 15px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

/* Order card */
.order-card {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 16px;
    padding: 18px;
    margin-bottom: 15px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
}

/* Metric card */
.metric-box {
    background: white;
    border-radius: 16px;
    padding: 18px;
    border: 1px solid #e1e7ee;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    text-align: center;
}

.metric-icon {
    font-size: 25px;
}

.metric-label {
    color: #718096;
    font-size: 14px;
    margin-top: 4px;
}

.metric-number {
    color: #26364a;
    font-size: 30px;
    font-weight: 700;
    margin-top: 4px;
}

/* Labels */
.break-label {
    display: inline-block;
    background: #f0ebff;
    color: #6b4bb3;
    padding: 5px 11px;
    border-radius: 18px;
    font-weight: 600;
    font-size: 13px;
}

.regular-label {
    display: inline-block;
    background: #e8f6f4;
    color: #28786f;
    padding: 5px 11px;
    border-radius: 18px;
    font-weight: 600;
    font-size: 13px;
}

/* Status */
.status-confirmed {
    color: #2468a8;
    background: #eaf3ff;
    padding: 5px 10px;
    border-radius: 15px;
    font-weight: 600;
}

.status-preparing {
    color: #a46700;
    background: #fff3df;
    padding: 5px 10px;
    border-radius: 15px;
    font-weight: 600;
}

.status-ready {
    color: #20844a;
    background: #e8f7ef;
    padding: 5px 10px;
    border-radius: 15px;
    font-weight: 600;
}

.status-collected {
    color: #69727d;
    background: #edf0f3;
    padding: 5px 10px;
    border-radius: 15px;
    font-weight: 600;
}

/* Popular */
.popular-label {
    color: #9a6b00;
    background: #fff6d9;
    padding: 4px 9px;
    border-radius: 14px;
    font-size: 12px;
    font-weight: 600;
}

/* Out of stock */
.stock-label {
    color: #b33a3a;
    background: #fdeaea;
    padding: 4px 9px;
    border-radius: 14px;
    font-size: 12px;
    font-weight: 600;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# FIREBASE
# =========================================================

@st.cache_resource
def init_firebase():

    if not firebase_admin._apps:

        firebase_json = st.secrets["firebase_json"]

        cred = credentials.Certificate(
            json.loads(firebase_json)
        )

        firebase_admin.initialize_app(cred)

    return firestore.client()


try:

    db = init_firebase()
    firebase_ok = True

except Exception as e:

    db = None
    firebase_ok = False

    st.error("Firebase connection failed.")
    st.code(str(e))


# =========================================================
# DEFAULT MENU
# =========================================================

DEFAULT_MENU = {

    "Tea": {
        "price": 15,
        "emoji": "☕",
        "discount": 0,
        "available": True,
        "popular": True,
        "image": None
    },

    "Sandwich": {
        "price": 40,
        "emoji": "🥪",
        "discount": 0,
        "available": True,
        "popular": False,
        "image": None
    },

    "Maggi": {
        "price": 35,
        "emoji": "🍜",
        "discount": 0,
        "available": True,
        "popular": True,
        "image": None
    },

    "Cold Coffee": {
        "price": 30,
        "emoji": "🥤",
        "discount": 0,
        "available": True,
        "popular": False,
        "image": None
    },

    "Veg Roll": {
        "price": 45,
        "emoji": "🌯",
        "discount": 0,
        "available": True,
        "popular": True,
        "image": None
    },

    "Water Bottle": {
        "price": 20,
        "emoji": "💧",
        "discount": 0,
        "available": True,
        "popular": False,
        "image": None
    }
}


# =========================================================
# IMAGE HELPERS
# =========================================================

def image_to_base64(uploaded_file):

    try:

        image = Image.open(uploaded_file)

        image.thumbnail((700, 700))

        buffer = BytesIO()

        image.convert("RGB").save(
            buffer,
            format="JPEG",
            quality=70,
            optimize=True
        )

        return base64.b64encode(
            buffer.getvalue()
        ).decode()

    except Exception:

        return None


def show_base64_image(image_data, width=120):

    if not image_data:
        return False

    try:

        image_bytes = base64.b64decode(
            image_data
        )

        st.image(
            image_bytes,
            width=width
        )

        return True

    except Exception:

        return False


# =========================================================
# MENU FUNCTIONS
# =========================================================

def load_menu():

    if not firebase_ok:
        return DEFAULT_MENU

    try:

        docs = db.collection("menu").stream()

        menu = {}

        for doc in docs:

            data = doc.to_dict()

            menu[doc.id] = {

                "price": data.get("price", 0),

                "emoji": data.get(
                    "emoji",
                    "🍽️"
                ),

                "discount": data.get(
                    "discount",
                    0
                ),

                "available": data.get(
                    "available",
                    True
                ),

                "popular": data.get(
                    "popular",
                    False
                ),

                "image": data.get(
                    "image",
                    None
                )
            }

        if not menu:

            for name, data in DEFAULT_MENU.items():

                db.collection("menu").document(
                    name
                ).set(data)

            return DEFAULT_MENU

        return menu

    except Exception as e:

        st.error(
            f"Could not load menu: {e}"
        )

        return {}


def discounted_price(item):

    price = float(
        item.get("price", 0)
    )

    discount = float(
        item.get("discount", 0)
    )

    return round(
        price * (1 - discount / 100),
        2
    )


# =========================================================
# BREAK TIMES
# =========================================================

BREAK_OPTIONS = [

    "10:30 AM – 11:00 AM",

    "11:00 AM – 11:30 AM",

    "12:30 PM – 2:00 PM",

    "1:00 PM – 2:00 PM",

    "3:30 PM – 4:00 PM",

    "5:30 PM – 6:00 PM",

    "7:30 PM – 8:00 PM",

    "9:30 PM – 10:00 PM"
]


# =========================================================
# ORDER ID
# =========================================================

def generate_daily_order_id():

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    counter_ref = (
        db.collection("counters")
        .document(today)
    )

    transaction = db.transaction()

    @firestore.transactional
    def update_counter(
        transaction,
        ref
    ):

        snapshot = ref.get(
            transaction=transaction
        )

        if snapshot.exists:

            current = snapshot.to_dict().get(
                "count",
                0
            )

        else:

            current = 0

        new_count = current + 1

        transaction.set(
            ref,
            {
                "count": new_count
            },
            merge=True
        )

        return new_count

    number = update_counter(
        transaction,
        counter_ref
    )

    return f"{number:03d}"


# =========================================================
# FIND ORDER DOCUMENT
# =========================================================

def find_order_document(order):

    """
    Finds the actual Firestore document instead of assuming
    the document ID.

    This fixes the old-order problem such as #111240.
    """

    order_id = str(
        order.get("order_id", "")
    )

    date = order.get("date")

    # First try current naming convention
    if date:

        possible_id = f"{date}_{order_id}"

        ref = (
            db.collection("orders")
            .document(possible_id)
        )

        try:

            if ref.get().exists:
                return ref

        except Exception:
            pass

    # If not found, search orders
    try:

        docs = db.collection("orders").stream()

        for doc in docs:

            data = doc.to_dict()

            if str(
                data.get("order_id", "")
            ) == order_id:

                if not date or data.get("date") == date:
                    return doc.reference

    except Exception:
        pass

    return None


# =========================================================
# UPDATE ORDER STATUS
# =========================================================

def update_order_status(
    order,
    new_status
):

    try:

        order_ref = find_order_document(
            order
        )

        if order_ref is None:

            st.error(
                "Order document could not be found."
            )

            return

        order_ref.update({

            "status": new_status,

            "updated_at":
                firestore.SERVER_TIMESTAMP
        })

        st.success(
            f"Order #{order.get('order_id')} "
            f"marked as {new_status}."
        )

        st.rerun()

    except Exception as e:

        st.error(
            f"Could not update order: {e}"
        )


# =========================================================
# SESSION STATE
# =========================================================

if "cart" not in st.session_state:
    st.session_state.cart = {}

if "page" not in st.session_state:
    st.session_state.page = "Home"

if "last_order" not in st.session_state:
    st.session_state.last_order = None


# =========================================================
# HOME
# =========================================================

def home_page():

    st.markdown("""
    <div class="portal-header">

        <div class="portal-title">
            🍽️ Campus Cafeteria
        </div>

        <div class="portal-subtitle">
            Fast ordering for students •
            Simple management for cafeteria staff
        </div>

    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:

        st.markdown("""
        <div class="soft-card">

        <h2>🎓 Student Portal</h2>

        <p>
        Pre-order your food and collect it
        quickly from the cafeteria counter.
        </p>

        </div>
        """, unsafe_allow_html=True)

        if st.button(
            "🍴 Order Food",
            type="primary",
            use_container_width=True
        ):

            st.session_state.page = "Student"
            st.rerun()

    with col2:

        st.markdown("""
        <div class="soft-card">

        <h2>📋 Cafeteria Portal</h2>

        <p>
        Manage orders, menu, availability,
        popular items and feedback.
        </p>

        </div>
        """, unsafe_allow_html=True)

        if st.button(
            "📋 Open Cafeteria Portal",
            use_container_width=True
        ):

            st.session_state.page = "Cafeteria"
            st.rerun()

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(
            "⚡ **Fast ordering**\n\n"
            "Order before reaching the counter."
        )

    with col2:
        st.success(
            "📱 **Track order**\n\n"
            "See preparation status."
        )

    with col3:
        st.warning(
            "🎟️ **Easy pickup**\n\n"
            "Show your Order ID."
        )


# =========================================================
# STUDENT PAGE
# =========================================================

def student_page():

    menu = load_menu()

    st.title("🍽️ Order Food")

    if st.button("← Back to Home"):
        go_home()

    st.subheader("Choose Order Type")

    order_type = st.radio(
        "",
        [
            "Break Order",
            "Regular Order"
        ],
        horizontal=True
    )

    if order_type == "Break Order":

        st.info(
            "🕐 Select your break and "
            "order in advance."
        )

        break_time = st.selectbox(
            "Select Break",
            BREAK_OPTIONS
        )

    else:

        st.markdown("""
        <div class="soft-card">

        <h3>🏠 Room / Hostel Pre-order</h3>

        <p>
        Order from your room or hostel.
        The cafeteria will prepare it and
        you can collect it from the counter.
        </p>

        <p>
        ⏱️ Typical preparation time:
        <b>10–15 minutes</b>
        </p>

        </div>
        """, unsafe_allow_html=True)

        break_time = None

    st.divider()

    # =====================================================
    # POPULAR PICKS
    # =====================================================

    st.subheader("🔥 Popular Picks")

    popular_items = [

        name for name, data in menu.items()

        if data.get("available", True)
        and data.get("popular", False)
    ]

    if popular_items:

        cols = st.columns(
            min(len(popular_items), 4)
        )

        for i, item_name in enumerate(
            popular_items
        ):

            item = menu[item_name]

            with cols[
                i % len(cols)
            ]:

                st.markdown(
                    '<div class="soft-card">',
                    unsafe_allow_html=True
                )

                if item.get("image"):

                    show_base64_image(
                        item["image"],
                        width=130
                    )

                else:

                    st.markdown(
                        f"<h1>{item.get('emoji', '🍽️')}</h1>",
                        unsafe_allow_html=True
                    )

                st.markdown(
                    f"**{item_name}**"
                )

                st.caption(
                    f"₹{discounted_price(item):.0f}"
                )

                if st.button(
                    f"Add {item_name}",
                    key=f"popular_{item_name}",
                    use_container_width=True
                ):

                    st.session_state.cart[
                        item_name
                    ] = (
                        st.session_state.cart.get(
                            item_name,
                            0
                        ) + 1
                    )

                    st.success(
                        "Added!"
                    )

                st.markdown(
                    '</div>',
                    unsafe_allow_html=True
                )

    else:

        st.info(
            "Cafeteria has not selected "
            "popular items yet."
        )

    # =====================================================
    # MENU
    # =====================================================

    st.divider()

    st.subheader("🍴 Menu")

    available_items = {

        name: data

        for name, data in menu.items()

        if data.get(
            "available",
            True
        )
    }

    if not available_items:

        st.warning(
            "No items are currently available."
        )

        return

    for item_name, item in available_items.items():

        col1, col2, col3 = st.columns(
            [1, 5, 1]
        )

        with col1:

            if item.get("image"):

                show_base64_image(
                    item["image"],
                    width=85
                )

            else:

                st.markdown(
                    f"<h2>{item.get('emoji', '🍽️')}</h2>",
                    unsafe_allow_html=True
                )

        with col2:

            original = float(
                item.get("price", 0)
            )

            final_price = discounted_price(
                item
            )

            discount = float(
                item.get("discount", 0)
            )

            st.markdown(
                f"### {item_name}"
            )

            if item.get("popular"):

                st.markdown(
                    '<span class="popular-label">'
                    '⭐ Popular'
                    '</span>',
                    unsafe_allow_html=True
                )

            if discount > 0:

                st.markdown(
                    f"~~₹{original:.0f}~~ "
                    f"**₹{final_price:.0f}** "
                    f"🟢 {discount:.0f}% OFF"
                )

            else:

                st.write(
                    f"₹{final_price:.0f}"
                )

        with col3:

            if st.button(
                "Add",
                key=f"add_{item_name}",
                use_container_width=True
            ):

                st.session_state.cart[
                    item_name
                ] = (
                    st.session_state.cart.get(
                        item_name,
                        0
                    ) + 1
                )

                st.success(
                    "Added"
                )

    # =====================================================
    # CART
    # =====================================================

    st.divider()

    st.subheader("🛒 Your Cart")

    if not st.session_state.cart:

        st.info(
            "Your cart is empty."
        )

    else:

        total = 0

        for item_name, quantity in list(
            st.session_state.cart.items()
        ):

            item = menu.get(
                item_name
            )

            if not item:
                continue

            price = discounted_price(
                item
            )

            subtotal = (
                price * quantity
            )

            total += subtotal

            col1, col2, col3, col4 = st.columns(
                [4, 1, 1, 1]
            )

            with col1:

                st.write(
                    f"{item.get('emoji', '🍽️')} "
                    f"**{item_name}**"
                )

            with col2:

                st.write(
                    f"₹{price:.0f}"
                )

            with col3:

                st.write(
                    f"x {quantity}"
                )

            with col4:

                if st.button(
                    "Remove",
                    key=f"remove_{item_name}"
                ):

                    del st.session_state.cart[
                        item_name
                    ]

                    st.rerun()

        st.markdown(
            f"### Total: ₹{total:.0f}"
        )

        st.divider()

        st.subheader(
            "Student Details"
        )

        student_name = st.text_input(
            "Student Name"
        )

        student_id = st.text_input(
            "Student ID"
        )

        if st.button(
            "🚀 Place Order",
            type="primary",
            use_container_width=True
        ):

            if not student_name.strip():

                st.warning(
                    "Please enter your name."
                )

                return

            if not student_id.strip():

                st.warning(
                    "Please enter your Student ID."
                )

                return

            try:

                order_id = (
                    generate_daily_order_id()
                )

                today = datetime.now().strftime(
                    "%Y-%m-%d"
                )

                order_data = {

                    "order_id": order_id,

                    "student_name":
                        student_name,

                    "student_id":
                        student_id,

                    "order_type":
                        order_type,

                    "break_time":
                        break_time,

                    "items":
                        dict(
                            st.session_state.cart
                        ),

                    "total":
                        total,

                    "status":
                        "Confirmed",

                    "date":
                        today,

                    "created_at":
                        firestore.SERVER_TIMESTAMP
                }

                db.collection(
                    "orders"
                ).document(
                    f"{today}_{order_id}"
                ).set(
                    order_data
                )

                st.session_state.last_order = (
                    order_id
                )

                st.session_state.cart = {}

                st.session_state.page = (
                    "Confirmation"
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

    order_id = (
        st.session_state.last_order
    )

    st.markdown("""
    <div class="soft-card"
         style="text-align:center;">

    <h1>🎉 Order Confirmed!</h1>

    <p>
    Your food order has been successfully placed.
    </p>

    </div>
    """, unsafe_allow_html=True)

    st.metric(
        "Your Order ID",
        order_id
    )

    st.info(
        "📌 Remember your Order ID and "
        "show it at the cafeteria counter."
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "📍 Track My Order",
            use_container_width=True
        ):

            st.session_state.page = "Track"
            st.rerun()

    with col2:

        if st.button(
            "🏠 Return to Home",
            type="primary",
            use_container_width=True
        ):

            go_home()


# =========================================================
# TRACK ORDER
# =========================================================

def track_order_page():

    st.title("📍 Track My Order")

    if st.button("← Back to Home"):
        go_home()

    order_id = st.text_input(
        "Order ID",
        placeholder="Example: 023"
    )

    student_id = st.text_input(
        "Student ID"
    )

    if st.button(
        "🔍 Track Order",
        type="primary"
    ):

        if not order_id or not student_id:

            st.warning(
                "Enter both Order ID and Student ID."
            )

            return

        try:

            orders = (
                db.collection("orders")
                .stream()
            )

            found = None

            for doc in orders:

                data = doc.to_dict()

                if (

                    str(
                        data.get(
                            "order_id",
                            ""
                        )
                    )
                    ==
                    str(order_id).zfill(3)

                    and

                    str(
                        data.get(
                            "student_id",
                            ""
                        )
                    )
                    ==
                    str(student_id)

                ):

                    found = data
                    break

            if not found:

                st.error(
                    "Order not found."
                )

                return

            status = found.get(
                "status",
                "Confirmed"
            )

            st.markdown(
                f"""
                <div class="soft-card">

                <h2>
                Order #{found.get('order_id')}
                </h2>

                <p>
                Student:
                <b>{found.get('student_name')}</b>
                </p>

                <p>
                Current Status:
                <b>{status}</b>
                </p>

                </div>
                """,
                unsafe_allow_html=True
            )

            if found.get(
                "order_type"
            ) == "Break Order":

                if status == "Confirmed":

                    st.success(
                        "🟢 Confirmed"
                    )

                    st.info(
                        "🎟️ Waiting for pickup"
                    )

                else:

                    st.success(
                        "🟢 Confirmed"
                    )

                    st.success(
                        "✅ Collected"
                    )

            else:

                steps = [
                    "Confirmed",
                    "Preparing",
                    "Ready",
                    "Collected"
                ]

                if status in steps:

                    current_index = (
                        steps.index(status)
                    )

                else:

                    current_index = 0

                for i, step in enumerate(
                    steps
                ):

                    if i <= current_index:

                        st.success(
                            f"● {step}"
                        )

                    else:

                        st.write(
                            f"○ {step}"
                        )

        except Exception as e:

            st.error(
                f"Could not track order: {e}"
            )


# =========================================================
# MENU MANAGEMENT
# =========================================================

def menu_management():

    st.subheader(
        "🍽️ Menu Management"
    )

    menu = load_menu()

    # =====================================================
    # ADD ITEM
    # =====================================================

    with st.expander(
        "➕ Add New Item",
        expanded=True
    ):

        col1, col2, col3 = st.columns(3)

        with col1:

            new_name = st.text_input(
                "Item Name"
            )

        with col2:

            new_price = st.number_input(
                "Price ₹",
                min_value=1.0,
                value=20.0,
                step=1.0
            )

        with col3:

            new_emoji = st.text_input(
                "Emoji",
                value="🍽️"
            )

        new_image = st.file_uploader(
            "📷 Add Food Photo",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp"
            ],
            key="new_food_image"
        )

        if new_image:

            st.image(
                new_image,
                width=180
            )

        new_popular = st.checkbox(
            "⭐ Mark as Popular",
            value=False
        )

        if st.button(
            "➕ Add Item",
            type="primary"
        ):

            if not new_name.strip():

                st.warning(
                    "Please enter an item name."
                )

            elif new_name in menu:

                st.warning(
                    "This item already exists."
                )

            else:

                image_data = None

                if new_image:

                    image_data = (
                        image_to_base64(
                            new_image
                        )
                    )

                db.collection(
                    "menu"
                ).document(
                    new_name
                ).set({

                    "price":
                        new_price,

                    "emoji":
                        new_emoji,

                    "discount":
                        0,

                    "available":
                        True,

                    "popular":
                        new_popular,

                    "image":
                        image_data
                })

                st.success(
                    f"{new_name} added!"
                )

                st.rerun()

    # =====================================================
    # EXISTING ITEMS
    # =====================================================

    st.divider()

    st.subheader(
        "✏️ Manage Existing Items"
    )

    for item_name, item in menu.items():

        with st.container(
            border=True
        ):

            col1, col2, col3, col4 = st.columns(
                [2, 1, 1, 1]
            )

            with col1:

                st.markdown(
                    f"### "
                    f"{item.get('emoji', '🍽️')} "
                    f"{item_name}"
                )

                if item.get("image"):

                    show_base64_image(
                        item["image"],
                        width=120
                    )

                if item.get("popular"):

                    st.markdown(
                        '<span class="popular-label">'
                        '⭐ Popular'
                        '</span>',
                        unsafe_allow_html=True
                    )

            with col2:

                price = st.number_input(
                    "Price",
                    min_value=1.0,
                    value=float(
                        item.get(
                            "price",
                            0
                        )
                    ),
                    step=1.0,
                    key=f"price_{item_name}"
                )

            with col3:

                discount = st.number_input(
                    "Discount %",
                    min_value=0.0,
                    max_value=90.0,
                    value=float(
                        item.get(
                            "discount",
                            0
                        )
                    ),
                    step=1.0,
                    key=f"discount_{item_name}"
                )

            with col4:

                available = st.checkbox(
                    "Available",
                    value=item.get(
                        "available",
                        True
                    ),
                    key=f"available_{item_name}"
                )

            popular = st.checkbox(
                "⭐ Show in Popular Picks",
                value=item.get(
                    "popular",
                    False
                ),
                key=f"popular_{item_name}"
            )

            new_photo = st.file_uploader(
                "📷 Change Food Photo",
                type=[
                    "jpg",
                    "jpeg",
                    "png",
                    "webp"
                ],
                key=f"photo_{item_name}"
            )

            if new_photo:

                st.image(
                    new_photo,
                    width=150
                )

            col_a, col_b = st.columns(2)

            with col_a:

                if st.button(
                    "💾 Save Changes",
                    key=f"save_{item_name}",
                    use_container_width=True
                ):

                    update_data = {

                        "price":
                            price,

                        "discount":
                            discount,

                        "available":
                            available,

                        "popular":
                            popular
                    }

                    if new_photo:

                        image_data = (
                            image_to_base64(
                                new_photo
                            )
                        )

                        if image_data:

                            update_data[
                                "image"
                            ] = image_data

                    db.collection(
                        "menu"
                    ).document(
                        item_name
                    ).update(
                        update_data
                    )

                    st.success(
                        f"{item_name} updated!"
                    )

                    st.rerun()

            with col_b:

                if st.button(
                    "🗑️ Remove Item",
                    key=f"delete_{item_name}",
                    use_container_width=True
                ):

                    db.collection(
                        "menu"
                    ).document(
                        item_name
                    ).delete()

                    st.success(
                        f"{item_name} removed."
                    )

                    st.rerun()


# =========================================================
# LOAD TODAY'S ORDERS
# =========================================================

def load_today_orders():

    today = datetime.now().strftime(
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

            if data.get(
                "date"
            ) == today:

                data["_doc_ref"] = (
                    doc.reference
                )

                orders.append(data)

    except Exception as e:

        st.error(
            f"Could not load orders: {e}"
        )

    return orders


# =========================================================
# ORDER CARD
# =========================================================

def render_order_card(
    order,
    break_order=False
):

    order_id = order.get(
        "order_id",
        "---"
    )

    student_name = order.get(
        "student_name",
        "Unknown"
    )

    status = order.get(
        "status",
        "Confirmed"
    )

    items = order.get(
        "items",
        {}
    )

    total = order.get(
        "total",
        0
    )

    st.markdown(
        '<div class="order-card">',
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns(
        [1.2, 4, 2]
    )

    with col1:

        st.markdown(
            f"## #{order_id}"
        )

        if break_order:

            st.markdown(
                '<span class="break-label">'
                '🕐 Break Order'
                '</span>',
                unsafe_allow_html=True
            )

        else:

            st.markdown(
                '<span class="regular-label">'
                '🏠 Regular'
                '</span>',
                unsafe_allow_html=True
            )

    with col2:

        st.markdown(
            f"**{student_name}**"
        )

        item_text = " • ".join(

            [
                f"{name} × {qty}"
                for name, qty
                in items.items()
            ]
        )

        st.caption(
            item_text
        )

        st.write(
            f"Total: **₹{float(total):.0f}**"
        )

        if (
            break_order
            and order.get("break_time")
        ):

            st.caption(
                f"Break: "
                f"{order.get('break_time')}"
            )

    with col3:

        st.markdown(
            f"**Status:** {status}"
        )

        # -------------------------------------------------
        # BREAK ORDER
        # -------------------------------------------------

        if break_order:

            if status == "Confirmed":

                if st.button(
                    "✅ Mark Collected",
                    key=f"collect_break_{order_id}",
                    use_container_width=True
                ):

                    update_order_status(
                        order,
                        "Collected"
                    )

            elif status == "Collected":

                st.success(
                    "✅ Order handed over"
                )

        # -------------------------------------------------
        # REGULAR ORDER
        # -------------------------------------------------

        else:

            if status == "Confirmed":

                if st.button(
                    "🟠 Start Preparing",
                    key=f"prepare_{order_id}",
                    use_container_width=True
                ):

                    update_order_status(
                        order,
                        "Preparing"
                    )

            elif status == "Preparing":

                if st.button(
                    "🟢 Mark Ready",
                    key=f"ready_{order_id}",
                    use_container_width=True
                ):

                    update_order_status(
                        order,
                        "Ready"
                    )

            elif status == "Ready":

                if st.button(
                    "✅ Mark Collected",
                    key=f"collect_{order_id}",
                    use_container_width=True
                ):

                    update_order_status(
                        order,
                        "Collected"
                    )

            elif status == "Collected":

                st.success(
                    "✅ Order handed over"
                )

    st.markdown(
        '</div>',
        unsafe_allow_html=True
    )


# =========================================================
# DATA CLEANUP
# =========================================================

def cleanup_old_data():

    cutoff = (
        datetime.now()
        - timedelta(days=14)
    )

    cutoff_date = cutoff.strftime(
        "%Y-%m-%d"
    )

    deleted_orders = 0
    deleted_feedback = 0

    # -----------------------------------------------------
    # ORDERS
    # -----------------------------------------------------

    try:

        orders = (
            db.collection("orders")
            .stream()
        )

        for doc in orders:

            data = doc.to_dict()

            date_text = data.get(
                "date"
            )

            if date_text:

                try:

                    record_date = (
                        datetime.strptime(
                            date_text,
                            "%Y-%m-%d"
                        )
                    )

                    if record_date < cutoff:

                        doc.reference.delete()

                        deleted_orders += 1

                except Exception:
                    pass

    except Exception as e:

        st.error(
            f"Order cleanup failed: {e}"
        )

    # -----------------------------------------------------
    # FEEDBACK
    # -----------------------------------------------------

    try:

        feedback_docs = (
            db.collection("feedback")
            .stream()
        )

        for doc in feedback_docs:

            data = doc.to_dict()

            date_text = data.get(
                "date"
            )

            if date_text:

                try:

                    record_date = (
                        datetime.strptime(
                            date_text,
                            "%Y-%m-%d"
                        )
                    )

                    if record_date < cutoff:

                        doc.reference.delete()

                        deleted_feedback += 1

                except Exception:
                    pass

    except Exception as e:

        st.error(
            f"Feedback cleanup failed: {e}"
        )

    return (
        deleted_orders,
        deleted_feedback
    )


# =========================================================
# DATA MANAGEMENT UI
# =========================================================

def data_management():

    st.subheader(
        "🧹 Data Management"
    )

    st.info(
        "Order history and feedback older than "
        "**14 days** can be removed to keep "
        "the database clean."
    )

    st.warning(
        "⚠️ Cleanup permanently deletes old "
        "orders and feedback."
    )

    if st.button(
        "🧹 Delete Data Older Than 14 Days",
        type="primary",
        use_container_width=True
    ):

        deleted_orders, deleted_feedback = (
            cleanup_old_data()
        )

        st.success(
            f"Cleanup completed: "
            f"{deleted_orders} old orders and "
            f"{deleted_feedback} old feedback "
            f"records deleted."
        )

        st.rerun()


# =========================================================
# CAFETERIA DASHBOARD
# =========================================================

def cafeteria_page():

    st.markdown("""
    <div class="portal-header">

        <div class="portal-title">
            📋 Cafeteria Portal
        </div>

        <div class="portal-subtitle">
            Manage orders, menu, popular picks,
            availability and feedback
        </div>

    </div>
    """, unsafe_allow_html=True)

    if st.button(
        "← Return to Home"
    ):

        go_home()

    # =====================================================
    # MENU
    # =====================================================

    with st.expander(
        "🍽️ Menu Management"
    ):

        menu_management()

    # =====================================================
    # DATA MANAGEMENT
    # =====================================================

    with st.expander(
        "🧹 Data Management"
    ):

        data_management()

    st.divider()

    # =====================================================
    # DASHBOARD
    # =====================================================

    st.subheader(
        "📊 Today's Dashboard"
    )

    orders = load_today_orders()

    total_orders = len(
        orders
    )

    confirmed = len(
        [
            x for x in orders
            if x.get("status")
            == "Confirmed"
        ]
    )

    preparing = len(
        [
            x for x in orders
            if x.get("status")
            == "Preparing"
        ]
    )

    ready = len(
        [
            x for x in orders
            if x.get("status")
            == "Ready"
        ]
    )

    collected = len(
        [
            x for x in orders
            if x.get("status")
            == "Collected"
        ]
    )

    metrics = [

        (
            "📦",
            "Total Orders",
            total_orders
        ),

        (
            "🔵",
            "Confirmed",
            confirmed
        ),

        (
            "🟠",
            "Preparing",
            preparing
        ),

        (
            "🟢",
            "Ready",
            ready
        ),

        (
            "✅",
            "Collected",
            collected
        )
    ]

    cols = st.columns(5)

    for col, (
        icon,
        label,
        value
    ) in zip(
        cols,
        metrics
    ):

        with col:

            st.markdown(
                f"""
                <div class="metric-box">

                    <div class="metric-icon">
                        {icon}
                    </div>

                    <div class="metric-label">
                        {label}
                    </div>

                    <div class="metric-number">
                        {value}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

    st.divider()

    # =====================================================
    # SEARCH / FILTER
    # =====================================================

    st.subheader(
        "📋 Today's Orders"
    )

    col1, col2 = st.columns(2)

    with col1:

        search = st.text_input(
            "🔍 Search Order ID / Student",
            placeholder="Example: 023"
        )

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

    if search:

        search_lower = (
            search.lower()
        )

        filtered_orders = [

            x for x in filtered_orders

            if (
                search_lower
                in str(
                    x.get(
                        "order_id",
                        ""
                    )
                ).lower()
            )

            or

            (
                search_lower
                in str(
                    x.get(
                        "student_name",
                        ""
                    )
                ).lower()
            )
        ]

    if status_filter != "All":

        filtered_orders = [

            x for x in filtered_orders

            if x.get(
                "status"
            ) == status_filter
        ]

    # =====================================================
    # SEPARATE ORDERS
    # =====================================================

    break_orders = [

        x for x in filtered_orders

        if x.get(
            "order_type"
        ) == "Break Order"
    ]

    regular_orders = [

        x for x in filtered_orders

        if x.get(
            "order_type"
        ) == "Regular Order"
    ]

    if break_orders:

        st.markdown(
            "### 🕐 Break Orders"
        )

        for order in break_orders:

            render_order_card(
                order,
                break_order=True
            )

    if regular_orders:

        st.markdown(
            "### 🏠 Regular Orders"
        )

        for order in regular_orders:

            render_order_card(
                order,
                break_order=False
            )

    if not break_orders and not regular_orders:

        st.info(
            "No orders match the current filter."
        )


# =========================================================
# FEEDBACK
# =========================================================

def feedback_page():

    st.title(
        "⭐ Feedback"
    )

    if st.button(
        "← Back to Home"
    ):

        go_home()

    st.write(
        "Tell us about your cafeteria experience."
    )

    order_id = st.text_input(
        "Order ID"
    )

    rating = st.slider(
        "Rating",
        1,
        5,
        5
    )

    comment = st.text_area(
        "Comments",
        placeholder=(
            "Tell us what you liked "
            "or what needs improvement..."
        )
    )

    feedback_image = st.file_uploader(
        "📷 Add Photo (optional)",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp"
        ],
        key="feedback_image"
    )

    if feedback_image:

        st.image(
            feedback_image,
            width=250
        )

    if st.button(
        "⭐ Submit Feedback",
        type="primary",
        use_container_width=True
    ):

        image_data = None

        if feedback_image:

            image_data = (
                image_to_base64(
                    feedback_image
                )
            )

        today = datetime.now().strftime(
            "%Y-%m-%d"
        )

        db.collection(
            "feedback"
        ).add({

            "order_id":
                order_id,

            "rating":
                rating,

            "comment":
                comment,

            "image":
                image_data,

            "date":
                today,

            "created_at":
                firestore.SERVER_TIMESTAMP
        })

        st.success(
            "Thank you for your feedback! ❤️"
        )


# =========================================================
# NAVIGATION
# =========================================================

def go_home():

    st.session_state.page = "Home"

    st.rerun()


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        "## 🍽️ Campus Cafeteria"
    )

    st.caption(
        "Quick • Simple • Campus-friendly"
    )

    st.divider()

    if st.button(
        "🏠 Home",
        use_container_width=True
    ):

        st.session_state.page = "Home"
        st.rerun()

    if st.button(
        "🍴 Student Portal",
        use_container_width=True
    ):

        st.session_state.page = "Student"
        st.rerun()

    if st.button(
        "📍 Track Order",
        use_container_width=True
    ):

        st.session_state.page = "Track"
        st.rerun()

    if st.button(
        "📋 Cafeteria Portal",
        use_container_width=True
    ):

        st.session_state.page = "Cafeteria"
        st.rerun()

    if st.button(
        "⭐ Feedback",
        use_container_width=True
    ):

        st.session_state.page = "Feedback"
        st.rerun()

    st.divider()

    if firebase_ok:

        st.success(
            "🟢 Firebase connected"
        )

    else:

        st.error(
            "🔴 Firebase disconnected"
        )


# =========================================================
# PAGE ROUTING
# =========================================================

if st.session_state.page == "Home":

    home_page()

elif st.session_state.page == "Student":

    student_page()

elif st.session_state.page == "Confirmation":

    confirmation_page()

elif st.session_state.page == "Track":

    track_order_page()

elif st.session_state.page == "Cafeteria":

    cafeteria_page()

elif st.session_state.page == "Feedback":

    feedback_page()
