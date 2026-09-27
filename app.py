import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore, auth
from google.cloud.firestore_v1 import transactional
from datetime import datetime, date, timedelta
import requests
import json
import base64
import uuid


# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Campus Cafeteria",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

CAFETERIA_NAME = "Campus Cafeteria"
DESK_NAME = "Rahul"
DESK_PHONE = "9065334992"
DESK_EMAIL = "p46120@irma.ac.in"

# Temporary cafeteria password.
# Later you can put cafeteria_password in Streamlit Secrets.
CAFETERIA_PASSWORD = st.secrets.get(
    "cafeteria_password",
    "Rahul 123"
)

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


# =========================================================
# SOFT UI
# =========================================================

st.markdown("""
<style>

.main {
    background-color: #fafafa;
}

.block-container {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

h1, h2, h3 {
    color: #243447;
}

div[data-testid="stMetric"] {
    background-color: #f5f7fa;
    border: 1px solid #e5e9ef;
    padding: 12px;
    border-radius: 12px;
}

.stButton > button {
    border-radius: 9px;
}

div[data-testid="stExpander"] {
    border-radius: 12px;
}

.wallet-card {
    background: #eef7f1;
    border: 1px solid #cfe8d7;
    padding: 18px;
    border-radius: 14px;
    margin-bottom: 15px;
}

.order-card {
    background: #ffffff;
    border: 1px solid #e5e9ef;
    padding: 16px;
    border-radius: 14px;
    margin-bottom: 12px;
}

.warning-card {
    background: #fff8e6;
    border: 1px solid #f3df9a;
    padding: 15px;
    border-radius: 12px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# FIREBASE INITIALIZATION
# =========================================================

@st.cache_resource
def initialize_firebase():

    try:
        if not firebase_admin._apps:

            firebase_json = st.secrets["firebase_json"]

            if isinstance(firebase_json, str):
                service_account_info = json.loads(firebase_json)
            else:
                service_account_info = dict(firebase_json)

            cred = credentials.Certificate(service_account_info)

            firebase_admin.initialize_app(cred)

        db = firestore.client()

        return db, None

    except Exception as e:
        return None, str(e)


db, firebase_error = initialize_firebase()


if db is None:
    st.error("🔴 Firebase connection failed.")
    st.code(firebase_error)
    st.stop()


# =========================================================
# FIREBASE WEB API KEY
# =========================================================

FIREBASE_WEB_API_KEY = st.secrets.get(
    "firebase_web_api_key",
    ""
)


# =========================================================
# SESSION STATE
# =========================================================

DEFAULT_SESSION_VALUES = {
    "student_uid": None,
    "student_email": None,
    "student_id_token": None,
    "student_refresh_token": None,
    "student_token_time": None,
    "cafeteria_logged_in": False,
    "cart": {},
    "current_order": None,
    "page": "Home",
}

for key, value in DEFAULT_SESSION_VALUES.items():
    if key not in st.session_state:
        st.session_state[key] = value


# =========================================================
# HELPERS
# =========================================================

def today_string():
    return date.today().isoformat()


def now_string():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def money(value):
    return f"₹{float(value):,.2f}"


def safe_int(value, default=0):
    try:
        return int(value)
    except:
        return default


def safe_float(value, default=0):
    try:
        return float(value)
    except:
        return default


def image_to_base64(uploaded_file):
    if uploaded_file is None:
        return None

    try:
        raw = uploaded_file.getvalue()
        encoded = base64.b64encode(raw).decode("utf-8")
        return f"data:{uploaded_file.type};base64,{encoded}"
    except:
        return None


def get_discounted_price(item):
    price = safe_float(item.get("price", 0))
    discount = safe_float(item.get("discount", 0))

    discounted = price * (1 - discount / 100)

    return round(max(discounted, 0), 2)


def get_item_total(item, quantity):
    return round(get_discounted_price(item) * quantity, 2)


def get_order_items_text(order):
    items = order.get("items", {})

    parts = []

    for name, qty in items.items():
        parts.append(f"{name} × {qty}")

    return ", ".join(parts)


# =========================================================
# FIREBASE AUTH REST API
# =========================================================

def firebase_auth_request(endpoint, payload):
    if not FIREBASE_WEB_API_KEY:
        return {
            "error": {
                "message": "MISSING_FIREBASE_WEB_API_KEY"
            }
        }

    url = (
        "https://identitytoolkit.googleapis.com/v1/"
        f"{endpoint}?key={FIREBASE_WEB_API_KEY}"
    )

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=15
        )

        return response.json()

    except Exception as e:
        return {
            "error": {
                "message": str(e)
            }
        }


def firebase_signup(email, password):

    return firebase_auth_request(
        "accounts:signUp",
        {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
    )


def firebase_login(email, password):

    return firebase_auth_request(
        "accounts:signInWithPassword",
        {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
    )


def firebase_refresh_token(refresh_token):

    if not FIREBASE_WEB_API_KEY:
        return None

    url = (
        "https://securetoken.googleapis.com/v1/token"
        f"?key={FIREBASE_WEB_API_KEY}"
    )

    try:

        response = requests.post(
            url,
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token
            },
            timeout=15
        )

        data = response.json()

        if "id_token" in data:
            return data

        return None

    except:
        return None


def firebase_send_password_reset(email):

    return firebase_auth_request(
        "accounts:sendOobCode",
        {
            "requestType": "PASSWORD_RESET",
            "email": email
        }
    )


def firebase_error_message(data):

    if not data:
        return "Unknown authentication error."

    if "error" not in data:
        return ""

    message = data["error"].get("message", "")

    messages = {
        "EMAIL_EXISTS":
            "This email is already registered.",
        "EMAIL_NOT_FOUND":
            "No account exists with this email.",
        "INVALID_PASSWORD":
            "Incorrect password.",
        "INVALID_LOGIN_CREDENTIALS":
            "Incorrect email or password.",
        "USER_DISABLED":
            "This account has been disabled.",
        "WEAK_PASSWORD":
            "Password is too weak. Use at least 6 characters.",
        "OPERATION_NOT_ALLOWED":
            "Email/password authentication is not enabled in Firebase.",
        "TOO_MANY_ATTEMPTS_TRY_LATER":
            "Too many attempts. Please try again later.",
    }

    return messages.get(message, message)


# =========================================================
# AUTH SESSION
# =========================================================

def logout_student():

    st.session_state.student_uid = None
    st.session_state.student_email = None
    st.session_state.student_id_token = None
    st.session_state.student_refresh_token = None
    st.session_state.student_token_time = None
    st.session_state.cart = {}
    st.session_state.current_order = None

    st.rerun()


def set_student_session(data):

    st.session_state.student_uid = data.get("localId")
    st.session_state.student_email = data.get("email")
    st.session_state.student_id_token = data.get("idToken")
    st.session_state.student_refresh_token = data.get("refreshToken")
    st.session_state.student_token_time = datetime.now()


def get_logged_in_uid():

    uid = st.session_state.get("student_uid")

    token = st.session_state.get("student_id_token")

    if not uid or not token:
        return None

    # Refresh token after approximately 50 minutes.
    token_time = st.session_state.get("student_token_time")

    if token_time:

        age = datetime.now() - token_time

        if age.total_seconds() > 3000:

            refresh = firebase_refresh_token(
                st.session_state.get("student_refresh_token")
            )

            if refresh:

                st.session_state.student_id_token = refresh.get(
                    "id_token"
                )

                st.session_state.student_refresh_token = refresh.get(
                    "refresh_token",
                    st.session_state.student_refresh_token
                )

                st.session_state.student_token_time = datetime.now()

    try:

        decoded = auth.verify_id_token(
            st.session_state.student_id_token
        )

        return decoded.get("uid")

    except:

        # Token expired/invalid.
        st.session_state.student_uid = None
        st.session_state.student_email = None
        st.session_state.student_id_token = None

        return None


def current_user():

    uid = get_logged_in_uid()

    if not uid:
        return None

    try:

        ref = db.collection("users").document(uid)
        snap = ref.get()

        if not snap.exists:
            return None

        user = snap.to_dict()

        user["uid"] = uid

        return user

    except:
        return None


# =========================================================
# AUTH UI
# =========================================================

def login_signup_page():

    st.title("🍽️ Campus Cafeteria")

    st.write(
        "Login to order food, view your wallet and track your orders."
    )

    if not FIREBASE_WEB_API_KEY:

        st.error(
            "Firebase Web API Key is missing from Streamlit Secrets."
        )

        st.info(
            "Add `firebase_web_api_key` to your Streamlit Secrets."
        )

        return

    tab_login, tab_signup, tab_reset = st.tabs(
        [
            "🔐 Login",
            "🆕 Create Account",
            "🔑 Forgot Password"
        ]
    )

    # -----------------------------------------------------
    # LOGIN
    # -----------------------------------------------------

    with tab_login:

        st.subheader("Student Login")

        email = st.text_input(
            "Email",
            key="login_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "Login",
            type="primary",
            use_container_width=True
        ):

            if not email or not password:

                st.warning(
                    "Please enter both email and password."
                )

            else:

                result = firebase_login(
                    email.strip(),
                    password
                )

                if "idToken" in result:

                    set_student_session(result)

                    st.success("Login successful.")

                    st.rerun()

                else:

                    st.error(
                        firebase_error_message(result)
                    )

    # -----------------------------------------------------
    # SIGN UP
    # -----------------------------------------------------

    with tab_signup:

        st.subheader("Create Student Account")

        st.caption(
            "Use your college email if possible."
        )

        name = st.text_input(
            "Full Name",
            key="signup_name"
        )

        student_id = st.text_input(
            "Roll Number / Student ID",
            key="signup_student_id"
        )

        email = st.text_input(
            "Email",
            key="signup_email"
        )

        password = st.text_input(
            "Create Password",
            type="password",
            key="signup_password"
        )

        confirm = st.text_input(
            "Confirm Password",
            type="password",
            key="signup_confirm"
        )

        if st.button(
            "Create Account",
            type="primary",
            use_container_width=True
        ):

            if not name or not student_id or not email:

                st.warning(
                    "Please fill all account details."
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

                # Check if this student ID already exists.
                existing = (
                    db.collection("users")
                    .where(
                        "student_id",
                        "==",
                        student_id.strip()
                    )
                    .limit(1)
                    .stream()
                )

                existing_list = list(existing)

                if existing_list:

                    st.error(
                        "This Roll Number / Student ID is already registered."
                    )

                else:

                    result = firebase_signup(
                        email.strip(),
                        password
                    )

                    if "idToken" not in result:

                        st.error(
                            firebase_error_message(result)
                        )

                    else:

                        uid = result["localId"]

                        user_ref = (
                            db.collection("users")
                            .document(uid)
                        )

                        user_ref.set({
                            "uid": uid,
                            "name": name.strip(),
                            "student_id": student_id.strip(),
                            "email": email.strip().lower(),
                            "wallet_balance": 0.0,
                            "created_at": now_string()
                        })

                        set_student_session(result)

                        st.success(
                            "Account created successfully!"
                        )

                        st.rerun()

    # -----------------------------------------------------
    # RESET PASSWORD
    # -----------------------------------------------------

    with tab_reset:

        st.subheader("Reset Password")

        email = st.text_input(
            "Enter your registered email",
            key="reset_email"
        )

        if st.button(
            "Send Reset Email",
            use_container_width=True
        ):

            if not email:

                st.warning(
                    "Enter your email first."
                )

            else:

                result = firebase_send_password_reset(
                    email.strip()
                )

                if "error" in result:

                    st.error(
                        firebase_error_message(result)
                    )

                else:

                    st.success(
                        "Password reset email sent."
                    )


# =========================================================
# MENU
# =========================================================

def get_menu():

    try:

        docs = (
            db.collection("menu")
            .order_by("name")
            .stream()
        )

        menu = []

        for doc in docs:

            item = doc.to_dict()
            item["id"] = doc.id

            menu.append(item)

        if not menu:

            seed_default_menu()

            docs = (
                db.collection("menu")
                .order_by("name")
                .stream()
            )

            for doc in docs:

                item = doc.to_dict()
                item["id"] = doc.id

                menu.append(item)

        return menu

    except Exception as e:

        st.error(f"Could not load menu: {e}")

        return []


def seed_default_menu():

    default_items = [
        {
            "name": "Veg Roll",
            "price": 40,
            "discount": 0,
            "available": True,
            "popular": True,
            "photo": None
        },
        {
            "name": "Sandwich",
            "price": 40,
            "discount": 0,
            "available": True,
            "popular": True,
            "photo": None
        },
        {
            "name": "Tea",
            "price": 20,
            "discount": 0,
            "available": True,
            "popular": False,
            "photo": None
        },
        {
            "name": "Coffee",
            "price": 30,
            "discount": 0,
            "available": True,
            "popular": False,
            "photo": None
        },
        {
            "name": "Maggi",
            "price": 40,
            "discount": 0,
            "available": True,
            "popular": False,
            "photo": None
        },
    ]

    for item in default_items:

        db.collection("menu").add({
            **item,
            "created_at": now_string(),
            "updated_at": now_string()
        })


# =========================================================
# CART
# =========================================================

def add_to_cart(item):

    name = item["name"]

    if name not in st.session_state.cart:
        st.session_state.cart[name] = 0

    st.session_state.cart[name] += 1


def remove_from_cart(name):

    if name in st.session_state.cart:

        st.session_state.cart[name] -= 1

        if st.session_state.cart[name] <= 0:

            del st.session_state.cart[name]


def get_cart_items(menu):

    menu_map = {
        item["name"]: item
        for item in menu
    }

    result = []

    for name, qty in st.session_state.cart.items():

        if name in menu_map:

            result.append(
                (
                    menu_map[name],
                    qty
                )
            )

    return result


def calculate_cart_total(menu):

    total = 0

    for item, qty in get_cart_items(menu):

        total += get_item_total(
            item,
            qty
        )

    return round(total, 2)


# =========================================================
# DAILY ORDER NUMBER
# =========================================================

def get_next_order_id(transaction, counter_ref):

    snapshot = transaction.get(counter_ref)

    if snapshot.exists:

        data = snapshot.to_dict()

        next_number = safe_int(
            data.get("next_number", 1),
            1
        )

    else:

        next_number = 1

    transaction.set(
        counter_ref,
        {
            "next_number": next_number + 1,
            "date": today_string()
        },
        merge=True
    )

    return str(next_number).zfill(3)


# =========================================================
# CREATE ORDER
# =========================================================

@transactional
def create_order_transaction(
    transaction,
    user_ref,
    counter_ref,
    order_ref,
    order_data,
    total,
    payment_method
):

    user_snapshot = transaction.get(user_ref)

    if not user_snapshot.exists:

        raise Exception(
            "Student account not found."
        )

    user_data = user_snapshot.to_dict()

    current_balance = safe_float(
        user_data.get("wallet_balance", 0),
        0
    )

    # Wallet payment
    if payment_method == "Wallet":

        if current_balance < total:

            raise Exception(
                f"Insufficient wallet balance. "
                f"Available: {money(current_balance)}"
            )

        new_balance = round(
            current_balance - total,
            2
        )

        transaction.update(
            user_ref,
            {
                "wallet_balance": new_balance
            }
        )

        payment_status = "Paid"

    else:

        new_balance = current_balance

        payment_status = "Pending"

    order_id = get_next_order_id(
        transaction,
        counter_ref
    )

    final_order = {
        **order_data,

        "order_id": order_id,

        "payment_method": payment_method,

        "payment_status": payment_status,

        "wallet_balance_after": new_balance,

        "created_at": now_string(),

        "date": today_string(),

        "status": "Confirmed"
    }

    transaction.set(
        order_ref,
        final_order
    )

    return final_order


def place_order(
    user,
    menu,
    order_mode,
    break_time,
    payment_method
):

    if not st.session_state.cart:

        return None, "Your cart is empty."

    total = calculate_cart_total(menu)

    if total <= 0:

        return None, "Invalid order total."

    items = dict(
        st.session_state.cart
    )

    order_data = {
        "uid": user["uid"],
        "student_id": user.get("student_id", ""),
        "student_name": user.get("name", ""),
        "student_email": user.get("email", ""),

        "items": items,

        "total": total,

        "order_mode": order_mode,

        "break_time": break_time,

        "estimated_time": (
            "10–15 minutes"
            if order_mode == "Regular Order"
            else "Collect during selected break"
        ),

        "status": "Confirmed"
    }

    try:

        transaction = db.transaction()

        user_ref = (
            db.collection("users")
            .document(user["uid"])
        )

        counter_ref = (
            db.collection("counters")
            .document(today_string())
        )

        # Temporary unique document ID.
        # Actual order ID is generated transactionally.
        order_ref = (
            db.collection("orders")
            .document(
                f"{today_string()}_{uuid.uuid4().hex}"
            )
        )

        final_order = create_order_transaction(
            transaction,
            user_ref,
            counter_ref,
            order_ref,
            order_data,
            total,
            payment_method
        )

        st.session_state.cart = {}

        return final_order, None

    except Exception as e:

        return None, str(e)


# =========================================================
# STUDENT PORTAL
# =========================================================

def student_portal(user):

    st.title("🍽️ Student Portal")

    st.success(
        f"Welcome, {user.get('name', 'Student')}!"
    )

    # -----------------------------------------------------
    # WALLET
    # -----------------------------------------------------

    balance = safe_float(
        user.get("wallet_balance", 0),
        0
    )

    st.markdown(
        f"""
        <div class="wallet-card">
            <h3>💰 Cafeteria Wallet</h3>
            <h1>{money(balance)}</h1>
            <p>Use your prepaid balance to place orders.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # -----------------------------------------------------
    # MENU
    # -----------------------------------------------------

    menu = get_menu()

    st.subheader("🍴 Menu")

    available_items = [
        item
        for item in menu
        if item.get("available", True)
    ]

    if not available_items:

        st.warning(
            "No items are currently available."
        )

    cols = st.columns(3)

    for index, item in enumerate(available_items):

        with cols[index % 3]:

            with st.container(border=True):

                photo = item.get("photo")

                if photo:

                    try:

                        st.image(
                            photo,
                            use_container_width=True
                        )

                    except:
                        pass

                name = item["name"]

                price = safe_float(
                    item.get("price", 0)
                )

                discount = safe_float(
                    item.get("discount", 0)
                )

                final_price = get_discounted_price(
                    item
                )

                if item.get("popular"):

                    st.markdown(
                        "⭐ **Popular Pick**"
                    )

                st.markdown(
                    f"### {name}"
                )

                if discount > 0:

                    st.write(
                        f"~~₹{price:.0f}~~ "
                        f"**₹{final_price:.0f}** "
                        f"({discount:.0f}% off)"
                    )

                else:

                    st.write(
                        f"**₹{final_price:.0f}**"
                    )

                if st.button(
                    "Add",
                    key=f"add_{item['id']}",
                    use_container_width=True
                ):

                    add_to_cart(item)

                    st.toast(
                        f"{name} added to cart"
                    )

    # -----------------------------------------------------
    # CART
    # -----------------------------------------------------

    st.divider()

    st.subheader(
        f"🛒 Cart ({sum(st.session_state.cart.values())})"
    )

    cart_items = get_cart_items(menu)

    if not cart_items:

        st.info(
            "Your cart is empty."
        )

        return

    for item, qty in cart_items:

        col1, col2, col3, col4 = st.columns(
            [4, 1, 1, 1]
        )

        with col1:

            st.write(
                f"**{item['name']}**"
            )

        with col2:

            st.write(
                f"₹{get_discounted_price(item):.0f}"
            )

        with col3:

            st.write(
                f"× {qty}"
            )

        with col4:

            if st.button(
                "−",
                key=f"minus_{item['id']}"
            ):

                remove_from_cart(
                    item["name"]
                )

                st.rerun()

    total = calculate_cart_total(menu)

    st.markdown(
        f"### Total: {money(total)}"
    )

    # -----------------------------------------------------
    # ORDER TYPE
    # -----------------------------------------------------

    st.subheader("📦 Order Type")

    order_mode = st.radio(
        "Choose order type",
        [
            "Break Order",
            "Regular Order"
        ],
        horizontal=True
    )

    break_time = None

    if order_mode == "Break Order":

        break_time = st.selectbox(
            "Select collection break",
            BREAK_OPTIONS
        )

        st.info(
            "Your order will be prepared for the selected break. "
            "Once accepted, it will remain Confirmed until collection."
        )

    else:

        st.info(
            "Regular orders can be placed anytime, including during breaks. "
            "Estimated preparation time: 10–15 minutes."
        )

        st.caption(
            "Regular Order is for room / hostel pre-order."
        )

    # -----------------------------------------------------
    # PAYMENT
    # -----------------------------------------------------

    st.subheader("💳 Payment")

    payment_method = st.radio(
        "Choose payment method",
        [
            "Wallet",
            "Pay at Counter"
        ],
        format_func=lambda x: (
            f"💰 Wallet — {money(balance)} available"
            if x == "Wallet"
            else "💵 Pay at Counter / COD"
        )
    )

    if payment_method == "Wallet":

        if balance < total:

            st.warning(
                f"Insufficient wallet balance. "
                f"You need {money(total)} but have {money(balance)}."
            )

        else:

            st.success(
                f"After payment your balance will be "
                f"{money(balance - total)}."
            )

    else:

        st.warning(
            "Payment will be collected at the cafeteria counter. "
            "Your order will be recorded as Payment Pending."
        )

    # -----------------------------------------------------
    # PLACE ORDER
    # -----------------------------------------------------

    if st.button(
        "🍽️ Place Order",
        type="primary",
        use_container_width=True
    ):

        if (
            payment_method == "Wallet"
            and balance < total
        ):

            st.error(
                "Please recharge your wallet first."
            )

        else:

            final_order, error = place_order(
                user,
                menu,
                order_mode,
                break_time,
                payment_method
            )

            if error:

                st.error(error)

            else:

                st.session_state.current_order = (
                    final_order
                )

                st.success(
                    f"Order #{final_order['order_id']} placed!"
                )

                st.rerun()


# =========================================================
# ORDER CONFIRMATION
# =========================================================

def show_order_confirmation(order):

    if not order:
        return

    st.divider()

    st.success(
        f"Order #{order.get('order_id')} placed successfully!"
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "Order",
            f"#{order.get('order_id')}"
        )

    with col2:

        st.metric(
            "Total",
            money(order.get("total", 0))
        )

    with col3:

        st.metric(
            "Payment",
            order.get("payment_status", "Pending")
        )

    st.write(
        "**Items:**",
        get_order_items_text(order)
    )

    st.write(
        "**Order Status:**",
        order.get("status", "Confirmed")
    )

    if order.get("order_mode") == "Break Order":

        st.write(
            "**Collection Break:**",
            order.get("break_time")
        )

    else:

        st.write(
            "**Estimated preparation:**",
            "10–15 minutes"
        )

    if order.get("payment_method") == "Pay at Counter":

        st.warning(
            "Please pay at the cafeteria counter "
            "when collecting your order."
        )

    else:

        st.success(
            "Paid from your cafeteria wallet."
        )


# =========================================================
# TRACK MY ORDERS
# =========================================================

def track_orders(user):

    st.title("📍 My Orders")

    try:

        docs = (
            db.collection("orders")
            .where(
                "uid",
                "==",
                user["uid"]
            )
            .order_by(
                "created_at",
                direction=firestore.Query.DESCENDING
            )
            .limit(30)
            .stream()
        )

        orders = []

        for doc in docs:

            order = doc.to_dict()

            order["_doc_id"] = doc.id

            orders.append(order)

    except Exception:

        # Fallback if index/order query is unavailable.
        docs = (
            db.collection("orders")
            .where(
                "uid",
                "==",
                user["uid"]
            )
            .stream()
        )

        orders = []

        for doc in docs:

            order = doc.to_dict()

            order["_doc_id"] = doc.id

            orders.append(order)

        orders.sort(
            key=lambda x: x.get(
                "created_at",
                ""
            ),
            reverse=True
        )

        orders = orders[:30]

    if not orders:

        st.info(
            "You haven't placed any orders yet."
        )

        return

    for order in orders:

        with st.container(border=True):

            order_id = order.get(
                "order_id",
                "—"
            )

            st.markdown(
                f"### Order #{order_id}"
            )

            col1, col2, col3 = st.columns(3)

            with col1:

                st.write(
                    "**Items**"
                )

                st.write(
                    get_order_items_text(order)
                )

            with col2:

                st.write(
                    "**Order Status**"
                )

                st.write(
                    order.get(
                        "status",
                        "Confirmed"
                    )
                )

            with col3:

                st.write(
                    "**Payment**"
                )

                payment_status = order.get(
                    "payment_status",
                    "Pending"
                )

                payment_method = order.get(
                    "payment_method",
                    ""
                )

                st.write(
                    f"{payment_status}"
                )

                st.caption(
                    payment_method
                )

            st.write(
                f"**Total:** {money(order.get('total', 0))}"
            )

            if order.get("break_time"):

                st.write(
                    f"**Break:** {order['break_time']}"
                )

            if order.get("status") == "Collected":

                st.success(
                    "✅ Collected"
                )

            elif order.get("status") == "Ready":

                st.success(
                    "🟢 Ready for collection"
                )

            elif order.get("status") == "Preparing":

                st.warning(
                    "🟠 Being prepared"
                )

            else:

                st.info(
                    "🔵 Confirmed"
                )


# =========================================================
# FIND ORDER DOCUMENT
# =========================================================

def find_order_document(order):

    doc_id = order.get("_doc_id")

    if doc_id:

        ref = (
            db.collection("orders")
            .document(doc_id)
        )

        snap = ref.get()

        if snap.exists:

            return ref

    # New format fallback
    expected_id = (
        f"{order.get('date')}_{order.get('order_id')}"
    )

    ref = (
        db.collection("orders")
        .document(expected_id)
    )

    snap = ref.get()

    if snap.exists:

        return ref

    # Legacy fallback
    try:

        docs = (
            db.collection("orders")
            .where(
                "order_id",
                "==",
                order.get("order_id")
            )
            .where(
                "date",
                "==",
                order.get("date")
            )
            .limit(1)
            .stream()
        )

        for doc in docs:

            return doc.reference

    except:
        pass

    return None


# =========================================================
# UPDATE ORDER STATUS
# =========================================================

def update_order_status(order, new_status):

    try:

        ref = find_order_document(order)

        if ref is None:

            return False, "Order document not found."

        update_data = {
            "status": new_status,
            "updated_at": now_string()
        }

        if new_status == "Collected":

            if order.get("payment_method") == "Pay at Counter":

                update_data["payment_status"] = "Paid"

                update_data["payment_received_at"] = (
                    now_string()
                )

        ref.update(update_data)

        return True, None

    except Exception as e:

        return False, str(e)


def mark_payment_received(order):

    try:

        ref = find_order_document(order)

        if ref is None:

            return False, "Order document not found."

        ref.update({
            "payment_status": "Paid",
            "payment_received_at": now_string(),
            "updated_at": now_string()
        })

        return True, None

    except Exception as e:

        return False, str(e)


# =========================================================
# CAFETERIA LOGIN
# =========================================================

def cafeteria_login_page():

    st.title("🧑‍🍳 Cafeteria Portal")

    st.write(
        "Cafeteria desk access"
    )

    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button(
        "Login",
        type="primary",
        use_container_width=True
    ):

        if password == CAFETERIA_PASSWORD:

            st.session_state.cafeteria_logged_in = True

            st.success(
                "Cafeteria login successful."
            )

            st.rerun()

        else:

            st.error(
                "Incorrect password."
            )


# =========================================================
# CAFETERIA DASHBOARD
# =========================================================

def get_today_orders():

    try:

        docs = (
            db.collection("orders")
            .where(
                "date",
                "==",
                today_string()
            )
            .stream()
        )

        orders = []

        for doc in docs:

            order = doc.to_dict()

            order["_doc_id"] = doc.id

            orders.append(order)

        orders.sort(
            key=lambda x: x.get(
                "created_at",
                ""
            ),
            reverse=False
        )

        return orders

    except Exception as e:

        st.error(
            f"Could not load orders: {e}"
        )

        return []


def cafeteria_dashboard():

    st.title("🧑‍🍳 Cafeteria Portal")

    st.caption(
        f"Desk: {DESK_NAME} | "
        f"{DESK_PHONE} | "
        f"{DESK_EMAIL}"
    )

    orders = get_today_orders()

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

    # -----------------------------------------------------
    # METRICS
    # -----------------------------------------------------

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric(
        "📦 Total Orders",
        total_orders
    )

    c2.metric(
        "🔵 Confirmed",
        confirmed
    )

    c3.metric(
        "🟠 Preparing",
        preparing
    )

    c4.metric(
        "🟢 Ready",
        ready
    )

    c5.metric(
        "✅ Collected",
        collected
    )

    # -----------------------------------------------------
    # PAYMENT SUMMARY
    # -----------------------------------------------------

    st.subheader("💳 Payment Summary")

    pending_payment = sum(
        1
        for o in orders
        if o.get("payment_status") == "Pending"
    )

    paid_orders = sum(
        1
        for o in orders
        if o.get("payment_status") == "Paid"
    )

    p1, p2 = st.columns(2)

    p1.metric(
        "🟢 Paid",
        paid_orders
    )

    p2.metric(
        "🟠 Payment Pending",
        pending_payment
    )

    # -----------------------------------------------------
    # FILTER
    # -----------------------------------------------------

    st.subheader("📋 Today's Orders")

    search = st.text_input(
        "Search by Order ID, student name or roll number"
    )

    status_filter = st.selectbox(
        "Filter Status",
        [
            "All",
            "Confirmed",
            "Preparing",
            "Ready",
            "Collected"
        ]
    )

    payment_filter = st.selectbox(
        "Filter Payment",
        [
            "All",
            "Paid",
            "Pending"
        ]
    )

    filtered = []

    for order in orders:

        if search:

            search_text = (
                f"{order.get('order_id', '')} "
                f"{order.get('student_name', '')} "
                f"{order.get('student_id', '')}"
            ).lower()

            if search.lower() not in search_text:

                continue

        if (
            status_filter != "All"
            and order.get("status") != status_filter
        ):

            continue

        if (
            payment_filter != "All"
            and order.get("payment_status") != payment_filter
        ):

            continue

        filtered.append(order)

    if not filtered:

        st.info(
            "No matching orders."
        )

    # -----------------------------------------------------
    # ORDERS
    # -----------------------------------------------------

    for order in filtered:

        order_id = order.get(
            "order_id",
            "—"
        )

        status = order.get(
            "status",
            "Confirmed"
        )

        payment_status = order.get(
            "payment_status",
            "Pending"
        )

        with st.container(border=True):

            top1, top2, top3 = st.columns(
                [2, 4, 2]
            )

            with top1:

                st.markdown(
                    f"### #{order_id}"
                )

            with top2:

                st.write(
                    f"**{order.get('student_name', '')}** "
                    f"({order.get('student_id', '')})"
                )

                st.write(
                    get_order_items_text(order)
                )

            with top3:

                st.write(
                    f"**{money(order.get('total', 0))}**"
                )

                st.write(
                    f"Order: {status}"
                )

                if payment_status == "Paid":

                    st.success(
                        "💰 PAID"
                    )

                else:

                    st.warning(
                        "💵 PAYMENT PENDING"
                    )

            if order.get("break_time"):

                st.caption(
                    f"Break: {order['break_time']}"
                )

            # ---------------------------------------------
            # ACTIONS
            # ---------------------------------------------

            a1, a2, a3, a4 = st.columns(4)

            # Payment
            with a1:

                if (
                    order.get("payment_method")
                    == "Pay at Counter"
                    and payment_status != "Paid"
                ):

                    if st.button(
                        "💰 Mark Paid",
                        key=f"paid_{order_id}"
                    ):

                        ok, error = mark_payment_received(
                            order
                        )

                        if ok:

                            st.success(
                                "Payment marked as received."
                            )

                            st.rerun()

                        else:

                            st.error(error)

            # Preparing
            with a2:

                if (
                    status == "Confirmed"
                    and order.get("order_mode")
                    == "Regular Order"
                ):

                    if st.button(
                        "🟠 Preparing",
                        key=f"prep_{order_id}"
                    ):

                        ok, error = update_order_status(
                            order,
                            "Preparing"
                        )

                        if ok:

                            st.rerun()

                        else:

                            st.error(error)

            # Ready
            with a3:

                if status == "Preparing":

                    if st.button(
                        "🟢 Ready",
                        key=f"ready_{order_id}"
                    ):

                        ok, error = update_order_status(
                            order,
                            "Ready"
                        )

                        if ok:

                            st.rerun()

                        else:

                            st.error(error)

            # Collected
            with a4:

                if status in [
                    "Confirmed",
                    "Preparing",
                    "Ready"
                ]:

                    if st.button(
                        "✅ Collect",
                        key=f"collect_{order_id}"
                    ):

                        if (
                            order.get("payment_method")
                            == "Pay at Counter"
                            and payment_status != "Paid"
                        ):

                            st.error(
                                "Collect payment first."
                            )

                        else:

                            ok, error = update_order_status(
                                order,
                                "Collected"
                            )

                            if ok:

                                st.success(
                                    f"Order #{order_id} collected."
                                )

                                st.rerun()

                            else:

                                st.error(error)


# =========================================================
# WALLET MANAGEMENT
# =========================================================

def search_students(query):

    query = query.strip().lower()

    if not query:

        return []

    try:

        docs = (
            db.collection("users")
            .stream()
        )

        students = []

        for doc in docs:

            data = doc.to_dict()

            searchable = " ".join([
                str(data.get("name", "")),
                str(data.get("student_id", "")),
                str(data.get("email", ""))
            ]).lower()

            if query in searchable:

                data["uid"] = doc.id

                students.append(data)

        return students

    except:

        return []


def add_wallet_money(uid, amount, reason):

    if amount <= 0:

        return False, "Amount must be greater than zero."

    try:

        transaction = db.transaction()

        user_ref = (
            db.collection("users")
            .document(uid)
        )

        wallet_log_ref = (
            db.collection("wallet_transactions")
            .document()
        )

        @transactional
        def update_wallet(
            transaction,
            user_ref,
            wallet_log_ref
        ):

            snapshot = transaction.get(
                user_ref
            )

            if not snapshot.exists:

                raise Exception(
                    "Student not found."
                )

            data = snapshot.to_dict()

            old_balance = safe_float(
                data.get("wallet_balance", 0),
                0
            )

            new_balance = round(
                old_balance + amount,
                2
            )

            transaction.update(
                user_ref,
                {
                    "wallet_balance": new_balance
                }
            )

            transaction.set(
                wallet_log_ref,
                {
                    "uid": uid,
                    "type": "Credit",
                    "amount": amount,
                    "balance_after": new_balance,
                    "reason": reason,
                    "created_at": now_string(),
                    "date": today_string()
                }
            )

            return new_balance

        new_balance = update_wallet(
            transaction,
            user_ref,
            wallet_log_ref
        )

        return True, new_balance

    except Exception as e:

        return False, str(e)


def wallet_management():

    st.subheader("💰 Wallet / Coupon Management")

    st.info(
        "When a student deposits money at the cafeteria, "
        "use this section to credit their wallet."
    )

    query = st.text_input(
        "Search student by Roll Number, Name or Email"
    )

    students = search_students(query)

    if query and not students:

        st.warning(
            "No student found."
        )

    for student in students:

        with st.container(border=True):

            st.write(
                f"**{student.get('name')}**"
            )

            st.write(
                f"Roll No: {student.get('student_id')}"
            )

            st.write(
                f"Email: {student.get('email')}"
            )

            st.write(
                f"Current Wallet: "
                f"**{money(student.get('wallet_balance', 0))}**"
            )

            amount = st.number_input(
                "Deposit Amount",
                min_value=1.0,
                step=50.0,
                value=500.0,
                key=f"wallet_amount_{student['uid']}"
            )

            reason = st.text_input(
                "Reason",
                value="Cafeteria Deposit",
                key=f"wallet_reason_{student['uid']}"
            )

            if st.button(
                "➕ Add Money",
                key=f"wallet_add_{student['uid']}",
                type="primary"
            ):

                ok, result = add_wallet_money(
                    student["uid"],
                    amount,
                    reason
                )

                if ok:

                    st.success(
                        f"Wallet updated. "
                        f"New balance: {money(result)}"
                    )

                    st.rerun()

                else:

                    st.error(
                        str(result)
                    )


# =========================================================
# WALLET HISTORY
# =========================================================

def wallet_history():

    st.subheader("📜 Wallet Transactions")

    try:

        docs = (
            db.collection("wallet_transactions")
            .order_by(
                "created_at",
                direction=firestore.Query.DESCENDING
            )
            .limit(100)
            .stream()
        )

        records = []

        for doc in docs:

            data = doc.to_dict()

            records.append(data)

        if not records:

            st.info(
                "No wallet transactions yet."
            )

            return

        for record in records:

            amount = safe_float(
                record.get("amount", 0)
            )

            transaction_type = record.get(
                "type",
                ""
            )

            symbol = (
                "+"
                if transaction_type == "Credit"
                else "-"
            )

            st.write(
                f"**{record.get('date', '')}** | "
                f"{record.get('uid', '')[:8]}... | "
                f"{symbol}{money(amount)} | "
                f"{record.get('reason', '')} | "
                f"Balance: {money(record.get('balance_after', 0))}"
            )

    except Exception as e:

        st.error(
            f"Could not load wallet history: {e}"
        )


# =========================================================
# MENU MANAGEMENT
# =========================================================

def menu_management():

    st.subheader("🍴 Menu Management")

    menu = get_menu()

    # -----------------------------------------------------
    # ADD ITEM
    # -----------------------------------------------------

    with st.expander(
        "➕ Add New Item",
        expanded=False
    ):

        name = st.text_input(
            "Item Name",
            key="new_item_name"
        )

        price = st.number_input(
            "Price",
            min_value=0.0,
            step=5.0,
            key="new_item_price"
        )

        discount = st.number_input(
            "Discount %",
            min_value=0.0,
            max_value=100.0,
            step=1.0,
            key="new_item_discount"
        )

        popular = st.checkbox(
            "⭐ Popular Pick",
            key="new_item_popular"
        )

        available = st.checkbox(
            "Available",
            value=True,
            key="new_item_available"
        )

        photo = st.file_uploader(
            "Food Photo",
            type=[
                "jpg",
                "jpeg",
                "png",
                "webp"
            ],
            key="new_item_photo"
        )

        if st.button(
            "Add Item",
            type="primary"
        ):

            if not name.strip():

                st.warning(
                    "Enter an item name."
                )

            else:

                db.collection("menu").add({
                    "name": name.strip(),
                    "price": price,
                    "discount": discount,
                    "popular": popular,
                    "available": available,
                    "photo": image_to_base64(photo),
                    "created_at": now_string(),
                    "updated_at": now_string()
                })

                st.success(
                    "Item added."
                )

                st.rerun()

    # -----------------------------------------------------
    # EXISTING ITEMS
    # -----------------------------------------------------

    st.write(
        "### Existing Items"
    )

    for item in menu:

        with st.container(border=True):

            st.markdown(
                f"### {item.get('name', '')}"
            )

            photo = item.get("photo")

            if photo:

                try:

                    st.image(
                        photo,
                        width=180
                    )

                except:
                    pass

            col1, col2, col3 = st.columns(3)

            with col1:

                price = st.number_input(
                    "Price",
                    min_value=0.0,
                    value=float(
                        item.get("price", 0)
                    ),
                    step=5.0,
                    key=f"price_{item['id']}"
                )

            with col2:

                discount = st.number_input(
                    "Discount %",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(
                        item.get("discount", 0)
                    ),
                    step=1.0,
                    key=f"discount_{item['id']}"
                )

            with col3:

                available = st.checkbox(
                    "Available",
                    value=item.get(
                        "available",
                        True
                    ),
                    key=f"available_{item['id']}"
                )

            popular = st.checkbox(
                "⭐ Popular Pick",
                value=item.get(
                    "popular",
                    False
                ),
                key=f"popular_{item['id']}"
            )

            new_photo = st.file_uploader(
                "Change Food Photo",
                type=[
                    "jpg",
                    "jpeg",
                    "png",
                    "webp"
                ],
                key=f"photo_{item['id']}"
            )

            b1, b2 = st.columns(2)

            with b1:

                if st.button(
                    "💾 Save Changes",
                    key=f"save_{item['id']}"
                ):

                    update = {
                        "price": price,
                        "discount": discount,
                        "available": available,
                        "popular": popular,
                        "updated_at": now_string()
                    }

                    if new_photo:

                        update["photo"] = (
                            image_to_base64(
                                new_photo
                            )
                        )

                    db.collection(
                        "menu"
                    ).document(
                        item["id"]
                    ).update(update)

                    st.success(
                        "Updated."
                    )

                    st.rerun()

            with b2:

                if st.button(
                    "🗑️ Remove Item",
                    key=f"delete_{item['id']}"
                ):

                    db.collection(
                        "menu"
                    ).document(
                        item["id"]
                    ).delete()

                    st.success(
                        "Item removed."
                    )

                    st.rerun()


# =========================================================
# FEEDBACK
# =========================================================

def feedback_page(user):

    st.title("💬 Feedback")

    st.write(
        "Tell us about your cafeteria experience."
    )

    rating = st.slider(
        "Rating",
        1,
        5,
        5
    )

    feedback = st.text_area(
        "Your feedback"
    )

    order_id = st.text_input(
        "Order ID (optional)"
    )

    photo = st.file_uploader(
        "Upload Photo (optional)",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp"
        ]
    )

    if st.button(
        "Submit Feedback",
        type="primary"
    ):

        if not feedback.strip():

            st.warning(
                "Please write some feedback."
            )

        else:

            db.collection(
                "feedback"
            ).add({
                "uid": user["uid"],
                "student_id": user.get(
                    "student_id",
                    ""
                ),
                "student_name": user.get(
                    "name",
                    ""
                ),
                "order_id": order_id.strip(),
                "rating": rating,
                "feedback": feedback.strip(),
                "photo": image_to_base64(photo),
                "date": today_string(),
                "created_at": now_string()
            })

            st.success(
                "Thank you for your feedback!"
            )


# =========================================================
# CLEANUP 14 DAYS
# =========================================================

def delete_old_data():

    cutoff = date.today() - timedelta(
        days=14
    )

    cutoff_string = cutoff.isoformat()

    deleted_orders = 0
    deleted_feedback = 0

    try:

        orders = (
            db.collection("orders")
            .stream()
        )

        for doc in orders:

            data = doc.to_dict()

            record_date = data.get(
                "date",
                ""
            )

            if record_date and record_date < cutoff_string:

                doc.reference.delete()

                deleted_orders += 1

    except:
        pass

    try:

        feedback_docs = (
            db.collection("feedback")
            .stream()
        )

        for doc in feedback_docs:

            data = doc.to_dict()

            record_date = data.get(
                "date",
                ""
            )

            if record_date and record_date < cutoff_string:

                doc.reference.delete()

                deleted_feedback += 1

    except:
        pass

    return deleted_orders, deleted_feedback


# =========================================================
# DATA MANAGEMENT
# =========================================================

def data_management():

    st.subheader(
        "🧹 Data Management"
    )

    st.warning(
        "This manually deletes Orders and Feedback "
        "older than 14 days. Menu and student accounts "
        "are not deleted."
    )

    confirm = st.checkbox(
        "I understand that old orders and feedback will be deleted."
    )

    if st.button(
        "Delete Data Older Than 14 Days",
        type="primary",
        disabled=not confirm
    ):

        orders_deleted, feedback_deleted = (
            delete_old_data()
        )

        st.success(
            f"Deleted {orders_deleted} old orders "
            f"and {feedback_deleted} old feedback records."
        )


# =========================================================
# CAFETERIA PORTAL
# =========================================================

def cafeteria_portal():

    if not st.session_state.cafeteria_logged_in:

        cafeteria_login_page()

        return

    st.title("🧑‍🍳 Cafeteria Portal")

    if st.button(
        "Logout Cafeteria",
        key="cafeteria_logout"
    ):

        st.session_state.cafeteria_logged_in = False

        st.rerun()

    tabs = st.tabs([
        "📋 Orders",
        "💰 Wallet",
        "📜 Wallet History",
        "🍴 Menu",
        "🧹 Data Management"
    ])

    with tabs[0]:

        cafeteria_dashboard()

    with tabs[1]:

        wallet_management()

    with tabs[2]:

        wallet_history()

    with tabs[3]:

        menu_management()

    with tabs[4]:

        data_management()


# =========================================================
# HOME
# =========================================================

def home_page():

    st.title("🍽️ Campus Cafeteria")

    st.subheader(
        "Pre-order your food. Skip the queue."
    )

    st.write(
        "Order during class, choose your break, "
        "or place a regular room/hostel pre-order."
    )

    st.divider()

    c1, c2, c3 = st.columns(3)

    with c1:

        st.markdown(
            "### 🛒 Pre-order"
        )

        st.write(
            "Place your order before reaching the cafeteria."
        )

    with c2:

        st.markdown(
            "### 💰 Wallet"
        )

        st.write(
            "Deposit money once and use it for multiple orders."
        )

    with c3:

        st.markdown(
            "### ⚡ Quick Collection"
        )

        st.write(
            "Show your Order ID at the cafeteria desk."
        )

    st.divider()

    st.info(
        "Students need to log in to place orders, "
        "use their wallet and view their orders."
    )


# =========================================================
# SIDEBAR
# =========================================================

def sidebar():

    st.sidebar.title(
        "🍽️ Campus Cafeteria"
    )

    user = current_user()

    if user:

        st.sidebar.success(
            f"Logged in as {user.get('name', 'Student')}"
        )

        st.sidebar.caption(
            user.get("email", "")
        )

        st.sidebar.write(
            f"💰 Wallet: "
            f"**{money(user.get('wallet_balance', 0))}**"
        )

        page_options = [
            "Home",
            "Student Portal",
            "My Orders",
            "Feedback",
            "Cafeteria Portal"
        ]

        page = st.sidebar.radio(
            "Go to",
            page_options,
            key="main_navigation"
        )

        if st.sidebar.button(
            "Logout Student"
        ):

            logout_student()

        return page, user

    else:

        page = st.sidebar.radio(
            "Go to",
            [
                "Home",
                "Student Login",
                "Cafeteria Portal"
            ],
            key="guest_navigation"
        )

        return page, None


# =========================================================
# MAIN APP
# =========================================================

page, user = sidebar()


if page == "Home":

    home_page()


elif page == "Student Login":

    login_signup_page()


elif page == "Student Portal":

    if user:

        student_portal(user)

        if st.session_state.current_order:

            show_order_confirmation(
                st.session_state.current_order
            )

    else:

        login_signup_page()


elif page == "My Orders":

    if user:

        track_orders(user)

    else:

        login_signup_page()


elif page == "Feedback":

    if user:

        feedback_page(user)

    else:

        login_signup_page()


elif page == "Cafeteria Portal":

    cafeteria_portal()
