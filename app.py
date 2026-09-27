import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
from google.cloud.firestore_v1 import transactional
from datetime import datetime, date, timedelta
import requests
import json
import base64
import io
from PIL import Image


# ============================================================
# APP CONFIG
# ============================================================

st.set_page_config(
    page_title="Campus Cafeteria",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CAFETERIA_NAME = "Campus Cafeteria"

# Cafeteria Login
CAFETERIA_LOGIN_ID = "cafeteria"
CAFETERIA_PASSWORD = "Campus@123"

# Cafeteria Desk Contact
DESK_NAME = "Rahul"
DESK_PHONE = "9065334992"
DESK_EMAIL = "rahulraj1244raj@gmail.com"

# ============================================================
# BREAK OPTIONS
# ============================================================

BREAK_OPTIONS = [
    "10:30 AM – 11:00 AM",
    "11:00 AM – 11:30 AM",
    "12:30 PM – 2:00 PM",
    "1:00 PM – 2:00 PM",
    "3:30 PM – 4:00 PM",
    "5:30 PM – 6:00 PM",
    "7:30 PM – 8:00 PM",
    "9:30 PM – 10:00 PM",
]


# ============================================================
# DEFAULT MENU
# ============================================================

DEFAULT_MENU = [
    {
        "name": "Veg Roll",
        "price": 40,
        "available": True,
        "discount": 0,
        "popular": True,
        "image": "",
    },
    {
        "name": "Maggi",
        "price": 40,
        "available": True,
        "discount": 0,
        "popular": True,
        "image": "",
    },
    {
        "name": "Sandwich",
        "price": 50,
        "available": True,
        "discount": 0,
        "popular": True,
        "image": "",
    },
    {
        "name": "Samosa",
        "price": 15,
        "available": True,
        "discount": 0,
        "popular": False,
        "image": "",
    },
    {
        "name": "Tea",
        "price": 20,
        "available": True,
        "discount": 0,
        "popular": True,
        "image": "",
    },
    {
        "name": "Coffee",
        "price": 30,
        "available": True,
        "discount": 0,
        "popular": False,
        "image": "",
    },
    {
        "name": "Cold Drink",
        "price": 30,
        "available": True,
        "discount": 0,
        "popular": False,
        "image": "",
    },
]


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background: #f7f8fc;
}

.block-container {
    max-width: 1250px;
    padding-top: 1.3rem;
}

/* HERO */

.hero {
    padding: 2.2rem;
    border-radius: 26px;
    background: linear-gradient(
        135deg,
        #fff7ed 0%,
        #ffffff 52%,
        #eff6ff 100%
    );
    border: 1px solid #e5e7eb;
    margin-bottom: 1.25rem;
}

.hero h1 {
    font-size: 2.65rem;
    margin: 0;
    color: #111827;
}

.hero p {
    font-size: 1.08rem;
    color: #6b7280;
    margin: .6rem 0 0;
}

/* GENERAL CARD */

.card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 1.1rem;
    box-shadow: 0 2px 10px rgba(0,0,0,.035);
}

.card h3 {
    margin: .15rem 0 .45rem;
    color: #111827;
}

.card p {
    margin: 0;
    color: #6b7280;
}

/* FOOD CARD */

.food-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 2px 10px rgba(0,0,0,.04);
}

.food-card img {
    width: 100%;
    height: 145px;
    object-fit: cover;
}

.food-card-body {
    padding: 1rem;
}

.food-card-title {
    font-size: 1.08rem;
    font-weight: 700;
    color: #111827;
}

/* ORDER ID */

.order-id {
    font-size: 2.1rem;
    font-weight: 800;
    text-align: center;
    color: #111827;
}

/* SUCCESS */

.success-box {
    padding: 1.15rem;
    border-radius: 18px;
    background: #ecfdf5;
    border: 1px solid #a7f3d0;
}

/* LOGIN */

.login-box {
    max-width: 560px;
    margin: 1rem auto;
    padding: 1.5rem;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 22px;
}

/* SMALL TEXT */

.small-muted {
    color: #6b7280;
    font-size: .9rem;
}

/* METRICS */

div[data-testid="stMetric"] {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    padding: 10px;
    border-radius: 16px;
}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# FIREBASE INITIALIZATION
# ============================================================

@st.cache_resource
def init_firebase():

    if not firebase_admin._apps:

        firebase_json = st.secrets.get(
            "firebase_json"
        )

        if not firebase_json:
            raise RuntimeError(
                "firebase_json is missing from Streamlit Secrets."
            )

        if isinstance(firebase_json, str):
            firebase_json = json.loads(
                firebase_json
            )

        cred = credentials.Certificate(
            firebase_json
        )

        firebase_admin.initialize_app(
            cred
        )

    return firestore.client()


try:

    db = init_firebase()

    firebase_connected = True
    firebase_error = ""

except Exception as e:

    db = None

    firebase_connected = False
    firebase_error = str(e)


def get_web_api_key():

    return st.secrets.get(
        "firebase_web_api_key",
        "",
    )


# ============================================================
# IMAGE FUNCTIONS
# ============================================================

def image_to_data_url(
    uploaded_file,
    max_size=600,
    quality=78,
):

    if uploaded_file is None:
        return ""

    try:

        img = Image.open(
            uploaded_file
        ).convert("RGB")

        img.thumbnail(
            (
                max_size,
                max_size,
            )
        )

        buffer = io.BytesIO()

        img.save(
            buffer,
            format="JPEG",
            quality=quality,
            optimize=True,
        )

        encoded = base64.b64encode(
            buffer.getvalue()
        ).decode("utf-8")

        return (
            "data:image/jpeg;base64,"
            + encoded
        )

    except Exception:

        return ""


def image_html(
    data_url,
    height=145,
):

    if not data_url:
        return ""

    return (
        f'<img src="{data_url}" '
        f'style="width:100%;'
        f'height:{height}px;'
        f'object-fit:cover;'
        f'border-radius:14px;'
        f'margin-bottom:8px;">'
    )


# ============================================================
# FIREBASE AUTH REST
# ============================================================

def auth_request(
    endpoint,
    payload,
):

    api_key = get_web_api_key()

    if not api_key:

        return (
            None,
            "Firebase Web API Key is missing from "
            "Streamlit Secrets.",
        )

    url = (
        "https://identitytoolkit.googleapis.com/v1/"
        f"{endpoint}?key={api_key}"
    )

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=20,
        )

        data = response.json()

        if response.ok:
            return data, None

        message = (
            data
            .get("error", {})
            .get(
                "message",
                "Authentication failed.",
            )
        )

        return None, message

    except Exception as e:

        return None, str(e)


def signup_student(
    email,
    password,
):

    return auth_request(
        "accounts:signUp",
        {
            "email": email,
            "password": password,
            "returnSecureToken": True,
        },
    )


def login_student(
    email,
    password,
):

    return auth_request(
        "accounts:signInWithPassword",
        {
            "email": email,
            "password": password,
            "returnSecureToken": True,
        },
    )


def send_password_reset(
    email,
):

    return auth_request(
        "accounts:sendOobCode",
        {
            "requestType": "PASSWORD_RESET",
            "email": email,
        },
    )


def refresh_id_token(
    refresh_token,
):

    api_key = get_web_api_key()

    if not api_key:

        return (
            None,
            "Firebase Web API Key is missing.",
        )

    url = (
        "https://securetoken.googleapis.com/v1/token"
        f"?key={api_key}"
    )

    try:

        response = requests.post(
            url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            timeout=20,
        )

        data = response.json()

        if response.ok:
            return data, None

        return (
            None,
            data
            .get("error", {})
            .get(
                "message",
                "Could not refresh session.",
            ),
        )

    except Exception as e:

        return None, str(e)


def get_logged_in_uid():

    session = st.session_state.get(
        "auth_session"
    )

    if not session:
        return None

    try:

        login_time = session.get(
            "login_time",
            0,
        )

        if (
            datetime.now().timestamp()
            - login_time
            > 3000
        ):

            refreshed, error = (
                refresh_id_token(
                    session[
                        "refresh_token"
                    ]
                )
            )

            if error:

                st.session_state.pop(
                    "auth_session",
                    None,
                )

                st.session_state.pop(
                    "student_user",
                    None,
                )

                return None

            session[
                "id_token"
            ] = refreshed[
                "id_token"
            ]

            session[
                "refresh_token"
            ] = refreshed[
                "refresh_token"
            ]

            session[
                "login_time"
            ] = datetime.now().timestamp()

            st.session_state.auth_session = (
                session
            )

        decoded = auth.verify_id_token(
            session["id_token"]
        )

        return decoded["uid"]

    except Exception:

        st.session_state.pop(
            "auth_session",
            None,
        )

        st.session_state.pop(
            "student_user",
            None,
        )

        return None


# ============================================================
# USER PROFILE
# ============================================================

def get_user_profile(uid):

    snap = (
        db.collection("users")
        .document(uid)
        .get()
    )

    if snap.exists:
        return snap.to_dict()

    return None


def save_user_profile(
    uid,
    name,
    student_id,
    email,
):

    db.collection(
        "users"
    ).document(uid).set(
        {
            "name": name,
            "student_id": student_id,
            "email": email,
            "wallet_balance": 0,
            "created_at":
                firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )


def current_student():

    uid = get_logged_in_uid()

    if not uid:
        return None

    profile = get_user_profile(
        uid
    )

    if not profile:
        return None

    profile["uid"] = uid

    return profile


# ============================================================
# MENU
# ============================================================

def load_menu():

    docs = list(
        db.collection("menu")
        .stream()
    )

    if not docs:

        for item in DEFAULT_MENU:

            db.collection(
                "menu"
            ).document(
                item["name"]
            ).set(item)

        return DEFAULT_MENU

    menu = []

    for doc in docs:

        item = doc.to_dict()

        item["name"] = doc.id

        item.setdefault(
            "image",
            "",
        )

        menu.append(item)

    return sorted(
        menu,
        key=lambda x:
            x["name"].lower(),
    )


def effective_price(item):

    price = float(
        item.get(
            "price",
            0,
        )
    )

    discount = float(
        item.get(
            "discount",
            0,
        )
    )

    return max(
        0,
        round(
            price
            * (
                1
                - discount / 100
            ),
            2,
        ),
    )


def save_menu_item(
    name,
    price,
    discount,
    available,
    popular,
    image="",
):

    data = {
        "price": float(price),
        "discount": float(discount),
        "available": bool(available),
        "popular": bool(popular),
    }

    if image:
        data["image"] = image

    db.collection(
        "menu"
    ).document(
        name
    ).set(
        data,
        merge=True,
    )


def delete_menu_item(
    name,
):

    db.collection(
        "menu"
    ).document(
        name
    ).delete()


# ============================================================
# ORDER ID
# ============================================================

def generate_daily_order_id():

    today = date.today().isoformat()

    ref = (
        db.collection("counters")
        .document(today)
    )

    transaction = db.transaction()

    @transactional
    def increment_counter(
        transaction,
        ref,
    ):

        snap = ref.get(
            transaction=transaction
        )

        if snap.exists:

            current = int(
                snap.to_dict()
                .get(
                    "value",
                    0,
                )
            )

        else:

            current = 0

        new_value = (
            current + 1
        )

        transaction.set(
            ref,
            {
                "value": new_value
            },
            merge=True,
        )

        return new_value

    number = increment_counter(
        transaction,
        ref,
    )

    return f"{number:03d}"


# ============================================================
# ORDER FORMAT COMPATIBILITY
# ============================================================

def normalize_order_items(
    items,
):

    # OLD FORMAT:
    # {"Veg Roll": 1, "Tea": 1}

    if isinstance(
        items,
        dict,
    ):

        return [
            {
                "name": name,
                "quantity": int(
                    quantity
                ),
                "unit_price": 0,
                "line_total": 0,
            }

            for name, quantity
            in items.items()
        ]

    # NEW FORMAT:
    # [
    #   {"name": "Veg Roll",
    #    "quantity": 1}
    # ]

    if isinstance(
        items,
        list,
    ):

        return items

    return []


def order_items_text(
    order,
):

    items = normalize_order_items(
        order.get(
            "items",
            [],
        )
    )

    if not items:
        return "No items"

    return ", ".join(
        f"{x.get('name', 'Item')} "
        f"× {x.get('quantity', 0)}"
        for x in items
    )


# ============================================================
# ORDER DOCUMENT
# ============================================================

def find_order_document(
    order,
):

    order_id = str(
        order.get(
            "order_id"
        )
    )

    order_date = order.get(
        "date",
        date.today().isoformat(),
    )

    # New document format

    ref = (
        db.collection("orders")
        .document(
            f"{order_date}_{order_id}"
        )
    )

    if ref.get().exists:
        return ref

    # Old orders

    query = (
        db.collection("orders")
        .where(
            "order_id",
            "==",
            order_id,
        )
        .where(
            "date",
            "==",
            order_date,
        )
        .limit(1)
        .stream()
    )

    for doc in query:
        return doc.reference

    query = (
        db.collection("orders")
        .where(
            "order_id",
            "==",
            order_id,
        )
        .limit(1)
        .stream()
    )

    for doc in query:
        return doc.reference

    return None


def update_order_status(
    order,
    new_status,
):

    ref = find_order_document(
        order
    )

    if not ref:

        return (
            False,
            "Order document not found.",
        )

    ref.update(
        {
            "status": new_status,
            "updated_at":
                firestore.SERVER_TIMESTAMP,
        }
    )

    return True, None


def mark_counter_payment_received(
    order,
):

    ref = find_order_document(
        order
    )

    if not ref:

        return (
            False,
            "Order document not found.",
        )

    ref.update(
        {
            "payment_status":
                "Paid",
            "payment_received_at":
                firestore.SERVER_TIMESTAMP,
        }
    )

    return True, None


def get_today_orders():

    today = date.today().isoformat()

    docs = (
        db.collection("orders")
        .where(
            "date",
            "==",
            today,
        )
        .stream()
    )

    orders = [
        doc.to_dict()
        for doc in docs
    ]

    def sort_order(x):

        try:

            return int(
                str(
                    x.get(
                        "order_id",
                        "0",
                    )
                )
            )

        except Exception:

            return 0

    return sorted(
        orders,
        key=sort_order,
    )


def get_student_orders(
    uid,
):

    docs = (
        db.collection("orders")
        .where(
            "uid",
            "==",
            uid,
        )
        .stream()
    )

    orders = [
        doc.to_dict()
        for doc in docs
    ]

    def sort_order(x):

        try:

            return int(
                str(
                    x.get(
                        "order_id",
                        "0",
                    )
                )
            )

        except Exception:

            return 0

    return sorted(
        orders,
        key=lambda x: (
            x.get(
                "date",
                "",
            ),
            sort_order(x),
        ),
        reverse=True,
    )


# ============================================================
# WALLET / COUPON
# ============================================================

def credit_wallet(
    uid,
    amount,
    reason,
):

    amount = float(amount)

    if amount <= 0:

        return (
            False,
            "Amount must be greater than zero.",
        )

    transaction = db.transaction()

    user_ref = (
        db.collection("users")
        .document(uid)
    )

    transaction_ref = (
        db.collection(
            "wallet_transactions"
        ).document()
    )

    @transactional
    def credit(
        transaction,
        user_ref,
        transaction_ref,
    ):

        snap = user_ref.get(
            transaction=transaction
        )

        if snap.exists:

            current = float(
                snap.to_dict()
                .get(
                    "wallet_balance",
                    0,
                )
            )

        else:

            current = 0

        new_balance = round(
            current + amount,
            2,
        )

        transaction.set(
            user_ref,
            {
                "wallet_balance":
                    new_balance
            },
            merge=True,
        )

        transaction.set(
            transaction_ref,
            {
                "uid": uid,
                "type": "Credit",
                "amount": amount,
                "balance_after":
                    new_balance,
                "reason": reason,
                "created_at":
                    firestore.SERVER_TIMESTAMP,
                "date":
                    date.today().isoformat(),
            },
        )

        return new_balance

    new_balance = credit(
        transaction,
        user_ref,
        transaction_ref,
    )

    return True, new_balance


def debit_wallet_transaction(
    transaction,
    uid,
    user_ref,
    amount,
    order_id,
):

    snap = user_ref.get(
        transaction=transaction
    )

    if snap.exists:

        balance = float(
            snap.to_dict()
            .get(
                "wallet_balance",
                0,
            )
        )

    else:

        balance = 0

    if balance < amount:

        raise ValueError(
            "Insufficient wallet balance. "
            f"Available ₹{balance:.2f}."
        )

    new_balance = round(
        balance - amount,
        2,
    )

    transaction.update(
        user_ref,
        {
            "wallet_balance":
                new_balance
        },
    )

    transaction_ref = (
        db.collection(
            "wallet_transactions"
        ).document()
    )

    transaction.set(
        transaction_ref,
        {
            "uid": uid,
            "type": "Debit",
            "amount": amount,
            "balance_after":
                new_balance,
            "reason":
                f"Order #{order_id}",
            "order_id":
                order_id,
            "created_at":
                firestore.SERVER_TIMESTAMP,
            "date":
                date.today().isoformat(),
        },
    )

    return new_balance


# ============================================================
# CREATE ORDER
# ============================================================

def create_order(
    student,
    cart,
    order_type,
    break_time,
    payment_method,
):

    if not cart:

        return (
            False,
            "Your cart is empty.",
        )

    uid = student["uid"]

    today = date.today().isoformat()

    order_id = generate_daily_order_id()

    menu = {
        x["name"]: x
        for x in load_menu()
    }

    items = []

    total = 0

    for name, quantity in cart.items():

        if quantity <= 0:
            continue

        item = menu.get(name)

        if not item:

            return (
                False,
                f"{name} is no longer available.",
            )

        if not item.get(
            "available",
            True,
        ):

            return (
                False,
                f"{name} is currently unavailable.",
            )

        price = effective_price(
            item
        )

        line_total = round(
            price * quantity,
            2,
        )

        items.append(
            {
                "name": name,
                "quantity": int(
                    quantity
                ),
                "unit_price": price,
                "line_total":
                    line_total,
            }
        )

        total += line_total

    total = round(
        total,
        2,
    )

    order_ref = (
        db.collection("orders")
        .document(
            f"{today}_{order_id}"
        )
    )

    user_ref = (
        db.collection("users")
        .document(uid)
    )

    transaction = db.transaction()

    @transactional
    def create_transaction(
        transaction,
        order_ref,
        user_ref,
    ):

        user_snap = user_ref.get(
            transaction=transaction
        )

        if not user_snap.exists:

            raise ValueError(
                "Student profile not found."
            )

        if payment_method == "Wallet":

            debit_wallet_transaction(
                transaction,
                uid,
                user_ref,
                total,
                order_id,
            )

            payment_status = "Paid"

        else:

            payment_status = "Pending"

        order_data = {
            "order_id":
                order_id,
            "uid":
                uid,
            "student_name":
                student.get(
                    "name",
                    "",
                ),
            "student_id":
                student.get(
                    "student_id",
                    "",
                ),
            "email":
                student.get(
                    "email",
                    "",
                ),
            "items":
                items,
            "total":
                total,
            "order_type":
                order_type,
            "break_time":
                break_time,
            "payment_method":
                payment_method,
            "payment_status":
                payment_status,
            "status":
                "Confirmed",
            "date":
                today,
            "created_at":
                firestore.SERVER_TIMESTAMP,
        }

        transaction.set(
            order_ref,
            order_data,
        )

        return order_data

    try:

        result = create_transaction(
            transaction,
            order_ref,
            user_ref,
        )

        return True, result

    except Exception as e:

        return False, str(e)


# ============================================================
# CLEANUP
# ============================================================

def cleanup_old_records(
    days=14,
):

    cutoff = (
        date.today()
        - timedelta(
            days=days
        )
    )

    removed_orders = 0
    removed_feedback = 0

    # Orders

    for doc in (
        db.collection("orders")
        .stream()
    ):

        data = doc.to_dict()

        record_date = data.get(
            "date",
            "",
        )

        try:

            if (
                record_date
                and date.fromisoformat(
                    record_date
                )
                < cutoff
            ):

                doc.reference.delete()

                removed_orders += 1

        except Exception:

            pass

    # Feedback

    for doc in (
        db.collection("feedback")
        .stream()
    ):

        data = doc.to_dict()

        record_date = data.get(
            "date",
            "",
        )

        try:

            if (
                record_date
                and date.fromisoformat(
                    record_date
                )
                < cutoff
            ):

                doc.reference.delete()

                removed_feedback += 1

        except Exception:

            pass

    return (
        removed_orders,
        removed_feedback,
    )


# ============================================================
# SESSION
# ============================================================

def init_state():

    defaults = {
        "page": "Home",
        "cart": {},
        "last_order": None,
        "cafeteria_logged_in":
            False,
    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[
                key
            ] = value


def go_to(page):

    st.session_state.page = page

    st.rerun()


def logout_student():

    st.session_state.pop(
        "auth_session",
        None,
    )

    st.session_state.pop(
        "student_user",
        None,
    )

    st.session_state.cart = {}

    st.session_state.page = "Home"

    st.rerun()


init_state()


# ============================================================
# NAVIGATION
# ============================================================

def render_nav():

    student = current_student()

    cafeteria = st.session_state.get(
        "cafeteria_logged_in",
        False,
    )

    st.markdown(
        "### 🍽️ Campus Cafeteria"
    )

    if student:

        cols = st.columns(6)

        nav = [
            (
                "🏠 Home",
                "Home",
            ),
            (
                "🍔 Order Food",
                "Order Food",
            ),
            (
                "📦 My Orders",
                "My Orders",
            ),
            (
                "💰 Wallet",
                "Wallet",
            ),
            (
                "💬 Feedback",
                "Feedback",
            ),
            (
                "🚪 Logout",
                "Logout",
            ),
        ]

        for col, (
            label,
            page,
        ) in zip(
            cols,
            nav,
        ):

            with col:

                if st.button(
                    label,
                    use_container_width=True,
                    key=(
                        f"student_nav_{page}"
                    ),
                ):

                    if page == "Logout":

                        logout_student()

                    else:

                        go_to(page)

    elif cafeteria:

        cols = st.columns(6)

        nav = [
            (
                "📊 Dashboard",
                "Cafeteria Dashboard",
            ),
            (
                "🍔 Menu",
                "Menu Management",
            ),
            (
                "💰 Wallet",
                "Wallet Management",
            ),
            (
                "💬 Feedback",
                "Feedback Management",
            ),
            (
                "🧹 Cleanup",
                "Cleanup",
            ),
            (
                "🚪 Logout",
                "Cafeteria Logout",
            ),
        ]

        for col, (
            label,
            page,
        ) in zip(
            cols,
            nav,
        ):

            with col:

                if st.button(
                    label,
                    use_container_width=True,
                    key=(
                        f"caf_nav_{page}"
                    ),
                ):

                    if page == (
                        "Cafeteria Logout"
                    ):

                        st.session_state[
                            "cafeteria_logged_in"
                        ] = False

                        go_to("Home")

                    else:

                        go_to(page)

    else:

        cols = st.columns(3)

        nav = [
            (
                "🏠 Home",
                "Home",
            ),
            (
                "🎓 Student Login",
                "Student Login",
            ),
            (
                "🧑‍🍳 Cafeteria Portal",
                "Cafeteria Portal",
            ),
        ]

        for col, (
            label,
            page,
        ) in zip(
            cols,
            nav,
        ):

            with col:

                if st.button(
                    label,
                    use_container_width=True,
                    key=(
                        f"guest_nav_{page}"
                    ),
                ):

                    go_to(page)

    st.divider()


# ============================================================
# HOME
# ============================================================

def home_page():

    student = current_student()

    st.markdown(
        """
        <div class="hero">

            <h1>
                Pre-order. Skip the queue.
                Enjoy your break. 🍽️
            </h1>

            <p>
                Order from Campus Cafeteria
                before the rush and collect
                your food quickly.
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    if student:

        balance = float(
            student.get(
                "wallet_balance",
                0,
            )
        )

        st.markdown(
            f"""
            <div class="success-box">

                <b>
                    Welcome back,
                    {student.get(
                        "name",
                        "Student"
                    )}!
                </b>

                <br>

                Wallet / Coupon Balance:
                <b>₹{balance:.2f}</b>

            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            if st.button(
                "🍔 Order Food",
                type="primary",
                use_container_width=True,
            ):

                go_to(
                    "Order Food"
                )

        with c2:

            if st.button(
                "📦 Track Orders",
                use_container_width=True,
            ):

                go_to(
                    "My Orders"
                )

        with c3:

            if st.button(
                "💰 Wallet / Coupon",
                use_container_width=True,
            ):

                go_to(
                    "Wallet"
                )

    else:

        c1, c2, c3 = st.columns(3)

        cards = [
            (
                "🍔 Order Food",
                "Pre-order your food before the rush.",
            ),
            (
                "⏱️ Save Break Time",
                "Collect quickly instead of standing in the queue.",
            ),
            (
                "💳 Easy Payment",
                "Use your prepaid coupon or pay at counter.",
            ),
        ]

        for col, (
            title,
            text,
        ) in zip(
            [c1, c2, c3],
            cards,
        ):

            with col:

                st.markdown(
                    f"""
                    <div class="card">
                        <h3>{title}</h3>
                        <p>{text}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button(
                    "Get Started",
                    use_container_width=True,
                    key=(
                        f"home_{title}"
                    ),
                ):

                    go_to(
                        "Student Login"
                    )

    st.markdown(
        "### How it works"
    )

    cols = st.columns(4)

    steps = [
        (
            "1",
            "Login",
            "Create your student account.",
        ),
        (
            "2",
            "Order",
            "Choose Break or Regular Order.",
        ),
        (
            "3",
            "Pay",
            "Use wallet/coupon or pay at counter.",
        ),
        (
            "4",
            "Collect",
            "Show your Order ID at the desk.",
        ),
    ]

    for col, (
        number,
        title,
        text,
    ) in zip(
        cols,
        steps,
    ):

        with col:

            st.markdown(
                f"""
                <div class="card">

                    <h3>
                        {number}. {title}
                    </h3>

                    <p>
                        {text}
                    </p>

                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        "### Order modes"
    )

    c1, c2 = st.columns(2)

    with c1:

        st.markdown(
            """
            <div class="card">

                <h3>
                    🕐 Break Order
                </h3>

                <p>
                    Pre-order for a selected
                    break period.
                    Status:
                    Confirmed → Collected.
                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:

        st.markdown(
            """
            <div class="card">

                <h3>
                    🏠 Regular Order
                </h3>

                <p>
                    Room / Hostel pre-order,
                    available anytime including
                    during breaks.
                    Estimated preparation:
                    10–15 minutes.
                </p>

            </div>
            """,
            unsafe_allow_html=True,
        )

    st.info(
        f"Need help? Contact "
        f"{DESK_NAME} at "
        f"{DESK_PHONE} or "
        f"{DESK_EMAIL}."
    )


# ============================================================
# STUDENT LOGIN
# ============================================================

def student_login_page():

    st.markdown(
        "## 🎓 Student Login"
    )

    if current_student():

        st.success(
            "You are already logged in."
        )

        if st.button(
            "Go to Home"
        ):

            go_to(
                "Home"
            )

        return

    login_tab, signup_tab, reset_tab = st.tabs(
        [
            "Login",
            "Create Account",
            "Forgot Password",
        ]
    )

    # LOGIN

    with login_tab:

        email = st.text_input(
            "College / Student Email",
            key="login_email",
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password",
        )

        if st.button(
            "Login",
            type="primary",
            use_container_width=True,
        ):

            if not email or not password:

                st.error(
                    "Please enter both email and password."
                )

            else:

                data, error = login_student(
                    email.strip(),
                    password,
                )

                if error:

                    st.error(
                        f"Login failed: {error}"
                    )

                else:

                    st.session_state[
                        "auth_session"
                    ] = {
                        "id_token":
                            data["idToken"],
                        "refresh_token":
                            data["refreshToken"],
                        "login_time":
                            datetime.now().timestamp(),
                    }

                    profile = get_user_profile(
                        data["localId"]
                    )

                    if not profile:

                        st.warning(
                            "Authentication worked, "
                            "but the student profile "
                            "was not found."
                        )

                    else:

                        st.session_state[
                            "student_user"
                        ] = profile

                        st.session_state[
                            "page"
                        ] = "Home"

                        st.rerun()

    # SIGNUP

    with signup_tab:

        name = st.text_input(
            "Full Name",
            key="signup_name",
        )

        student_id = st.text_input(
            "Student ID / Roll Number",
            key="signup_student_id",
        )

        email = st.text_input(
            "Email",
            key="signup_email",
        )

        password = st.text_input(
            "Create Password",
            type="password",
            key="signup_password",
        )

        confirm = st.text_input(
            "Confirm Password",
            type="password",
            key="signup_confirm",
        )

        if st.button(
            "Create Account",
            type="primary",
            use_container_width=True,
        ):

            if not all(
                [
                    name,
                    student_id,
                    email,
                    password,
                    confirm,
                ]
            ):

                st.error(
                    "Please fill all fields."
                )

            elif password != confirm:

                st.error(
                    "Passwords do not match."
                )

            elif len(password) < 6:

                st.error(
                    "Password must be at least 6 characters."
                )

            else:

                data, error = signup_student(
                    email.strip(),
                    password,
                )

                if error:

                    st.error(
                        f"Could not create account: "
                        f"{error}"
                    )

                else:

                    uid = data[
                        "localId"
                    ]

                    save_user_profile(
                        uid,
                        name.strip(),
                        student_id.strip(),
                        email.strip(),
                    )

                    st.session_state[
                        "auth_session"
                    ] = {
                        "id_token":
                            data["idToken"],
                        "refresh_token":
                            data["refreshToken"],
                        "login_time":
                            datetime.now().timestamp(),
                    }

                    st.session_state[
                        "page"
                    ] = "Home"

                    st.success(
                        "Account created successfully!"
                    )

                    st.rerun()

    # PASSWORD RESET

    with reset_tab:

        email = st.text_input(
            "Account Email",
            key="reset_email",
        )

        if st.button(
            "Send Reset Email",
            use_container_width=True,
        ):

            if not email:

                st.error(
                    "Enter your email first."
                )

            else:

                _, error = send_password_reset(
                    email.strip()
                )

                if error:

                    st.error(
                        f"Could not send reset email: "
                        f"{error}"
                    )

                else:

                    st.success(
                        "Password reset email sent."
                    )


# ============================================================
# ORDER FOOD
# ============================================================

def order_food_page():

    student = current_student()

    if not student:

        st.warning(
            "Please log in first."
        )

        if st.button(
            "Go to Student Login"
        ):

            go_to(
                "Student Login"
            )

        return

    st.markdown(
        "## 🍔 Order Food"
    )

    menu = load_menu()

    available = [
        x
        for x in menu
        if x.get(
            "available",
            True,
        )
    ]

    if not available:

        st.warning(
            "No food items are currently available."
        )

        return

    # POPULAR

    popular = [
        x
        for x in available
        if x.get(
            "popular",
            False,
        )
    ]

    if popular:

        st.markdown(
            "### ⭐ Popular Picks"
        )

        cols = st.columns(
            min(
                3,
                len(popular),
            )
        )

        for col, item in zip(
            cols,
            popular[:3],
        ):

            with col:

                if item.get(
                    "image"
                ):

                    st.markdown(
                        image_html(
                            item[
                                "image"
                            ],
                            135,
                        ),
                        unsafe_allow_html=True,
                    )

                st.markdown(
                    f"""
                    <div class="card">

                        <h3>
                            {item['name']}
                        </h3>

                        <p>
                            ₹{effective_price(item):.0f}
                        </p>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # MENU

    st.markdown(
        "### Menu"
    )

    cols = st.columns(2)

    for index, item in enumerate(
        available
    ):

        with cols[
            index % 2
        ]:

            if item.get(
                "image"
            ):

                st.markdown(
                    image_html(
                        item[
                            "image"
                        ],
                        150,
                    ),
                    unsafe_allow_html=True,
                )

            price = effective_price(
                item
            )

            discount = float(
                item.get(
                    "discount",
                    0,
                )
            )

            if discount > 0:

                st.markdown(
                    f"**{item['name']}** — "
                    f"~~₹{item['price']}~~ "
                    f"**₹{price:.0f}**"
                )

            else:

                st.markdown(
                    f"**{item['name']}** — "
                    f"**₹{price:.0f}**"
                )

            current = int(
                st.session_state[
                    "cart"
                ].get(
                    item["name"],
                    0,
                )
            )

            qty = st.number_input(
                "Quantity",
                min_value=0,
                max_value=20,
                value=current,
                step=1,
                key=(
                    f"food_qty_"
                    f"{item['name']}"
                ),
            )

            if qty:

                st.session_state[
                    "cart"
                ][
                    item["name"]
                ] = int(qty)

            else:

                st.session_state[
                    "cart"
                ].pop(
                    item["name"],
                    None,
                )

    st.divider()

    cart = st.session_state[
        "cart"
    ]

    if not cart:

        st.info(
            "Your cart is empty."
        )

        return

    menu_map = {
        x["name"]: x
        for x in menu
    }

    total = 0

    st.markdown(
        "### 🛒 Your Cart"
    )

    for name, qty in cart.items():

        item = menu_map.get(
            name
        )

        if item:

            line = (
                effective_price(
                    item
                )
                * qty
            )

            total += line

            st.write(
                f"**{name}** × {qty} "
                f"= ₹{line:.0f}"
            )

    total = round(
        total,
        2,
    )

    st.markdown(
        f"### Total: ₹{total:.0f}"
    )

    # ORDER TYPE

    st.markdown(
        "### Choose Order Type"
    )

    order_type = st.radio(
        "Order Type",
        [
            "Break Order",
            "Regular Order",
        ],
        horizontal=True,
        key="order_type_radio",
    )

    break_time = None

    if order_type == "Break Order":

        st.success(
            "Choose the break period "
            "when you will collect "
            "your order."
        )

        break_time = st.selectbox(
            "Break Period",
            BREAK_OPTIONS,
            key="break_period",
        )

    else:

        st.info(
            "Regular Order: Room / Hostel "
            "pre-order only. Available anytime, "
            "including during breaks. "
            "Estimated preparation time: "
            "10–15 minutes."
        )

    # PAYMENT

    st.markdown(
        "### Payment"
    )

    wallet_balance = float(
        student.get(
            "wallet_balance",
            0,
        )
    )

    payment_method = st.radio(
        "Payment Method",
        [
            "Prepaid Wallet / Coupon",
            "Pay at Counter",
        ],
        horizontal=True,
        key="payment_method_radio",
    )

    if (
        payment_method
        == "Prepaid Wallet / Coupon"
    ):

        st.metric(
            "Available Wallet / Coupon Balance",
            f"₹{wallet_balance:.2f}",
        )

        if wallet_balance < total:

            st.warning(
                f"Insufficient balance. "
                f"You need "
                f"₹{total - wallet_balance:.2f} more."
            )

            st.caption(
                "Ask the cafeteria desk "
                "to add money to your "
                "prepaid wallet."
            )

    else:

        st.info(
            "You will pay at the "
            "cafeteria desk when "
            "collecting your order."
        )

    # PLACE ORDER

    if st.button(
        "🛒 Place Order",
        type="primary",
        use_container_width=True,
    ):

        actual_payment = (
            "Wallet"
            if payment_method
            == "Prepaid Wallet / Coupon"
            else "Pay at Counter"
        )

        if (
            actual_payment == "Wallet"
            and wallet_balance < total
        ):

            st.error(
                "Insufficient wallet/coupon balance."
            )

            return

        ok, result = create_order(
            student,
            cart,
            order_type,
            break_time,
            actual_payment,
        )

        if not ok:

            st.error(
                f"Could not place order: "
                f"{result}"
            )

            return

        st.session_state[
            "last_order"
        ] = result

        st.session_state[
            "cart"
        ] = {}

        st.session_state[
            "page"
        ] = "Order Confirmation"

        st.rerun()


# ============================================================
# ORDER CONFIRMATION
# ============================================================

def confirmation_page():

    order = st.session_state.get(
        "last_order"
    )

    if not order:

        st.info(
            "No recent order."
        )

        return

    st.markdown(
        "## ✅ Order Confirmed"
    )

    st.markdown(
        f"""
        <div class="success-box">

            <div class="small-muted">
                Your Order ID
            </div>

            <div class="order-id">
                #{order['order_id']}
            </div>

            <p style="text-align:center">
                Show this Order ID at the
                cafeteria desk when collecting.
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write(
        f"**Order Type:** "
        f"{order.get('order_type', '-')}"
    )

    if order.get(
        "break_time"
    ):

        st.write(
            f"**Break Period:** "
            f"{order['break_time']}"
        )

    st.write(
        f"**Payment:** "
        f"{order.get('payment_method', '-')}"
    )

    st.write(
        f"**Payment Status:** "
        f"{order.get('payment_status', '-')}"
    )

    st.write(
        f"**Status:** "
        f"{order.get('status', '-')}"
    )

    st.write(
        f"**Total:** "
        f"₹{order.get('total', 0):.0f}"
    )

    st.markdown(
        "### Items"
    )

    for item in normalize_order_items(
        order.get(
            "items",
            [],
        )
    ):

        st.write(
            f"{item.get('name', 'Item')} × "
            f"{item.get('quantity', 0)} — "
            f"₹{float(item.get('line_total', 0)):.0f}"
        )

    if (
        order.get(
            "payment_method"
        )
        == "Pay at Counter"
    ):

        st.warning(
            "Please pay at the cafeteria "
            "desk before collection."
        )

    c1, c2 = st.columns(2)

    with c1:

        if st.button(
            "📦 Track Order",
            use_container_width=True,
        ):

            go_to(
                "My Orders"
            )

    with c2:

        if st.button(
            "🍔 Order More",
            use_container_width=True,
        ):

            go_to(
                "Order Food"
            )


# ============================================================
# MY ORDERS
# ============================================================

def my_orders_page():

    student = current_student()

    if not student:

        st.warning(
            "Please log in first."
        )

        return

    st.markdown(
        "## 📦 My Orders"
    )

    orders = get_student_orders(
        student["uid"]
    )

    if not orders:

        st.info(
            "You have no orders yet."
        )

        return

    for order in orders[:30]:

        status = order.get(
            "status",
            "Confirmed",
        )

        payment = order.get(
            "payment_status",
            "-",
        )

        with st.container(
            border=True
        ):

            c1, c2, c3, c4 = st.columns(
                [
                    1,
                    2,
                    1.2,
                    1.2,
                ]
            )

            with c1:

                st.markdown(
                    f"### #{order.get('order_id')}"
                )

            with c2:

                st.write(
                    order_items_text(
                        order
                    )
                )

                st.caption(
                    f"{order.get('order_type', '')}"
                    + (
                        f" • {order.get('break_time')}"
                        if order.get(
                            "break_time"
                        )
                        else ""
                    )
                )

            with c3:

                st.write(
                    f"**Status**\n\n"
                    f"{status}"
                )

            with c4:

                st.write(
                    f"**₹{order.get('total', 0):.0f}**"
                )

                st.caption(
                    f"Payment: {payment}"
                )


# ============================================================
# STUDENT WALLET
# ============================================================

def wallet_page():

    student = current_student()

    if not student:

        st.warning(
            "Please log in first."
        )

        return

    student = get_user_profile(
        student["uid"]
    )

    balance = float(
        student.get(
            "wallet_balance",
            0,
        )
    )

    st.markdown(
        "## 💰 Prepaid Wallet / Coupon"
    )

    st.metric(
        "Available Balance",
        f"₹{balance:.2f}",
    )

    st.info(
        "Give money to the cafeteria "
        "desk and ask the desk person "
        "to credit your prepaid wallet."
    )

    st.markdown(
        "### How it works"
    )

    st.write(
        "1. Give money to the cafeteria desk."
    )

    st.write(
        "2. Tell the desk your Student ID."
    )

    st.write(
        "3. The desk credits your wallet."
    )

    st.write(
        "4. Select Prepaid Wallet / Coupon when ordering."
    )

    st.write(
        "5. The order amount is deducted automatically."
    )


# ============================================================
# STUDENT FEEDBACK
# ============================================================

def feedback_page():

    student = current_student()

    if not student:

        st.warning(
            "Please log in first."
        )

        return

    st.markdown(
        "## 💬 Feedback"
    )

    rating = st.slider(
        "Rating",
        1,
        5,
        5,
    )

    category = st.selectbox(
        "Category",
        [
            "Food Quality",
            "Taste",
            "Service",
            "Waiting Time",
            "Other",
        ],
    )

    message = st.text_area(
        "Your feedback"
    )

    photo = st.file_uploader(
        "Add a photo (optional)",
        type=[
            "jpg",
            "jpeg",
            "png",
        ],
        key="feedback_photo",
    )

    if st.button(
        "Submit Feedback",
        type="primary",
    ):

        if not message.strip():

            st.error(
                "Please enter your feedback."
            )

            return

        photo_data = image_to_data_url(
            photo,
            max_size=700,
            quality=70,
        )

        db.collection(
            "feedback"
        ).add(
            {
                "uid":
                    student["uid"],
                "student_name":
                    student.get(
                        "name",
                        "",
                    ),
                "student_id":
                    student.get(
                        "student_id",
                        "",
                    ),
                "rating":
                    rating,
                "category":
                    category,
                "message":
                    message.strip(),
                "photo":
                    photo_data,
                "created_at":
                    firestore.SERVER_TIMESTAMP,
                "date":
                    date.today().isoformat(),
            }
        )

        st.success(
            "Thank you for your feedback!"
        )


# ============================================================
# CAFETERIA LOGIN
# ============================================================

def cafeteria_login_page():

    st.markdown(
        "## 🧑‍🍳 Cafeteria Portal"
    )

    st.markdown(
        """
        <div class="login-box">

            <h3>
                Cafeteria Desk Login
            </h3>

            <p class="small-muted">
                Staff-only portal for managing
                orders, menu and wallet credits.
            </p>

        </div>
        """,
        unsafe_allow_html=True,
    )

    login_id = st.text_input(
        "Login ID"
    )

    password = st.text_input(
        "Password",
        type="password",
    )

    if st.button(
        "Login to Cafeteria Portal",
        type="primary",
        use_container_width=True,
    ):

        if (
            login_id.strip()
            == CAFETERIA_LOGIN_ID
            and password
            == CAFETERIA_PASSWORD
        ):

            st.session_state[
                "cafeteria_logged_in"
            ] = True

            st.session_state[
                "page"
            ] = "Cafeteria Dashboard"

            st.rerun()

        else:

            st.error(
                "Incorrect Login ID or Password."
            )


# ============================================================
# CAFETERIA DASHBOARD
# ============================================================

def cafeteria_dashboard_page():

    if not st.session_state.get(
        "cafeteria_logged_in"
    ):

        go_to(
            "Cafeteria Portal"
        )

        return

    st.markdown(
        "## 📊 Cafeteria Dashboard"
    )

    st.info(
        f"Desk: {DESK_NAME}  •  "
        f"Phone: {DESK_PHONE}  •  "
        f"Email: {DESK_EMAIL}"
    )

    orders = get_today_orders()

    total = len(
        orders
    )

    confirmed = sum(
        1
        for x in orders
        if x.get(
            "status"
        )
        == "Confirmed"
    )

    preparing = sum(
        1
        for x in orders
        if x.get(
            "status"
        )
        == "Preparing"
    )

    ready = sum(
        1
        for x in orders
        if x.get(
            "status"
        )
        == "Ready"
    )

    collected = sum(
        1
        for x in orders
        if x.get(
            "status"
        )
        == "Collected"
    )

    cols = st.columns(5)

    cols[0].metric(
        "📦 Total",
        total,
    )

    cols[1].metric(
        "🔵 Confirmed",
        confirmed,
    )

    cols[2].metric(
        "🟠 Preparing",
        preparing,
    )

    cols[3].metric(
        "🟢 Ready",
        ready,
    )

    cols[4].metric(
        "✅ Collected",
        collected,
    )

    st.markdown(
        "### Today's Orders"
    )

    if not orders:

        st.info(
            "No orders today."
        )

        return

    search = st.text_input(
        "Search Order ID / Student / Student ID",
        key="dashboard_search",
    )

    status_filter = st.selectbox(
        "Status Filter",
        [
            "All",
            "Confirmed",
            "Preparing",
            "Ready",
            "Collected",
        ],
        key="dashboard_status_filter",
    )

    for order in orders:

        searchable = (
            f"{order.get('order_id', '')} "
            f"{order.get('student_name', '')} "
            f"{order.get('student_id', '')}"
        ).lower()

        if (
            search.lower()
            not in searchable
        ):

            continue

        if (
            status_filter
            != "All"
            and order.get(
                "status"
            )
            != status_filter
        ):

            continue

        order_type = order.get(
            "order_type",
            "Regular Order",
        )

        status = order.get(
            "status",
            "Confirmed",
        )

        payment_method = order.get(
            "payment_method",
            "-",
        )

        payment_status = order.get(
            "payment_status",
            "-",
        )

        with st.container(
            border=True
        ):

            top = st.columns(
                [
                    1,
                    2,
                    2,
                    1,
                ]
            )

            with top[0]:

                st.markdown(
                    f"### #{order.get('order_id')}"
                )

            with top[1]:

                st.write(
                    f"**{order.get('student_name', '-') }**"
                )

                st.caption(
                    f"Student ID: "
                    f"{order.get('student_id', '-')}"
                )

            with top[2]:

                st.write(
                    order_items_text(
                        order
                    )
                )

                st.caption(
                    f"{order_type}"
                    + (
                        f" • "
                        f"{order.get('break_time')}"
                        if order.get(
                            "break_time"
                        )
                        else ""
                    )
                )

            with top[3]:

                st.metric(
                    "Amount",
                    f"₹{order.get('total', 0):.0f}",
                )

            a, b, c = st.columns(
                [
                    2,
                    2,
                    3,
                ]
            )

            with a:

                st.write(
                    f"**Status:** {status}"
                )

            with b:

                st.write(
                    f"**Payment:** "
                    f"{payment_status}"
                )

            with c:

                st.write(
                    f"**Method:** "
                    f"{payment_method}"
                )

            actions = st.columns(3)

            # --------------------------------------------
            # PAYMENT
            # --------------------------------------------

            if (
                payment_method
                == "Pay at Counter"
                and payment_status
                != "Paid"
            ):

                with actions[0]:

                    if st.button(
                        "💵 Payment Received",
                        key=(
                            f"pay_"
                            f"{order.get('order_id')}"
                        ),
                        use_container_width=True,
                    ):

                        ok, error = (
                            mark_counter_payment_received(
                                order
                            )
                        )

                        if ok:

                            st.success(
                                "Payment received."
                            )

                            st.rerun()

                        else:

                            st.error(
                                error
                            )

            # --------------------------------------------
            # REGULAR ORDER
            # --------------------------------------------

            if (
                order_type
                == "Regular Order"
            ):

                if status == "Confirmed":

                    with actions[1]:

                        if st.button(
                            "▶ Start Preparing",
                            key=(
                                f"prep_"
                                f"{order.get('order_id')}"
                            ),
                            use_container_width=True,
                        ):

                            ok, error = (
                                update_order_status(
                                    order,
                                    "Preparing",
                                )
                            )

                            if ok:

                                st.rerun()

                            else:

                                st.error(
                                    error
                                )

                elif status == "Preparing":

                    with actions[1]:

                        if st.button(
                            "✓ Mark Ready",
                            key=(
                                f"ready_"
                                f"{order.get('order_id')}"
                            ),
                            use_container_width=True,
                        ):

                            ok, error = (
                                update_order_status(
                                    order,
                                    "Ready",
                                )
                            )

                            if ok:

                                st.rerun()

                            else:

                                st.error(
                                    error
                                )

                elif status == "Ready":

                    with actions[1]:

                        if (
                            payment_method
                            == "Pay at Counter"
                            and payment_status
                            != "Paid"
                        ):

                            st.warning(
                                "Collect payment first."
                            )

                        else:

                            if st.button(
                                "📦 Mark Collected",
                                key=(
                                    f"collect_"
                                    f"{order.get('order_id')}"
                                ),
                                use_container_width=True,
                            ):

                                ok, error = (
                                    update_order_status(
                                        order,
                                        "Collected",
                                    )
                                )

                                if ok:

                                    st.rerun()

                                else:

                                    st.error(
                                        error
                                    )

            # --------------------------------------------
            # BREAK ORDER
            # --------------------------------------------

            else:

                if status == "Confirmed":

                    with actions[2]:

                        if (
                            payment_method
                            == "Pay at Counter"
                            and payment_status
                            != "Paid"
                        ):

                            st.warning(
                                "Collect payment first."
                            )

                        else:

                            if st.button(
                                "📦 Mark Collected",
                                key=(
                                    f"break_collect_"
                                    f"{order.get('order_id')}"
                                ),
                                use_container_width=True,
                            ):

                                ok, error = (
                                    update_order_status(
                                        order,
                                        "Collected",
                                    )
                                )

                                if ok:

                                    st.rerun()

                                else:

                                    st.error(
                                        error
                                    )


# ============================================================
# CAFETERIA WALLET MANAGEMENT
# ============================================================

def wallet_management_page():

    if not st.session_state.get(
        "cafeteria_logged_in"
    ):

        go_to(
            "Cafeteria Portal"
        )

        return

    st.markdown(
        "## 💰 Wallet / Coupon Management"
    )

    st.info(
        "When a student gives cash to the "
        "cafeteria, enter their Student ID "
        "and credit the same amount."
    )

    student_id = st.text_input(
        "Student ID / Roll Number",
        key="wallet_student_id",
    )

    amount = st.number_input(
        "Amount to Credit",
        min_value=1.0,
        max_value=50000.0,
        value=100.0,
        step=50.0,
        key="wallet_credit_amount",
    )

    reason = st.text_input(
        "Reason",
        value=(
            "Prepaid cafeteria "
            "coupon / wallet top-up"
        ),
        key="wallet_credit_reason",
    )

    if st.button(
        "💰 Credit Wallet",
        type="primary",
        use_container_width=True,
    ):

        if not student_id.strip():

            st.error(
                "Enter the Student ID."
            )

            return

        query = (
            db.collection("users")
            .where(
                "student_id",
                "==",
                student_id.strip(),
            )
            .limit(1)
            .stream()
        )

        found = None

        for doc in query:

            found = doc

            break

        if not found:

            st.error(
                "Student account not found."
            )

            return

        uid = found.id

        ok, result = credit_wallet(
            uid,
            amount,
            reason,
        )

        if ok:

            data = get_user_profile(
                uid
            )

            st.success(
                f"₹{amount:.2f} credited "
                f"successfully. "
                f"New balance for "
                f"{data.get('name', student_id)}: "
                f"₹{float(data.get('wallet_balance', 0)):.2f}"
            )

        else:

            st.error(
                str(result)
            )


# ============================================================
# MENU MANAGEMENT
# ============================================================

def menu_management_page():

    if not st.session_state.get(
        "cafeteria_logged_in"
    ):

        go_to(
            "Cafeteria Portal"
        )

        return

    st.markdown(
        "## 🍔 Menu Management"
    )

    st.markdown(
        "### Add / Update Food Item"
    )

    name = st.text_input(
        "Food Name"
    )

    price = st.number_input(
        "Price",
        min_value=0.0,
        step=5.0,
    )

    discount = st.number_input(
        "Discount (%)",
        min_value=0.0,
        max_value=100.0,
        value=0.0,
        step=1.0,
    )

    available = st.checkbox(
        "Available",
        value=True,
    )

    popular = st.checkbox(
        "Popular Pick",
        value=False,
    )

    image_file = st.file_uploader(
        "Food Photo (optional)",
        type=[
            "jpg",
            "jpeg",
            "png",
        ],
        key="menu_image_upload",
    )

    if st.button(
        "💾 Save Food Item",
        type="primary",
    ):

        if not name.strip():

            st.error(
                "Enter a food name."
            )

        elif price <= 0:

            st.error(
                "Price must be greater than zero."
            )

        else:

            image = image_to_data_url(
                image_file,
                max_size=700,
                quality=72,
            )

            save_menu_item(
                name.strip(),
                price,
                discount,
                available,
                popular,
                image,
            )

            st.success(
                "Food item saved."
            )

            st.rerun()

    st.markdown(
        "### Current Menu"
    )

    menu = load_menu()

    for item in menu:

        with st.container(
            border=True
        ):

            c1, c2, c3, c4 = st.columns(
                [
                    3,
                    1,
                    1,
                    1,
                ]
            )

            with c1:

                if item.get(
                    "image"
                ):

                    st.image(
                        item[
                            "image"
                        ],
                        width=130,
                    )

                st.write(
                    f"**{item['name']}** — "
                    f"₹{effective_price(item):.0f}"
                )

                if float(
                    item.get(
                        "discount",
                        0,
                    )
                ) > 0:

                    st.caption(
                        f"Discount: "
                        f"{item.get('discount')}%"
                    )

            with c2:

                st.write(
                    "🟢 Available"
                    if item.get(
                        "available",
                        True,
                    )
                    else
                    "🔴 Unavailable"
                )

            with c3:

                st.write(
                    "⭐ Popular"
                    if item.get(
                        "popular",
                        False,
                    )
                    else
                    "Not Popular"
                )

            with c4:

                if st.button(
                    "Delete",
                    key=(
                        f"delete_menu_"
                        f"{item['name']}"
                    ),
                ):

                    delete_menu_item(
                        item["name"]
                    )

                    st.rerun()


# ============================================================
# FEEDBACK MANAGEMENT
# ============================================================

def feedback_management_page():

    if not st.session_state.get(
        "cafeteria_logged_in"
    ):

        go_to(
            "Cafeteria Portal"
        )

        return

    st.markdown(
        "## 💬 Feedback Management"
    )

    feedback = [
        doc.to_dict()
        for doc in (
            db.collection(
                "feedback"
            ).stream()
        )
    ]

    if not feedback:

        st.info(
            "No feedback yet."
        )

        return

    for item in reversed(
        feedback[-50:]
    ):

        with st.container(
            border=True
        ):

            st.write(
                f"**{item.get('student_name', '-')}** "
                f"— ⭐ "
                f"{item.get('rating', '-')}/5"
            )

            st.caption(
                item.get(
                    "category",
                    "",
                )
            )

            st.write(
                item.get(
                    "message",
                    "",
                )
            )

            if item.get(
                "photo"
            ):

                st.image(
                    item["photo"],
                    width=250,
                )


# ============================================================
# CLEANUP
# ============================================================

def cleanup_page():

    if not st.session_state.get(
        "cafeteria_logged_in"
    ):

        go_to(
            "Cafeteria Portal"
        )

        return

    st.markdown(
        "## 🧹 Data Cleanup"
    )

    st.info(
        "This removes orders and feedback "
        "older than 14 days."
    )

    if st.button(
        "Run 14-Day Cleanup",
        type="primary",
    ):

        orders_removed, feedback_removed = (
            cleanup_old_records(14)
        )

        st.success(
            f"Removed "
            f"{orders_removed} old orders "
            f"and "
            f"{feedback_removed} old feedback records."
        )


# ============================================================
# MAIN ROUTER
# ============================================================

if not firebase_connected:

    st.error(
        "🔴 Firebase connection failed."
    )

    st.code(
        firebase_error
    )

    st.stop()


render_nav()

page = st.session_state.get(
    "page",
    "Home",
)


if page == "Home":

    home_page()


elif page == "Student Login":

    student_login_page()


elif page == "Order Food":

    order_food_page()


elif page == "Order Confirmation":

    confirmation_page()


elif page == "My Orders":

    my_orders_page()


elif page == "Wallet":

    wallet_page()


elif page == "Feedback":

    feedback_page()


elif page == "Cafeteria Portal":

    cafeteria_login_page()


elif page == "Cafeteria Dashboard":

    cafeteria_dashboard_page()


elif page == "Wallet Management":

    wallet_management_page()


elif page == "Menu Management":

    menu_management_page()


elif page == "Feedback Management":

    feedback_management_page()


elif page == "Cleanup":

    cleanup_page()


else:

    home_page()
