import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
from google.cloud.firestore_v1 import transactional
from datetime import datetime, date
import requests


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

# Cafeteria login
CAFETERIA_LOGIN_ID = "cafeteria"
CAFETERIA_PASSWORD = "Campus@123"

# Cafeteria desk contact
DESK_NAME = "Rahul"
DESK_PHONE = "9065334992"
DESK_EMAIL = "rahulraj1244raj@gmail.com"

# Break timings
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


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
<style>

.stApp {
    background: #f7f8fc;
}

.hero {
    padding: 2.2rem 2rem;
    border-radius: 24px;
    background: linear-gradient(
        135deg,
        #fff7ed 0%,
        #ffffff 55%,
        #eff6ff 100%
    );
    border: 1px solid #e5e7eb;
    margin-bottom: 1.2rem;
}

.hero h1 {
    font-size: 2.7rem;
    margin: 0;
    color: #111827;
}

.hero p {
    font-size: 1.08rem;
    color: #4b5563;
    margin-top: .6rem;
}

.section-title {
    font-size: 1.45rem;
    font-weight: 700;
    color: #111827;
    margin: 1.2rem 0 .7rem;
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

.small-muted {
    color: #6b7280;
    font-size: .9rem;
}

.order-id {
    font-size: 2rem;
    font-weight: 800;
    color: #111827;
    text-align: center;
}

.success-box {
    padding: 1.2rem;
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

.login-box {
    max-width: 560px;
    margin: 1rem auto;
    padding: 1.5rem;
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 22px;
    box-shadow: 0 5px 20px rgba(0,0,0,.05);
}

div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #e5e7eb;
    padding: 12px;
    border-radius: 16px;
}

button[kind="primary"] {
    border-radius: 12px;
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

        firebase_json = st.secrets.get("firebase_json")

        if not firebase_json:
            raise RuntimeError(
                "firebase_json is missing from Streamlit Secrets."
            )

        if isinstance(firebase_json, str):
            import json
            firebase_json = json.loads(firebase_json)

        cred = credentials.Certificate(firebase_json)

        firebase_admin.initialize_app(cred)

    return firestore.client()


try:
    db = init_firebase()
    firebase_connected = True
    firebase_error = None

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

def auth_request(endpoint, payload):

    api_key = get_web_api_key()

    if not api_key:

        return (
            None,
            "Firebase Web API Key is missing from Streamlit Secrets.",
        )

    url = (
        f"https://identitytoolkit.googleapis.com/v1/"
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
            .get("message", "Authentication failed.")
        )

        return None, message

    except Exception as e:

        return None, str(e)


def signup_student(email, password):

    return auth_request(
        "accounts:signUp",
        {
            "email": email,
            "password": password,
            "returnSecureToken": True,
        },
    )


def login_student(email, password):

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


def refresh_id_token(refresh_token):

    api_key = get_web_api_key()

    if not api_key:

        return None, "Firebase Web API Key is missing."

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
            .get("message", "Could not refresh session."),
        )

    except Exception as e:

        return None, str(e)


def get_logged_in_uid():

    session = st.session_state.get("auth_session")

    if not session:
        return None

    try:

        login_time = session.get(
            "login_time",
            0,
        )

        # Refresh token before ID token becomes stale
        if (
            datetime.now().timestamp()
            - login_time
            > 3000
        ):

            refreshed, error = refresh_id_token(
                session["refresh_token"]
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

            session["id_token"] = refreshed["id_token"]
            session["refresh_token"] = refreshed[
                "refresh_token"
            ]

            session["login_time"] = (
                datetime.now().timestamp()
            )

            st.session_state.auth_session = session

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

    if snap.exists:
        return snap.to_dict()

    return None


def save_user_profile(
    uid,
    name,
    student_id,
    email,
):

    db.collection("users").document(uid).set(
        {
            "name": name,
            "student_id": student_id,
            "email": email,
            "wallet_balance": 0,
            "created_at": firestore.SERVER_TIMESTAMP,
        },
        merge=True,
    )


def current_student():

    uid = get_logged_in_uid()

    if not uid:
        return None

    profile = get_user_profile(uid)

    if not profile:
        return None

    profile["uid"] = uid

    return profile


# ============================================================
# MENU
# ============================================================

def load_menu():

    if not db:
        return DEFAULT_MENU

    docs = list(
        db.collection("menu")
        .stream()
    )

    if not docs:

        for item in DEFAULT_MENU:

            db.collection("menu").document(
                item["name"]
            ).set(item)

        return DEFAULT_MENU

    menu = []

    for doc in docs:

        item = doc.to_dict()

        item["name"] = doc.id

        menu.append(item)

    return sorted(
        menu,
        key=lambda x: x["name"],
    )


def effective_price(item):

    price = float(
        item.get("price", 0)
    )

    discount = float(
        item.get("discount", 0)
    )

    return max(
        0,
        round(
            price * (1 - discount / 100),
            2,
        ),
    )


def save_menu_item(
    name,
    price,
    discount,
    available,
    popular,
):

    db.collection("menu").document(
        name
    ).set(
        {
            "price": float(price),
            "discount": float(discount),
            "available": bool(available),
            "popular": bool(popular),
        },
        merge=True,
    )


def delete_menu_item(name):

    db.collection("menu").document(
        name
    ).delete()


# ============================================================
# DAILY ORDER ID
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
                .get("value", 0)
            )

        else:

            current = 0

        new_value = current + 1

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
# ORDER HELPERS
# ============================================================

def find_order_document(order):

    order_id = str(
        order.get("order_id")
    )

    today = order.get(
        "date",
        date.today().isoformat(),
    )

    # New document structure
    ref = (
        db.collection("orders")
        .document(
            f"{today}_{order_id}"
        )
    )

    snap = ref.get()

    if snap.exists:
        return ref

    # Fallback for older orders
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
            today,
        )
        .limit(1)
        .stream()
    )

    for doc in query:
        return doc.reference

    # Final fallback
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
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )

    return True, None


def mark_counter_payment_received(order):

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
            "payment_status": "Paid",
            "payment_method": "Pay at Counter",
            "payment_received_at":
                firestore.SERVER_TIMESTAMP,
        }
    )

    return True, None


def get_today_orders():

    if not db:
        return []

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

    def order_sort(order):

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
        key=order_sort,
    )


def get_student_orders(uid):

    if not db:
        return []

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
    reason="Wallet top-up",
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

    wallet_tx_ref = (
        db.collection("wallet_transactions")
        .document()
    )

    @transactional
    def credit_wallet(
        transaction,
        user_ref,
        wallet_tx_ref,
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
            wallet_tx_ref,
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

    balance = credit_wallet(
        transaction,
        user_ref,
        wallet_tx_ref,
    )

    return True, balance


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

    items = []

    total = 0

    menu = {
        x["name"]: x
        for x in load_menu()
    }

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

        price = effective_price(item)

        line_total = round(
            price * quantity,
            2,
        )

        items.append(
            {
                "name": name,
                "quantity": quantity,
                "unit_price": price,
                "line_total": line_total,
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

        user_data = user_snap.to_dict()

        if payment_method == "Wallet":

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
                    "created_at":
                        firestore.SERVER_TIMESTAMP,
                    "date": today,
                },
            )

            payment_status = "Paid"

        else:

            payment_status = "Pending"

        order_data = {
            "order_id": order_id,
            "uid": uid,
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
            "items": items,
            "total": total,
            "order_type": order_type,
            "break_time": break_time,
            "payment_method":
                payment_method,
            "payment_status":
                payment_status,
            "status": "Confirmed",
            "date": today,
            "created_at":
                firestore.SERVER_TIMESTAMP,
        }

        transaction.set(
            order_ref,
            order_data,
        )

        return order_data

    try:

        final_order = (
            create_order_transaction(
                transaction,
                order_ref,
                user_ref,
            )
        )

        return True, final_order

    except Exception as e:

        return False, str(e)


# ============================================================
# SESSION
# ============================================================

def init_state():

    defaults = {
        "page": "Home",
        "cart": {},
        "last_order": None,
        "cafeteria_logged_in": False,
    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[key] = value


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

    st.session_state.page = "Home"

    st.session_state.cart = {}

    st.rerun()


init_state()

student = current_student()

if student:

    st.session_state.student_user = student


# ============================================================
# NAVIGATION
# ============================================================

def render_nav():

    logged_in = (
        current_student()
        is not None
    )

    cafeteria = (
        st.session_state
        .get(
            "cafeteria_logged_in",
            False,
        )
    )

    st.markdown(
        "### 🍽️ Campus Cafeteria"
    )

    if logged_in:

        cols = st.columns(6)

        labels = [
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
            labels,
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

        labels = [
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
            labels,
        ):

            with col:

                if st.button(
                    label,
                    use_container_width=True,
                    key=f"cnav_{page}",
                ):

                    if page == "Cafeteria Logout":

                        st.session_state.cafeteria_logged_in = False

                        go_to("Home")

                    else:

                        go_to(page)

    else:

        cols = st.columns(3)

        labels = [
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
            labels,
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
# HOME
# ============================================================

def home_page():

    student = current_student()

    st.markdown(
        """
        <div class="hero">
            <h1>
                Pre-order. Skip the queue. Enjoy your break. 🍽️
            </h1>

            <p>
                Order from Campus Cafeteria before the rush
                and collect your food quickly during your break.
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
                    {student.get("name", "Student")}!
                </b>
                <br>
                Wallet balance:
                <b>₹{balance:.2f}</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)

        with c1:

            if st.button(
                "🍔 Order Food",
                use_container_width=True,
                type="primary",
            ):

                go_to("Order Food")

        with c2:

            if st.button(
                "📦 Track My Orders",
                use_container_width=True,
            ):

                go_to("My Orders")

        with c3:

            if st.button(
                "💰 Wallet",
                use_container_width=True,
            ):

                go_to("Wallet")

    else:

        c1, c2, c3 = st.columns(3)

        cards = [
            (
                "🍔 Order Food",
                "Pre-order your meal and avoid the queue.",
                "Student Login",
            ),
            (
                "⏱️ Save Break Time",
                "Place your order before the cafeteria rush.",
                "Student Login",
            ),
            (
                "💳 Easy Payment",
                "Use your prepaid wallet or pay at the counter.",
                "Student Login",
            ),
        ]

        for col, (
            title,
            text,
            page,
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
                    key=f"home_{title}",
                ):

                    go_to(page)

    st.markdown(
        '<div class="section-title">'
        'How it works'
        '</div>',
        unsafe_allow_html=True,
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
            "Choose food and payment method.",
        ),
        (
            "3",
            "Prepare",
            "Cafeteria confirms your order.",
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
                    <p>{text}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        '<div class="section-title">'
        'Order modes'
        '</div>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns(2)

    with c1:

        st.markdown(
            """
            <div class="card">
                <h3>🕐 Break Order</h3>
                <p>
                    Select one of the scheduled break periods
                    and place your order in advance.
                    Once confirmed, collect it during
                    the selected break.
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
                    For Room / Hostel pre-orders.
                    Available anytime, including during
                    a break. Estimated preparation time:
                    10–15 minutes.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.info(
        f"Need help at the cafeteria desk? "
        f"Contact {DESK_NAME} at {DESK_PHONE} "
        f"or {DESK_EMAIL}."
    )


# ============================================================
# STUDENT LOGIN
# ============================================================

def student_login_page():

    st.markdown("## 🎓 Student Login")

    if current_student():

        st.success(
            f"You are logged in as "
            f"{current_student().get('name', 'Student')}."
        )

        if st.button(
            "Go to Student Home"
        ):

            go_to("Home")

        return

    tab_login, tab_signup, tab_reset = st.tabs(
        [
            "Login",
            "Create Account",
            "Forgot Password",
        ]
    )

    # --------------------------------------------------------
    # LOGIN
    # --------------------------------------------------------

    with tab_login:

        st.markdown(
            "### Login to your account"
        )

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

                    uid = data["localId"]

                    st.session_state.auth_session = {
                        "id_token":
                            data["idToken"],
                        "refresh_token":
                            data["refreshToken"],
                        "login_time":
                            datetime.now().timestamp(),
                    }

                    profile = get_user_profile(
                        uid
                    )

                    if not profile:

                        st.warning(
                            "Login succeeded, but "
                            "your student profile was "
                            "not found."
                        )

                    else:

                        st.session_state.student_user = profile

                        st.session_state.page = "Home"

                        st.rerun()

    # --------------------------------------------------------
    # SIGNUP
    # --------------------------------------------------------

    with tab_signup:

        st.markdown(
            "### Create your student account"
        )

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
                        f"Could not create account: {error}"
                    )

                else:

                    uid = data["localId"]

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

                    st.session_state.student_user = (
                        get_user_profile(uid)
                    )

                    st.session_state.page = "Home"

                    st.success(
                        "Account created successfully!"
                    )

                    st.rerun()

    # --------------------------------------------------------
    # PASSWORD RESET
    # --------------------------------------------------------

    with tab_reset:

        st.markdown(
            "### Reset your password"
        )

        email = st.text_input(
            "Enter your account email",
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
                        f"Could not send reset email: {error}"
                    )

                else:

                    st.success(
                        "Password reset email sent. "
                        "Check your inbox."
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

            go_to("Student Login")

        return

    st.markdown("## 🍔 Order Food")

    menu = load_menu()

    available_items = [
        x
        for x in menu
        if x.get(
            "available",
            True,
        )
    ]

    if not available_items:

        st.warning(
            "No food items are currently available."
        )

        return

    popular = [
        x
        for x in available_items
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

                st.markdown(
                    f"""
                    <div class="card">
                        <h3>{item['name']}</h3>
                        <p>
                            ₹{effective_price(item):.0f}
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown(
        "### Menu"
    )

    for item in available_items:

        name = item["name"]

        price = effective_price(item)

        c1, c2, c3 = st.columns(
            [4, 1, 1]
        )

        with c1:

            discount = float(
                item.get(
                    "discount",
                    0,
                )
            )

            if discount > 0:

                st.write(
                    f"**{name}** — "
                    f"~~₹{item['price']}~~ "
                    f"₹{price:.0f}"
                )

            else:

                st.write(
                    f"**{name}** — "
                    f"₹{price:.0f}"
                )

        with c2:

            current = (
                st.session_state.cart
                .get(
                    name,
                    0,
                )
            )

            qty = st.number_input(
                "Qty",
                min_value=0,
                max_value=20,
                value=int(current),
                step=1,
                key=f"qty_{name}",
            )

            if qty == 0:

                st.session_state.cart.pop(
                    name,
                    None,
                )

            else:

                st.session_state.cart[
                    name
                ] = int(qty)

        with c3:

            st.write("")

    st.divider()

    cart = st.session_state.cart

    if not cart:

        st.info(
            "Your cart is empty. "
            "Select quantities above."
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

        item = menu_map.get(name)

        if item:

            line = (
                effective_price(item)
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

    order_mode = st.radio(
        "Order Type",
        [
            "Break Order",
            "Regular Order",
        ],
        horizontal=True,
    )

    break_time = None

    if order_mode == "Break Order":

        st.caption(
            "Choose the break period when "
            "you will collect your order."
        )

        break_time = st.selectbox(
            "Break Time",
            BREAK_OPTIONS,
        )

    else:

        st.info(
            "Regular orders are for "
            "Room / Hostel pre-order only. "
            "Estimated preparation time: "
            "10–15 minutes."
        )

    payment_method = st.radio(
        "Payment Method",
        [
            "Wallet",
            "Pay at Counter",
        ],
        horizontal=True,
    )

    wallet_balance = float(
        student.get(
            "wallet_balance",
            0,
        )
    )

    if payment_method == "Wallet":

        st.caption(
            f"Wallet balance: "
            f"₹{wallet_balance:.2f}"
        )

        if wallet_balance < total:

            st.warning(
                f"Insufficient wallet balance. "
                f"You need "
                f"₹{total - wallet_balance:.2f} more."
            )

    else:

        st.caption(
            "Pay the cafeteria desk "
            "when you collect your order."
        )

    if st.button(
        "Place Order",
        type="primary",
        use_container_width=True,
    ):

        if (
            payment_method == "Wallet"
            and wallet_balance < total
        ):

            st.error(
                "Insufficient wallet balance."
            )

            return

        ok, result = create_order(
            student,
            cart,
            order_mode,
            break_time,
            payment_method,
        )

        if not ok:

            st.error(
                f"Could not place order: {result}"
            )

            return

        st.session_state.last_order = result

        st.session_state.cart = {}

        st.session_state.page = (
            "Order Confirmation"
        )

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

        if st.button(
            "Order Food"
        ):

            go_to("Order Food")

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

    if order.get("break_time"):

        st.write(
            f"**Break:** "
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
            f"{item['name']} × "
            f"{item['quantity']} — "
            f"₹{item['line_total']:.0f}"
        )

    if (
        order.get("payment_method")
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

            go_to("My Orders")

    with c2:

        if st.button(
            "🍔 Order More",
            use_container_width=True,
        ):

            go_to("Order Food")


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

        if st.button(
            "Order Food"
        ):

            go_to("Order Food")

        return

    for order in orders[:20]:

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

            c1, c2, c3, c4 = st.columns(
                4
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
                    f"{order['break_time']}"
                )

            item_text = ", ".join(
                f"{x['name']} × "
                f"{x['quantity']}"
                for x in order.get(
                    "items",
                    [],
                )
            )

            st.write(item_text)

            if status != "Collected":

                st.info(
                    "Bring your Order ID to "
                    "the cafeteria desk for collection."
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
    )

    reason = st.text_input(
        "Reason",
        value="Cash deposited at cafeteria desk",
    )

    if st.button(
        "Add Wallet Money",
        type="primary",
    ):

        ok, result = add_wallet_money(
            student["uid"],
            amount,
            reason,
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
        "For the prototype, the cafeteria desk "
        "controls wallet credits."
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

    if st.button(
        "Submit Feedback",
        type="primary",
    ):

        if not message.strip():

            st.error(
                "Please enter your feedback."
            )

            return

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
                This portal is for cafeteria
                staff only.
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

            st.session_state.cafeteria_logged_in = True

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
        f"Desk: {DESK_NAME} | "
        f"Phone: {DESK_PHONE} | "
        f"Email: {DESK_EMAIL}"
    )

    orders = get_today_orders()

    total = len(orders)

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
        key="order_search",
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
    )

    filtered = []

    for order in orders:

        text = (
            f"{order.get('order_id', '')} "
            f"{order.get('student_name', '')} "
            f"{order.get('student_id', '')}"
        ).lower()

        if search.lower() not in text:
            continue

        if (
            status_filter != "All"
            and order.get("status")
            != status_filter
        ):

            continue

        filtered.append(order)

    for order in filtered:

        with st.container(
            border=True
        ):

            c1, c2, c3, c4 = st.columns(
                [1, 2.5, 1.5, 2]
            )

            with c1:

                st.markdown(
                    f"### #{order.get('order_id')}"
                )

            with c2:

                st.write(
                    f"**{order.get('student_name', '-') }**"
                )

                st.caption(
                    f"Student ID: "
                    f"{order.get('student_id', '-')}"
                )

            with c3:

                item_text = ", ".join(
                    f"{x['name']} × "
                    f"{x['quantity']}"
                    for x in order.get(
                        "items",
                        [],
                    )
                )

                st.write(
                    item_text
                )

                st.caption(
                    f"₹{order.get('total', 0):.0f}"
                )

            with c4:

                status = order.get(
                    "status",
                    "Confirmed",
                )

                payment_status = order.get(
                    "payment_status",
                    "Pending",
                )

                st.write(
                    f"**Status:** {status}"
                )

                st.write(
                    f"**Payment:** "
                    f"{payment_status}"
                )

                # Pay at counter
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
                        key=(
                            f"pay_"
                            f"{order.get('order_id')}"
                        ),
                    ):

                        ok, error = (
                            mark_counter_payment_received(
                                order
                            )
                        )

                        if ok:

                            st.success(
                                "Payment marked as received."
                            )

                            st.rerun()

                        else:

                            st.error(
                                error
                            )

                # Confirmed -> Preparing
                if status == "Confirmed":

                    if st.button(
                        "▶ Start Preparing",
                        key=(
                            f"prep_"
                            f"{order.get('order_id')}"
                        ),
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

                            st.error(error)

                # Preparing -> Ready
                elif status == "Preparing":

                    if st.button(
                        "✓ Mark Ready",
                        key=(
                            f"ready_"
                            f"{order.get('order_id')}"
                        ),
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

                            st.error(error)

                # Ready -> Collected
                elif status == "Ready":

                    if (
                        order.get(
                            "payment_method"
                        )
                        == "Pay at Counter"
                        and payment_status
                        != "Paid"
                    ):

                        st.warning(
                            "Collect payment "
                            "before handover."
                        )

                    else:

                        if st.button(
                            "📦 Mark Collected",
                            key=(
                                f"collect_"
                                f"{order.get('order_id')}"
                            ),
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

                                st.error(error)


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

    menu = load_menu()

    st.markdown(
        "### Add / Update Item"
    )

    name = st.text_input(
        "Item Name"
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

    if st.button(
        "Save Item",
        type="primary",
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

            save_menu_item(
                name.strip(),
                price,
                discount,
                available,
                popular,
            )

            st.success(
                "Menu item saved."
            )

            st.rerun()

    st.markdown(
        "### Current Menu"
    )

    for item in menu:

        c1, c2, c3, c4 = st.columns(
            [3, 1, 1, 1]
        )

        with c1:

            price_text = (
                f"₹{effective_price(item):.0f}"
            )

            if item.get(
                "discount",
                0,
            ):

                price_text += (
                    f" ({item.get('discount')}% off)"
                )

            st.write(
                f"**{item['name']}** — "
                f"{price_text}"
            )

        with c2:

            st.write(
                "Available"
                if item.get(
                    "available",
                    True,
                )
                else "Unavailable"
            )

        with c3:

            st.write(
                "⭐ Popular"
                if item.get(
                    "popular",
                    False,
                )
                else ""
            )

        with c4:

            if st.button(
                "Delete",
                key=f"delete_{item['name']}",
            ):

                delete_menu_item(
                    item["name"]
                )

                st.rerun()


# ============================================================
# CAFETERIA FEEDBACK
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

    docs = (
        db.collection("feedback")
        .stream()
    )

    feedback = [
        doc.to_dict()
        for doc in docs
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


st.success(
    "🟢 Firebase connected successfully",
    icon="🟢",
)

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


else:

    home_page()
