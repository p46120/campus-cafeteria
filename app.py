import json
import base64
from io import BytesIO
from datetime import date, datetime, timedelta

import requests
import streamlit as st
from PIL import Image

import firebase_admin
from firebase_admin import auth, credentials, firestore
from google.cloud.firestore_v1 import transactional


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="Campus Cafeteria",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CAFETERIA_NAME = "Campus Cafeteria"

CAFETERIA_LOGIN_ID = "cafeteria"
CAFETERIA_PASSWORD = "Campus@123"

DESK_NAME = "Rahul"
DESK_PHONE = "9065334992"
DESK_EMAIL = "rahulraj1244raj@gmail.com"

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


DEFAULT_MENU = [
    {
        "name": "Veg Roll",
        "price": 40,
        "available": True,
        "discount": 0,
        "popular": True,
    },
    {
        "name": "Maggi",
        "price": 40,
        "available": True,
        "discount": 0,
        "popular": True,
    },
    {
        "name": "Sandwich",
        "price": 50,
        "available": True,
        "discount": 0,
        "popular": True,
    },
    {
        "name": "Samosa",
        "price": 15,
        "available": True,
        "discount": 0,
        "popular": False,
    },
    {
        "name": "Tea",
        "price": 20,
        "available": True,
        "discount": 0,
        "popular": True,
    },
    {
        "name": "Coffee",
        "price": 30,
        "available": True,
        "discount": 0,
        "popular": False,
    },
    {
        "name": "Cold Drink",
        "price": 30,
        "available": True,
        "discount": 0,
        "popular": False,
    },
]


# Old Firebase document IDs from earlier versions
LEGACY_MENU_NAME_MAP = {
    "4u3FCDLEIKKmeQcLXdnW": "Veg Roll",
    "Ulp0Yd6IZvOYMRxUeRof": "Maggi",
    "0z3xzZZH7Yajbkpa03fb": "Tea",
    "pI7CfsYLvEocPU1n2RTx": "Sandwich",
}


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background: #f7f8fc;
    }

    .main .block-container {
        max-width: 1200px;
        padding-top: 1.5rem;
        padding-bottom: 3rem;
    }

    .hero {
        padding: 2.2rem 2rem;
        border-radius: 24px;
        background: linear-gradient(
            135deg,
            #fff7ed 0%,
            #ffffff 52%,
            #eff6ff 100%
        );
        border: 1px solid #e5e7eb;
        margin: 1rem 0 1.5rem 0;
    }

    .hero h1 {
        font-size: 2.4rem;
        margin: 0;
        color: #111827;
        line-height: 1.15;
    }

    .hero p {
        font-size: 1.05rem;
        color: #4b5563;
        margin-top: .7rem;
        margin-bottom: 0;
    }

    .card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 18px;
        padding: 1.15rem;
        height: 100%;
        box-shadow: 0 2px 8px rgba(0,0,0,.035);
    }

    .card h3 {
        margin: 0 0 .4rem;
        color: #111827;
    }

    .card p {
        color: #6b7280;
        margin: 0;
    }

    .success-box {
        padding: 1.1rem;
        border-radius: 18px;
        background: #ecfdf5;
        border: 1px solid #a7f3d0;
        margin: .8rem 0;
    }

    .warning-box {
        padding: 1rem;
        border-radius: 16px;
        background: #fffbeb;
        border: 1px solid #fde68a;
    }

    .order-id {
        font-size: 2.4rem;
        font-weight: 800;
        text-align: center;
    }

    .login-box {
        max-width: 600px;
        margin: 1rem auto;
        padding: 1.5rem;
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 22px;
    }

    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e5e7eb;
        padding: 12px;
        border-radius: 16px;
    }

    div[data-testid="stImage"] img {
        border-radius: 14px;
    }

    button[kind="primary"] {
        border-radius: 12px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FIREBASE CONNECTION
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
# FIREBASE AUTHENTICATION
# ============================================================

def auth_request(
    endpoint,
    payload,
):

    api_key = get_web_api_key()

    if not api_key:
        return (
            None,
            "Firebase Web API Key is missing from Streamlit Secrets.",
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

        return (
            None,
            data.get(
                "error",
                {},
            ).get(
                "message",
                "Authentication failed.",
            ),
        )

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


def send_password_reset(email):

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
            data.get(
                "error",
                {},
            ).get(
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

            session["id_token"] = (
                refreshed["id_token"]
            )

            session["refresh_token"] = (
                refreshed["refresh_token"]
            )

            session["login_time"] = (
                datetime.now().timestamp()
            )

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

    if not db:
        return None

    snap = (
        db.collection("users")
        .document(uid)
        .get()
    )

    if not snap.exists:
        return None

    data = snap.to_dict()

    data["uid"] = uid

    return data


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

    return get_user_profile(uid)


# ============================================================
# IMAGE HELPERS
# ============================================================

def prepare_menu_image(
    uploaded_file,
    max_bytes=120000,
):

    if uploaded_file is None:
        return None, None

    try:

        image = Image.open(
            uploaded_file
        ).convert("RGB")

        image.thumbnail(
            (900, 700)
        )

        quality = 80

        while quality >= 40:

            buffer = BytesIO()

            image.save(
                buffer,
                format="JPEG",
                quality=quality,
                optimize=True,
            )

            image_bytes = (
                buffer.getvalue()
            )

            if (
                len(image_bytes)
                <= max_bytes
            ):

                encoded = (
                    base64.b64encode(
                        image_bytes
                    ).decode("utf-8")
                )

                return (
                    encoded,
                    "image/jpeg",
                )

            quality -= 10

        return None, None

    except Exception:

        return None, None


def decode_menu_image(item):

    image_data = item.get(
        "image_data"
    )

    if not image_data:
        return None

    try:

        return base64.b64decode(
            image_data
        )

    except Exception:

        return None


# ============================================================
# MENU
# ============================================================

def load_menu():

    if not db:
        return [
            {
                **item,
                "_doc_id": item["name"],
            }
            for item in DEFAULT_MENU
        ]

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

        return [
            {
                **item,
                "_doc_id": item["name"],
            }
            for item in DEFAULT_MENU
        ]

    menu = []

    unknown_number = 1

    for doc in docs:

        data = doc.to_dict() or {}

        doc_id = doc.id

        stored_name = str(
            data.get(
                "name",
                "",
            )
        ).strip()

        if stored_name:

            display_name = stored_name

        elif doc_id in LEGACY_MENU_NAME_MAP:

            display_name = (
                LEGACY_MENU_NAME_MAP[
                    doc_id
                ]
            )

            try:

                db.collection(
                    "menu"
                ).document(
                    doc_id
                ).set(
                    {
                        "name":
                            display_name
                    },
                    merge=True,
                )

            except Exception:

                pass

        else:

            display_name = (
                f"Food Item "
                f"{unknown_number}"
            )

            unknown_number += 1

        data["name"] = (
            display_name
        )

        data["_doc_id"] = doc_id

        data.setdefault(
            "price",
            30,
        )

        data.setdefault(
            "available",
            True,
        )

        data.setdefault(
            "discount",
            0,
        )

        data.setdefault(
            "popular",
            False,
        )

        menu.append(data)

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
    image_data=None,
    image_type=None,
    doc_id=None,
):

    document_id = (
        doc_id
        or name
    )

    payload = {
        "name": name,
        "price": float(price),
        "discount": float(discount),
        "available": bool(
            available
        ),
        "popular": bool(
            popular
        ),
    }

    if image_data:

        payload[
            "image_data"
        ] = image_data

        payload[
            "image_type"
        ] = (
            image_type
            or "image/jpeg"
        )

    db.collection(
        "menu"
    ).document(
        document_id
    ).set(
        payload,
        merge=True,
    )


def update_menu_popular(
    item,
    popular,
):

    doc_id = item.get(
        "_doc_id",
        item.get("name"),
    )

    db.collection(
        "menu"
    ).document(
        doc_id
    ).set(
        {
            "popular":
                bool(popular)
        },
        merge=True,
    )


def delete_menu_item(
    item,
):

    doc_id = item.get(
        "_doc_id",
        item.get("name"),
    )

    db.collection(
        "menu"
    ).document(
        doc_id
    ).delete()


# ============================================================
# ORDER COUNTER
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

        snapshot = ref.get(
            transaction=transaction
        )

        if snapshot.exists:

            current = int(
                snapshot.to_dict()
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
                "value":
                    new_value
            },
            merge=True,
        )

        return new_value

    number = (
        increment_counter(
            transaction,
            ref,
        )
    )

    return (
        f"{number:03d}"
    )


# ============================================================
# ORDER HELPERS
# ============================================================

def find_order_document(
    order,
):

    order_id = str(
        order.get(
            "order_id",
            "",
        )
    )

    order_date = order.get(
        "date",
        date.today().isoformat(),
    )

    ref = (
        db.collection("orders")
        .document(
            f"{order_date}_{order_id}"
        )
    )

    if ref.get().exists:
        return ref

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
            "status":
                new_status,
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
            "payment_method":
                "Pay at Counter",
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

    orders = []

    for doc in docs:

        item = (
            doc.to_dict()
            or {}
        )

        item["_doc_id"] = (
            doc.id
        )

        orders.append(item)

    def sort_key(order):

        try:

            return int(
                str(
                    order.get(
                        "order_id",
                        "0",
                    )
                )
            )

        except Exception:

            return 0

    return sorted(
        orders,
        key=sort_key,
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

    orders = []

    for doc in docs:

        item = (
            doc.to_dict()
            or {}
        )

        item["_doc_id"] = (
            doc.id
        )

        orders.append(item)

    return sorted(
        orders,
        key=lambda x:
            str(
                x.get(
                    "date",
                    "",
                )
            ),
        reverse=True,
    )


# ============================================================
# WALLET
# ============================================================

def add_wallet_money(
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

    wallet_ref = (
        db.collection(
            "wallet_transactions"
        ).document()
    )

    @transactional
    def credit_wallet(
        transaction,
        user_ref,
        wallet_ref,
    ):

        snap = user_ref.get(
            transaction=transaction
        )

        current = 0

        if snap.exists:

            current = float(
                snap.to_dict()
                .get(
                    "wallet_balance",
                    0,
                )
            )

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
            wallet_ref,
            {
                "uid": uid,
                "type": "Credit",
                "amount": amount,
                "balance_after":
                    new_balance,
                "reason": reason,
                "date":
                    date.today().isoformat(),
                "created_at":
                    firestore.SERVER_TIMESTAMP,
            },
        )

        return new_balance

    try:

        balance = (
            credit_wallet(
                transaction,
                user_ref,
                wallet_ref,
            )
        )

        return True, balance

    except Exception as e:

        return False, str(e)


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

    menu = load_menu()

    menu_map = {
        item["name"]: item
        for item in menu
    }

    items = []

    total = 0

    for name, quantity in cart.items():

        quantity = int(quantity)

        if quantity <= 0:
            continue

        item = menu_map.get(
            name
        )

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
                "quantity":
                    quantity,
                "unit_price":
                    price,
                "line_total":
                    line_total,
            }
        )

        total += line_total

    total = round(
        total,
        2,
    )

    if not items:
        return (
            False,
            "Your cart is empty.",
        )

    order_id = (
        generate_daily_order_id()
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
    def create_order_transaction(
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

        user_data = (
            user_snap.to_dict()
        )

        if (
            payment_method
            == "Wallet"
        ):

            balance = float(
                user_data.get(
                    "wallet_balance",
                    0,
                )
            )

            if balance < total:

                raise ValueError(
                    "Insufficient wallet balance. "
                    f"Available ₹{balance:.2f}."
                )

            new_balance = round(
                balance - total,
                2,
            )

            transaction.update(
                user_ref,
                {
                    "wallet_balance":
                        new_balance
                },
            )

            wallet_tx_ref = (
                db.collection(
                    "wallet_transactions"
                ).document()
            )

            transaction.set(
                wallet_tx_ref,
                {
                    "uid": uid,
                    "type": "Debit",
                    "amount": total,
                    "balance_after":
                        new_balance,
                    "reason":
                        f"Order #{order_id}",
                    "order_id":
                        order_id,
                    "date": today,
                    "created_at":
                        firestore.SERVER_TIMESTAMP,
                },
            )

            payment_status = "Paid"

        else:

            payment_status = (
                "Pending"
            )

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

        result = (
            create_order_transaction(
                transaction,
                order_ref,
                user_ref,
            )
        )

        return True, result

    except Exception as e:

        return False, str(e)


# ============================================================
# SESSION STATE
# ============================================================

def init_state():

    defaults = {
        "page":
            "Home",

        "cart":
            {},

        "last_order":
            None,

        "cafeteria_logged_in":
            False,
    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = (
                value
            )


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

    st.session_state.page = (
        "Home"
    )

    st.rerun()


init_state()


# ============================================================
# NAVIGATION
# ============================================================

def render_nav():

    student = current_student()

    cafeteria = (
        st.session_state.get(
            "cafeteria_logged_in",
            False,
        )
    )

    if student:

        cols = st.columns(6)

        nav_items = [
            ("🏠 Home", "Home"),
            ("🍔 Order Food", "Order Food"),
            ("📦 My Orders", "My Orders"),
            ("💰 Wallet", "Wallet"),
            ("💬 Feedback", "Feedback"),
            ("🚪 Logout", "Logout"),
        ]

        for col, (
            label,
            page,
        ) in zip(
            cols,
            nav_items,
        ):

            with col:

                if st.button(
                    label,
                    use_container_width=True,
                    key=f"nav_{page}",
                ):

                    if page == "Logout":

                        logout_student()

                    else:

                        go_to(page)

    elif cafeteria:

        cols = st.columns(4)

        nav_items = [
            (
                "📊 Dashboard",
                "Cafeteria Dashboard",
            ),
            (
                "🍔 Menu",
                "Menu Management",
            ),
            (
                "💬 Feedback",
                "Feedback Management",
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
            nav_items,
        ):

            with col:

                if st.button(
                    label,
                    use_container_width=True,
                    key=f"caf_nav_{page}",
                ):

                    if (
                        page
                        == "Cafeteria Logout"
                    ):

                        st.session_state.cafeteria_logged_in = (
                            False
                        )

                        go_to(
                            "Home"
                        )

                    else:

                        go_to(page)

    else:

        cols = st.columns(3)

        nav_items = [
            ("🏠 Home", "Home"),
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
            nav_items,
        ):

            with col:

                if st.button(
                    label,
                    use_container_width=True,
                    key=f"guest_{page}",
                ):

                    go_to(page)

    st.divider()


# ============================================================
# HOME PAGE
# ============================================================

def home_page():

    student = current_student()

    st.markdown(
        """
        <div class="hero">
            <h1>Skip the Queue. Enjoy Your Break. 🍽️</h1>
            <p>
                Pre-order your food from the campus cafeteria
                and collect it quickly.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # LOGGED-IN STUDENT
    # --------------------------------------------------------

    if student:

        balance = float(
            student.get(
                "wallet_balance",
                0,
            )
        )

        st.success(
            f"Welcome back, "
            f"{student.get('name', 'Student')}! "
            f"Wallet: ₹{balance:.2f}"
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
                "📦 My Orders",
                use_container_width=True,
            ):

                go_to(
                    "My Orders"
                )

        with c3:

            if st.button(
                "💰 Wallet",
                use_container_width=True,
            ):

                go_to(
                    "Wallet"
                )

    # --------------------------------------------------------
    # GUEST
    # --------------------------------------------------------

    else:

        c1, c2 = st.columns(2)

        with c1:

            if st.button(
                "🎓 Student Login",
                type="primary",
                use_container_width=True,
            ):

                go_to(
                    "Student Login"
                )

        with c2:

            if st.button(
                "🍔 Start Ordering",
                use_container_width=True,
            ):

                go_to(
                    "Student Login"
                )

    st.divider()

    # --------------------------------------------------------
    # HOW IT WORKS
    # --------------------------------------------------------

    st.markdown(
        "### How it works"
    )

    steps = [
        (
            "1",
            "Login",
            "Create your student account.",
        ),
        (
            "2",
            "Order",
            "Choose food and payment.",
        ),
        (
            "3",
            "Prepare",
            "Cafeteria prepares your order.",
        ),
        (
            "4",
            "Collect",
            "Show your Order ID.",
        ),
    ]

    cols = st.columns(4)

    for i, (
        number,
        title,
        description,
    ) in enumerate(steps):

        with cols[i]:

            st.markdown(
                f"""
                <div class="card">
                    <h3>{number}. {title}</h3>
                    <p>{description}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        "### Order Modes"
    )

    c1, c2 = st.columns(2)

    with c1:

        st.markdown(
            """
            <div class="card">
                <h3>🕐 Break Order</h3>
                <p>
                    Select your break period and
                    collect your confirmed order
                    during that break.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:

        st.markdown(
            """
            <div class="card">
                <h3>🏠 Regular Order</h3>
                <p>
                    Room / Hostel pre-order available
                    anytime. Preparation takes
                    approximately 10–15 minutes.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.caption(
        f"Desk: {DESK_NAME} • "
        f"Phone: {DESK_PHONE} • "
        f"Email: {DESK_EMAIL}"
    )


# ============================================================
# STUDENT LOGIN
# ============================================================

def student_login_page():

    st.markdown(
        "## 🎓 Student Login"
    )

    if current_student():

        student = current_student()

        st.success(
            f"Logged in as "
            f"{student.get('name', 'Student')}"
        )

        if st.button(
            "Go to Home",
            type="primary",
        ):

            go_to("Home")

        return

    login_tab, signup_tab, reset_tab = (
        st.tabs(
            [
                "Login",
                "Create Account",
                "Forgot Password",
            ]
        )
    )

    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    with login_tab:

        email = st.text_input(
            "Email",
            key="student_login_email",
        )

        password = st.text_input(
            "Password",
            type="password",
            key="student_login_password",
        )

        if st.button(
            "Login",
            type="primary",
            use_container_width=True,
            key="student_login_button",
        ):

            if not email or not password:

                st.error(
                    "Please enter email and password."
                )

            else:

                data, error = (
                    login_student(
                        email.strip(),
                        password,
                    )
                )

                if error:

                    st.error(
                        f"Login failed: {error}"
                    )

                else:

                    uid = data[
                        "localId"
                    ]

                    st.session_state.auth_session = {
                        "id_token":
                            data["idToken"],
                        "refresh_token":
                            data["refreshToken"],
                        "login_time":
                            datetime.now().timestamp(),
                    }

                    profile = (
                        get_user_profile(
                            uid
                        )
                    )

                    if not profile:

                        st.error(
                            "Student profile not found."
                        )

                    else:

                        st.session_state.student_user = (
                            profile
                        )

                        st.session_state.page = (
                            "Home"
                        )

                        st.rerun()

    # --------------------------------------------------------
    # SIGNUP
    # --------------------------------------------------------

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
            key="signup_button",
        ):

            if not name.strip():

                st.error(
                    "Enter your name."
                )

            elif not student_id.strip():

                st.error(
                    "Enter your student ID."
                )

            elif not email.strip():

                st.error(
                    "Enter your email."
                )

            elif len(password) < 6:

                st.error(
                    "Password must be at least 6 characters."
                )

            elif password != confirm:

                st.error(
                    "Passwords do not match."
                )

            else:

                data, error = (
                    signup_student(
                        email.strip(),
                        password,
                    )
                )

                if error:

                    st.error(
                        f"Could not create account: {error}"
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

                    st.session_state.auth_session = {
                        "id_token":
                            data["idToken"],
                        "refresh_token":
                            data["refreshToken"],
                        "login_time":
                            datetime.now().timestamp(),
                    }

                    st.success(
                        "Account created successfully."
                    )

                    st.session_state.page = (
                        "Home"
                    )

                    st.rerun()

    # --------------------------------------------------------
    # PASSWORD RESET
    # --------------------------------------------------------

    with reset_tab:

        email = st.text_input(
            "Account Email",
            key="reset_email",
        )

        if st.button(
            "Send Password Reset",
            use_container_width=True,
            key="reset_button",
        ):

            if not email.strip():

                st.error(
                    "Enter your email."
                )

            else:

                _, error = (
                    send_password_reset(
                        email.strip()
                    )
                )

                if error:

                    st.error(
                        f"Could not send reset email: {error}"
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

    available_items = [
        item
        for item in menu
        if item.get(
            "available",
            True,
        )
    ]

    if not available_items:

        st.warning(
            "No food items are currently available."
        )

        return

    # --------------------------------------------------------
    # POPULAR PICKS
    # --------------------------------------------------------

    popular = [
        item
        for item in available_items
        if item.get(
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

        for i, item in enumerate(
            popular[:3]
        ):

            with cols[i]:

                with st.container(
                    border=True
                ):

                    image_bytes = (
                        decode_menu_image(
                            item
                        )
                    )

                    if image_bytes:

                        st.image(
                            image_bytes,
                            use_container_width=True,
                        )

                    else:

                        st.markdown(
                            "🍽️"
                        )

                    st.markdown(
                        f"### {item['name']}"
                    )

                    discount = float(
                        item.get(
                            "discount",
                            0,
                        )
                    )

                    if discount > 0:

                        st.write(
                            f"~~₹{float(item.get('price', 0)):.0f}~~ "
                            f"**₹{effective_price(item):.0f}**"
                        )

                    else:

                        st.write(
                            f"**₹{effective_price(item):.0f}**"
                        )

    st.divider()

    # --------------------------------------------------------
    # MENU
    # --------------------------------------------------------

    st.markdown(
        "### 🍽️ Menu"
    )

    for item_index, item in enumerate(
        available_items
    ):

        name = item["name"]

        price = effective_price(
            item
        )

        unique_id = str(
            item.get(
                "_doc_id",
                f"item_{item_index}",
            )
        )

        with st.container(
            border=True
        ):

            c_image, c_info, c_qty = (
                st.columns(
                    [1.3, 5, 1.3]
                )
            )

            with c_image:

                image_bytes = (
                    decode_menu_image(
                        item
                    )
                )

                if image_bytes:

                    st.image(
                        image_bytes,
                        width=110,
                    )

                else:

                    st.markdown(
                        "🍽️"
                    )

            with c_info:

                discount = float(
                    item.get(
                        "discount",
                        0,
                    )
                )

                if discount > 0:

                    st.markdown(
                        f"### {name}"
                    )

                    st.write(
                        f"~~₹{float(item.get('price', 0)):.0f}~~ "
                        f"**₹{price:.0f}**"
                    )

                    st.caption(
                        f"{discount:.0f}% discount"
                    )

                else:

                    st.markdown(
                        f"### {name}"
                    )

                    st.write(
                        f"**₹{price:.0f}**"
                    )

                if item.get(
                    "popular",
                    False,
                ):

                    st.caption(
                        "⭐ Popular Pick"
                    )

            with c_qty:

                current = int(
                    st.session_state.cart.get(
                        name,
                        0,
                    )
                )

                qty = st.number_input(
                    "Qty",
                    min_value=0,
                    max_value=20,
                    value=current,
                    step=1,
                    key=f"qty_{unique_id}",
                )

                if qty <= 0:

                    st.session_state.cart.pop(
                        name,
                        None,
                    )

                else:

                    st.session_state.cart[
                        name
                    ] = int(qty)

    st.divider()

    # --------------------------------------------------------
    # CART
    # --------------------------------------------------------

    cart = (
        st.session_state.cart
    )

    if not cart:

        st.info(
            "Your cart is empty. Select quantities above."
        )

        return

    menu_map = {
        item["name"]: item
        for item in menu
    }

    total = 0

    st.markdown(
        "### 🛒 Your Cart"
    )

    for name, quantity in (
        cart.items()
    ):

        item = menu_map.get(
            name
        )

        if item:

            line_total = (
                effective_price(item)
                * quantity
            )

            total += line_total

            st.write(
                f"**{name}** × "
                f"{quantity} = "
                f"₹{line_total:.0f}"
            )

    total = round(
        total,
        2,
    )

    st.markdown(
        f"### Total: ₹{total:.0f}"
    )

    # --------------------------------------------------------
    # ORDER MODE
    # --------------------------------------------------------

    order_mode = st.radio(
        "Order Type",
        [
            "Break Order",
            "Regular Order",
        ],
        horizontal=True,
        key="order_mode",
    )

    break_time = None

    if (
        order_mode
        == "Break Order"
    ):

        st.caption(
            "Choose the break period when you will collect."
        )

        break_time = st.selectbox(
            "Break Time",
            BREAK_OPTIONS,
            key="break_time",
        )

    else:

        st.info(
            "Regular orders are for Room / Hostel "
            "pre-order only. Available anytime, "
            "including during breaks. "
            "Estimated preparation time: 10–15 minutes."
        )

    # --------------------------------------------------------
    # PAYMENT
    # --------------------------------------------------------

    payment_method = st.radio(
        "Payment Method",
        [
            "Wallet",
            "Pay at Counter",
        ],
        horizontal=True,
        key="payment_method",
    )

    wallet_balance = float(
        student.get(
            "wallet_balance",
            0,
        )
    )

    if (
        payment_method
        == "Wallet"
    ):

        st.caption(
            f"Wallet balance: "
            f"₹{wallet_balance:.2f}"
        )

        if wallet_balance < total:

            st.warning(
                "Insufficient wallet balance. "
                f"You need "
                f"₹{total - wallet_balance:.2f} more."
            )

    else:

        st.caption(
            "Pay the cafeteria desk when collecting."
        )

    # --------------------------------------------------------
    # PLACE ORDER
    # --------------------------------------------------------

    if st.button(
        "Place Order",
        type="primary",
        use_container_width=True,
        key="place_order_button",
    ):

        if (
            payment_method
            == "Wallet"
            and wallet_balance
            < total
        ):

            st.error(
                "Insufficient wallet balance."
            )

            return

        ok, result = (
            create_order(
                student,
                cart,
                order_mode,
                break_time,
                payment_method,
            )
        )

        if not ok:

            st.error(
                f"Could not place order: "
                f"{result}"
            )

            return

        st.session_state.last_order = (
            result
        )

        st.session_state.cart = {}

        st.session_state.page = (
            "Order Confirmation"
        )

        st.rerun()


# ============================================================
# ORDER CONFIRMATION
# ============================================================

def confirmation_page():

    order = (
        st.session_state.get(
            "last_order"
        )
    )

    if not order:

        st.info(
            "No recent order."
        )

        if st.button(
            "Order Food"
        ):

            go_to(
                "Order Food"
            )

        return

    st.markdown(
        "## ✅ Order Confirmed"
    )

    st.markdown(
        f"""
        <div class="success-box">
            <div>Your Order ID</div>
            <div class="order-id">
                #{order.get("order_id")}
            </div>
            <p style="text-align:center">
                Show this Order ID at the cafeteria desk.
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
            f"**Break:** "
            f"{order.get('break_time')}"
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
        f"{order.get('status', 'Confirmed')}"
    )

    st.write(
        f"**Total:** "
        f"₹{order.get('total', 0):.0f}"
    )

    st.markdown(
        "### Items"
    )

    for item in order.get(
        "items",
        [],
    ):

        st.write(
            f"{item.get('name')} × "
            f"{item.get('quantity')} — "
            f"₹{item.get('line_total', 0):.0f}"
        )

    if (
        order.get(
            "payment_method"
        )
        == "Pay at Counter"
    ):

        st.warning(
            "Please pay at the cafeteria desk before collection."
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

    orders = (
        get_student_orders(
            student["uid"]
        )
    )

    if not orders:

        st.info(
            "You have no orders yet."
        )

        if st.button(
            "Order Food"
        ):

            go_to(
                "Order Food"
            )

        return

    for index, order in enumerate(
        orders[:30]
    ):

        status = order.get(
            "status",
            "Confirmed",
        )

        payment_status = order.get(
            "payment_status",
            "-",
        )

        with st.container(
            border=True
        ):

            c1, c2, c3, c4 = (
                st.columns(4)
            )

            with c1:

                st.markdown(
                    f"### #{order.get('order_id')}"
                )

            with c2:

                st.write(
                    f"**Status**\n\n"
                    f"{status}"
                )

            with c3:

                st.write(
                    f"**Payment**\n\n"
                    f"{payment_status}"
                )

            with c4:

                st.write(
                    f"**Total**\n\n"
                    f"₹{order.get('total', 0):.0f}"
                )

            if order.get(
                "break_time"
            ):

                st.caption(
                    f"Break: "
                    f"{order.get('break_time')}"
                )

            raw_items = order.get(
                "items",
                [],
            )

            if isinstance(
                raw_items,
                dict,
            ):

                item_text = ", ".join(
                    f"{name} × {quantity}"
                    for name, quantity
                    in raw_items.items()
                )

            elif isinstance(
                raw_items,
                list,
            ):

                parts = []

                for x in raw_items:

                    if isinstance(
                        x,
                        dict,
                    ):

                        parts.append(
                            f"{x.get('name', 'Item')} "
                            f"× {x.get('quantity', 1)}"
                        )

                    else:

                        parts.append(
                            str(x)
                        )

                item_text = ", ".join(
                    parts
                )

            else:

                item_text = str(
                    raw_items
                )

            st.write(
                item_text
            )

            if status != "Collected":

                st.info(
                    "Bring your Order ID to the "
                    "cafeteria desk for collection."
                )


# ============================================================
# WALLET
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
        "## 💰 Wallet"
    )

    st.metric(
        "Available Balance",
        f"₹{balance:.2f}",
    )

    st.info(
        "Give money to the cafeteria desk "
        "and ask the desk person to credit "
        "the same amount to your prepaid wallet."
    )

    st.markdown(
        "### Wallet Top-up"
    )

    amount = st.number_input(
        "Amount to add",
        min_value=1.0,
        max_value=10000.0,
        value=100.0,
        step=50.0,
        key="wallet_amount",
    )

    reason = st.text_input(
        "Reason",
        value="Cash deposited at cafeteria desk",
        key="wallet_reason",
    )

    if st.button(
        "Add Wallet Money",
        type="primary",
        key="wallet_add_button",
    ):

        ok, result = (
            add_wallet_money(
                student["uid"],
                amount,
                reason,
            )
        )

        if ok:

            st.success(
                f"₹{amount:.2f} added. "
                f"New balance: ₹{result:.2f}"
            )

            st.rerun()

        else:

            st.error(
                str(result)
            )

    st.caption(
        "Prototype wallet: the cafeteria desk controls wallet credits."
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
        key="feedback_rating",
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
        key="feedback_category",
    )

    message = st.text_area(
        "Your feedback",
        key="feedback_message",
    )

    feedback_photo = st.file_uploader(
        "Upload Photo (optional)",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp",
        ],
        key="feedback_photo",
    )

    if feedback_photo:

        st.image(
            feedback_photo,
            width=250,
        )

    if st.button(
        "Submit Feedback",
        type="primary",
        key="submit_feedback",
    ):

        if not message.strip():

            st.error(
                "Please enter your feedback."
            )

            return

        photo_data = None

        if feedback_photo:

            photo_data, _ = (
                prepare_menu_image(
                    feedback_photo,
                    max_bytes=120000,
                )
            )

        feedback_data = {

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

            "date":
                date.today().isoformat(),

            "created_at":
                firestore.SERVER_TIMESTAMP,
        }

        if photo_data:

            feedback_data[
                "image_data"
            ] = photo_data

            feedback_data[
                "image_type"
            ] = "image/jpeg"

        db.collection(
            "feedback"
        ).add(
            feedback_data
        )

        st.success(
            "Thank you for your feedback!"
        )

        st.rerun()


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
            <h3>Cafeteria Desk Login</h3>
            <p>
                This portal is for cafeteria staff.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_id = st.text_input(
        "Login ID",
        key="cafeteria_login_id",
    )

    password = st.text_input(
        "Password",
        type="password",
        key="cafeteria_password",
    )

    if st.button(
        "Login to Cafeteria Portal",
        type="primary",
        use_container_width=True,
        key="cafeteria_login_button",
    ):

        if (
            login_id.strip().lower()
            == CAFETERIA_LOGIN_ID.lower()
            and password
            == CAFETERIA_PASSWORD
        ):

            st.session_state.cafeteria_logged_in = (
                True
            )

            st.session_state.page = (
                "Cafeteria Dashboard"
            )

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
        "cafeteria_logged_in",
        False,
    ):

        go_to(
            "Cafeteria Portal"
        )

        return

    st.markdown(
        "## 📊 Cafeteria Dashboard"
    )

    orders = (
        get_today_orders()
    )

    total = len(
        orders
    )

    confirmed = sum(
        x.get("status")
        == "Confirmed"
        for x in orders
    )

    preparing = sum(
        x.get("status")
        == "Preparing"
        for x in orders
    )

    ready = sum(
        x.get("status")
        == "Ready"
        for x in orders
    )

    collected = sum(
        x.get("status")
        == "Collected"
        for x in orders
    )

    cols = st.columns(5)

    cols[0].metric(
        "📦 Total Orders",
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
        "Search by Order ID, Student Name or Student ID",
        key="dashboard_search",
    )

    status_filter = st.selectbox(
        "Filter by Status",
        [
            "All",
            "Confirmed",
            "Preparing",
            "Ready",
            "Collected",
        ],
        key="dashboard_status_filter",
    )

    filtered = []

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
            status_filter != "All"
            and order.get("status")
            != status_filter
        ):

            continue

        filtered.append(
            order
        )

    for order_index, order in enumerate(
        filtered
    ):

        with st.container(
            border=True
        ):

            c1, c2, c3, c4 = (
                st.columns(
                    [1, 2.5, 2.5, 2]
                )
            )

            with c1:

                st.markdown(
                    f"### #{order.get('order_id', '-')}"
                )

            with c2:

                st.write(
                    f"**{order.get('student_name', '-')}**"
                )

                st.caption(
                    "Student ID: "
                    f"{order.get('student_id', '-')}"
                )

                if order.get(
                    "order_type"
                ):

                    st.caption(
                        "Type: "
                        f"{order.get('order_type')}"
                    )

                if order.get(
                    "break_time"
                ):

                    st.caption(
                        "Break: "
                        f"{order.get('break_time')}"
                    )

            with c3:

                raw_items = (
                    order.get(
                        "items",
                        [],
                    )
                )

                if isinstance(
                    raw_items,
                    dict,
                ):

                    item_text = (
                        ", ".join(
                            f"{name} × {quantity}"
                            for name, quantity
                            in raw_items.items()
                        )
                    )

                elif isinstance(
                    raw_items,
                    list,
                ):

                    parts = []

                    for x in raw_items:

                        if isinstance(
                            x,
                            dict,
                        ):

                            parts.append(
                                f"{x.get('name', 'Item')} "
                                f"× {x.get('quantity', 1)}"
                            )

                        else:

                            parts.append(
                                str(x)
                            )

                    item_text = ", ".join(
                        parts
                    )

                else:

                    item_text = str(
                        raw_items
                    )

                st.write(
                    item_text
                )

                st.caption(
                    f"₹{float(order.get('total', 0)):.0f}"
                )

            with c4:

                status = order.get(
                    "status",
                    "Confirmed",
                )

                payment_status = (
                    order.get(
                        "payment_status",
                        "Pending",
                    )
                )

                st.write(
                    f"**Status:** {status}"
                )

                st.write(
                    f"**Payment:** {payment_status}"
                )

                order_key = str(
                    order.get(
                        "_doc_id",
                        order.get(
                            "order_id",
                            order_index,
                        ),
                    )
                )

                if (
                    order.get(
                        "payment_method"
                    )
                    == "Pay at Counter"
                    and payment_status
                    != "Paid"
                ):

                    if st.button(
                        "💵 Mark Payment Received",
                        key=f"pay_{order_key}",
                        use_container_width=True,
                    ):

                        ok, error = (
                            mark_counter_payment_received(
                                order
                            )
                        )

                        if ok:

                            st.success(
                                "Payment marked received."
                            )

                            st.rerun()

                        else:

                            st.error(
                                error
                            )

                if (
                    status
                    == "Confirmed"
                ):

                    if st.button(
                        "▶ Start Preparing",
                        key=f"prep_{order_key}",
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

                elif (
                    status
                    == "Preparing"
                ):

                    if st.button(
                        "✓ Mark Ready",
                        key=f"ready_{order_key}",
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

                elif (
                    status
                    == "Ready"
                ):

                    if (
                        order.get(
                            "payment_method"
                        )
                        == "Pay at Counter"
                        and payment_status
                        != "Paid"
                    ):

                        st.warning(
                            "Collect payment before handover."
                        )

                    else:

                        if st.button(
                            "📦 Mark Collected",
                            key=f"collect_{order_key}",
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
# MENU MANAGEMENT
# ============================================================

def menu_management_page():

    if not st.session_state.get(
        "cafeteria_logged_in",
        False,
    ):

        go_to(
            "Cafeteria Portal"
        )

        return

    st.markdown(
        "## 🍔 Menu Management"
    )

    # --------------------------------------------------------
    # ADD NEW ITEM
    # --------------------------------------------------------

    with st.container(
        border=True
    ):

        st.markdown(
            "### ➕ Add New Food Item"
        )

        c1, c2 = st.columns(2)

        with c1:

            name = st.text_input(
                "Item Name",
                key="menu_name",
            )

            price = st.number_input(
                "Price",
                min_value=0.0,
                step=5.0,
                key="menu_price",
            )

            discount = st.number_input(
                "Discount (%)",
                min_value=0.0,
                max_value=100.0,
                value=0.0,
                step=1.0,
                key="menu_discount",
            )

        with c2:

            uploaded_image = st.file_uploader(
                "Food Image",
                type=[
                    "jpg",
                    "jpeg",
                    "png",
                    "webp",
                ],
                key="new_menu_image",
                help="Upload a clear food image.",
            )

            available = st.checkbox(
                "Available",
                value=True,
                key="menu_available",
            )

            popular = st.checkbox(
                "⭐ Popular Pick",
                value=False,
                key="menu_popular",
            )

        if uploaded_image:

            st.image(
                uploaded_image,
                caption="Preview",
                width=220,
            )

        if st.button(
            "💾 Save New Item",
            type="primary",
            use_container_width=True,
            key="save_new_menu_item",
        ):

            if not name.strip():

                st.error(
                    "Enter an item name."
                )

            elif price <= 0:

                st.error(
                    "Price must be greater than zero."
                )

            else:

                image_data = None
                image_type = None

                if uploaded_image:

                    (
                        image_data,
                        image_type,
                    ) = (
                        prepare_menu_image(
                            uploaded_image
                        )
                    )

                    if not image_data:

                        st.error(
                            "Could not process the image. "
                            "Please try another image."
                        )

                        return

                save_menu_item(
                    name.strip(),
                    price,
                    discount,
                    available,
                    popular,
                    image_data,
                    image_type,
                )

                st.success(
                    f"{name.strip()} added to the menu."
                )

                st.rerun()

    st.divider()

    # --------------------------------------------------------
    # CURRENT MENU
    # --------------------------------------------------------

    st.markdown(
        "### 📋 Current Menu"
    )

    menu = load_menu()

    if not menu:

        st.info(
            "No menu items available."
        )

        return

    for index, item in enumerate(
        menu
    ):

        unique_id = str(
            item.get(
                "_doc_id",
                index,
            )
        )

        with st.container(
            border=True
        ):

            c1, c2, c3 = (
                st.columns(
                    [1.2, 3, 2]
                )
            )

            # ------------------------------------------------
            # IMAGE
            # ------------------------------------------------

            with c1:

                image_bytes = (
                    decode_menu_image(
                        item
                    )
                )

                if image_bytes:

                    st.image(
                        image_bytes,
                        width=130,
                    )

                else:

                    st.markdown(
                        "## 🍽️"
                    )

                    st.caption(
                        "No image"
                    )

            # ------------------------------------------------
            # DETAILS
            # ------------------------------------------------

            with c2:

                st.markdown(
                    f"### {item['name']}"
                )

                price = effective_price(
                    item
                )

                original_price = float(
                    item.get(
                        "price",
                        0,
                    )
                )

                discount_value = float(
                    item.get(
                        "discount",
                        0,
                    )
                )

                if discount_value > 0:

                    st.write(
                        f"~~₹{original_price:.0f}~~ "
                        f"**₹{price:.0f}** "
                        f"({discount_value:.0f}% off)"
                    )

                else:

                    st.write(
                        f"**₹{price:.0f}**"
                    )

                if item.get(
                    "available",
                    True,
                ):

                    st.caption(
                        "🟢 Available"
                    )

                else:

                    st.caption(
                        "🔴 Unavailable"
                    )

                if item.get(
                    "popular",
                    False,
                ):

                    st.caption(
                        "⭐ Popular Pick"
                    )

            # ------------------------------------------------
            # ACTIONS
            # ------------------------------------------------

            with c3:

                current_available = (
                    st.checkbox(
                        "Available",
                        value=item.get(
                            "available",
                            True,
                        ),
                        key=f"available_{unique_id}",
                    )
                )

                current_popular = (
                    st.checkbox(
                        "⭐ Popular",
                        value=item.get(
                            "popular",
                            False,
                        ),
                        key=f"popular_{unique_id}",
                    )
                )

                new_image = (
                    st.file_uploader(
                        "Replace Image",
                        type=[
                            "jpg",
                            "jpeg",
                            "png",
                            "webp",
                        ],
                        key=f"image_{unique_id}",
                    )
                )

                if new_image:

                    st.image(
                        new_image,
                        width=150,
                    )

                if st.button(
                    "💾 Save Changes",
                    key=f"save_changes_{unique_id}",
                    use_container_width=True,
                ):

                    image_data = None
                    image_type = None

                    if new_image:

                        (
                            image_data,
                            image_type,
                        ) = (
                            prepare_menu_image(
                                new_image
                            )
                        )

                        if not image_data:

                            st.error(
                                "Could not process image."
                            )

                            continue

                    save_menu_item(
                        item["name"],
                        item.get(
                            "price",
                            0,
                        ),
                        item.get(
                            "discount",
                            0,
                        ),
                        current_available,
                        current_popular,
                        image_data,
                        image_type,
                        unique_id,
                    )

                    st.success(
                        "Item updated."
                    )

                    st.rerun()

                if st.button(
                    "🗑️ Delete",
                    key=f"delete_menu_{unique_id}",
                    use_container_width=True,
                ):

                    delete_menu_item(
                        item
                    )

                    st.rerun()


# ============================================================
# FEEDBACK MANAGEMENT
# ============================================================

def feedback_management_page():

    if not st.session_state.get(
        "cafeteria_logged_in",
        False,
    ):

        go_to(
            "Cafeteria Portal"
        )

        return

    st.markdown(
        "## 💬 Feedback Management"
    )

    docs = (
        db.collection("feedback")
        .stream()
    )

    feedback = []

    for doc in docs:

        data = (
            doc.to_dict()
            or {}
        )

        feedback.append(
            data
        )

    if not feedback:

        st.info(
            "No feedback yet."
        )

        return

    for index, item in enumerate(
        reversed(
            feedback[-50:]
        )
    ):

        with st.container(
            border=True
        ):

            st.write(
                f"**{item.get('student_name', '-')}** "
                f"— ⭐ {item.get('rating', '-')}/5"
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

            image_data = item.get(
                "image_data"
            )

            if image_data:

                try:

                    st.image(
                        base64.b64decode(
                            image_data
                        ),
                        width=250,
                    )

                except Exception:

                    pass


# ============================================================
# 14-DAY CLEANUP
# ============================================================

def cleanup_old_orders():

    cutoff = (
        date.today()
        - timedelta(days=14)
    ).isoformat()

    docs = (
        db.collection("orders")
        .stream()
    )

    deleted = 0

    for doc in docs:

        data = (
            doc.to_dict()
            or {}
        )

        order_date = str(
            data.get(
                "date",
                "",
            )
        )

        if (
            order_date
            and order_date < cutoff
        ):

            doc.reference.delete()

            deleted += 1

    return deleted


def cleanup_old_feedback():

    cutoff = (
        date.today()
        - timedelta(days=14)
    ).isoformat()

    docs = (
        db.collection("feedback")
        .stream()
    )

    deleted = 0

    for doc in docs:

        data = (
            doc.to_dict()
            or {}
        )

        feedback_date = str(
            data.get(
                "date",
                "",
            )
        )

        if (
            feedback_date
            and feedback_date < cutoff
        ):

            doc.reference.delete()

            deleted += 1

    return deleted


# ============================================================
# CLEANUP MANAGEMENT
# ============================================================

def cleanup_management_page():

    if not st.session_state.get(
        "cafeteria_logged_in",
        False,
    ):

        go_to(
            "Cafeteria Portal"
        )

        return

    st.markdown(
        "## 🗑️ Data Cleanup"
    )

    st.info(
        "Orders and feedback older than 14 days "
        "can be removed. Menu items and menu images "
        "are not removed by this cleanup."
    )

    if st.button(
        "Delete Orders Older Than 14 Days",
        key="cleanup_orders",
    ):

        deleted = (
            cleanup_old_orders()
        )

        st.success(
            f"{deleted} old order(s) deleted."
        )

    if st.button(
        "Delete Feedback Older Than 14 Days",
        key="cleanup_feedback",
    ):

        deleted = (
            cleanup_old_feedback()
        )

        st.success(
            f"{deleted} old feedback item(s) deleted."
        )


# ============================================================
# MAIN
# ============================================================

if not firebase_connected:

    st.error(
        "🔴 Firebase connection failed."
    )

    st.code(
        firebase_error
    )

    st.stop()


# IMPORTANT:
# Firebase success message is intentionally NOT shown
# to normal users because it made the homepage look cluttered.

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


elif page == "Menu Management":

    menu_management_page()


elif page == "Feedback Management":

    feedback_management_page()


elif page == "Cleanup Management":

    cleanup_management_page()


else:

    home_page()
