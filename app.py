import base64
import json
import uuid
from datetime import date, datetime, timedelta

import requests
import streamlit as st
import firebase_admin
from firebase_admin import auth, credentials, firestore
from google.cloud.firestore_v1 import transactional

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
    {"name": "Veg Roll", "price": 40, "available": True, "discount": 0, "popular": True},
    {"name": "Maggi", "price": 40, "available": True, "discount": 0, "popular": True},
    {"name": "Sandwich", "price": 50, "available": True, "discount": 0, "popular": True},
    {"name": "Samosa", "price": 15, "available": True, "discount": 0, "popular": False},
    {"name": "Tea", "price": 20, "available": True, "discount": 0, "popular": True},
    {"name": "Coffee", "price": 30, "available": True, "discount": 0, "popular": False},
    {"name": "Cold Drink", "price": 30, "available": True, "discount": 0, "popular": False},
]

# These are the old random document IDs created during testing.
# They are mapped to the names that were already established in the app.
LEGACY_MENU_NAME_MAP = {
    "4u3FCDLEIKKmeQcLXdnW": "Veg Roll",
    "Ulp0Yd6IZvOYMRxUeRof": "Maggi",
    "0z3xzZZH7Yajbkpa03fb": "Tea",
    "pI7CfsYLvEocPU1n2RTx": "Sandwich",
}

# ============================================================
# STYLING
# ============================================================

st.markdown(
    """
<style>
.stApp { background: linear-gradient(180deg,#f8fafc 0%,#f7f8fc 55%,#ffffff 100%); }
.block-container { padding-top: .65rem; padding-bottom: 3rem; max-width: 1400px; }
.app-brand {
    display:flex; align-items:center; gap:.55rem;
    padding:.65rem .9rem; margin-bottom:.7rem;
    border-radius:18px;
    background:linear-gradient(135deg,#ffffff 0%,#f8fafc 60%,#eef6ff 100%);
    border:1px solid #e2e8f0;
    box-shadow:0 5px 18px rgba(15,23,42,.045);
}
.app-brand-icon { font-size:1.7rem; }
.app-brand-name { font-size:1.35rem; font-weight:800; color:#1f2937; }
div[data-testid="stHorizontalBlock"] button {
    border-radius:13px;
    border:1px solid #dbe2ea;
    background:#ffffff;
    transition:all .15s ease;
}
div[data-testid="stHorizontalBlock"] button:hover {
    border-color:#93c5fd;
    box-shadow:0 4px 12px rgba(59,130,246,.10);
}

.hero {
    padding: 2rem;
    border-radius: 24px;
    background: linear-gradient(135deg,#fff7ed 0%,#ffffff 55%,#eff6ff 100%);
    border: 1px solid #e5e7eb;
    margin-bottom: 1.2rem;
}
.hero-title { font-size: 2.45rem; font-weight: 800; color:#111827; margin:0; }
.hero-sub { font-size:1.05rem; color:#4b5563; margin-top:.55rem; }
.card {
    background:#fff; border:1px solid #e5e7eb; border-radius:18px;
    padding:1.1rem; box-shadow:0 2px 8px rgba(0,0,0,.035);
}
.card-title { font-size:1.08rem; font-weight:700; color:#111827; margin-bottom:.35rem; }
.card-text { color:#6b7280; margin:0; }
.order-id {
    font-size:2.1rem; font-weight:900; color:#111827; text-align:center;
}
.success-box {
    padding:1rem 1.2rem; border-radius:18px;
    background:#ecfdf5; border:1px solid #a7f3d0;
}
.warning-box {
    padding:1rem 1.2rem; border-radius:18px;
    background:#fffbeb; border:1px solid #fde68a;
}
div[data-testid="stMetric"] {
    background:white; border:1px solid #e5e7eb;
    padding:12px; border-radius:16px;
    box-shadow:0 5px 16px rgba(15,23,42,.055);
}
.dashboard-title {
    padding:1.45rem 1.55rem;
    border-radius:24px;
    background:linear-gradient(135deg,#dbeafe 0%,#ffffff 45%,#fef3c7 100%);
    border:1px solid #dbeafe;
    margin-bottom:1rem;
    box-shadow:0 8px 24px rgba(15,23,42,.07);
}
.dashboard-title h2 { margin:0; color:#111827; font-size:1.85rem; }
.dashboard-title p { margin:.35rem 0 0; color:#64748b; font-size:.98rem; }
.dashboard-chip {
    display:inline-block; margin-top:.75rem; padding:.35rem .75rem;
    border-radius:999px; background:rgba(255,255,255,.85);
    border:1px solid #cbd5e1; color:#475569; font-size:.82rem; font-weight:650;
}
.section-title { font-size:1.3rem; font-weight:800; color:#111827; margin:1.1rem 0 .55rem; }
.dashboard-subtitle { color:#64748b; font-size:.9rem; margin-top:-.3rem; margin-bottom:.7rem; }
.topup-empty {
    padding:1rem 1.1rem; border-radius:16px; background:#ecfdf5;
    border:1px solid #bbf7d0; color:#166534; font-weight:650;
}
.order-card-label { color:#64748b; font-size:.76rem; text-transform:uppercase; letter-spacing:.04em; margin-bottom:.15rem; }
.order-card-id { font-size:1.35rem; font-weight:850; color:#1d4ed8; }
.payment-paid { color:#15803d; font-weight:700; }
.payment-pending { color:#c2410c; font-weight:700; }
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
        raw = st.secrets.get("firebase_json")
        if not raw:
            raise RuntimeError("firebase_json is missing from Streamlit Secrets.")

        if isinstance(raw, str):
            raw = json.loads(raw)

        firebase_admin.initialize_app(credentials.Certificate(raw))

    return firestore.client()


try:
    db = init_firebase()
    firebase_connected = True
    firebase_error = ""
except Exception as exc:
    db = None
    firebase_connected = False
    firebase_error = str(exc)


def web_api_key():
    return st.secrets.get("firebase_web_api_key", "")


# ============================================================
# FIREBASE AUTH REST
# ============================================================

def auth_request(endpoint, payload):
    key = web_api_key()
    if not key:
        return None, "Firebase Web API Key is missing from Streamlit Secrets."

    url = f"https://identitytoolkit.googleapis.com/v1/{endpoint}?key={key}"
    try:
        response = requests.post(url, json=payload, timeout=20)
        data = response.json()
        if response.ok:
            return data, None
        return None, data.get("error", {}).get("message", "Authentication failed.")
    except Exception as exc:
        return None, str(exc)


def signup_student(email, password):
    return auth_request(
        "accounts:signUp",
        {"email": email, "password": password, "returnSecureToken": True},
    )


def login_student(email, password):
    return auth_request(
        "accounts:signInWithPassword",
        {"email": email, "password": password, "returnSecureToken": True},
    )


def send_password_reset(email):
    return auth_request(
        "accounts:sendOobCode",
        {"requestType": "PASSWORD_RESET", "email": email},
    )


def refresh_id_token(refresh_token):
    key = web_api_key()
    if not key:
        return None, "Firebase Web API Key is missing."

    url = f"https://securetoken.googleapis.com/v1/token?key={key}"
    try:
        response = requests.post(
            url,
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
            timeout=20,
        )
        data = response.json()
        if response.ok:
            return data, None
        return None, data.get("error", {}).get("message", "Could not refresh session.")
    except Exception as exc:
        return None, str(exc)


def get_logged_in_uid():
    session = st.session_state.get("auth_session")
    if not session:
        return None

    try:
        if datetime.now().timestamp() - session.get("login_time", 0) > 3000:
            refreshed, error = refresh_id_token(session["refresh_token"])
            if error:
                raise RuntimeError(error)
            session["id_token"] = refreshed["id_token"]
            session["refresh_token"] = refreshed["refresh_token"]
            session["login_time"] = datetime.now().timestamp()
            st.session_state.auth_session = session

        decoded = auth.verify_id_token(session["id_token"])
        return decoded["uid"]
    except Exception:
        st.session_state.pop("auth_session", None)
        st.session_state.pop("student_user", None)
        return None


# ============================================================
# USER PROFILES
# ============================================================

def get_user_profile(uid):
    if not db:
        return None
    snap = db.collection("users").document(uid).get()
    return snap.to_dict() if snap.exists else None


def save_user_profile(uid, name, student_id, email):
    db.collection("users").document(uid).set(
        {
            "name": name.strip(),
            "student_id": student_id.strip(),
            "email": email.strip().lower(),
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
# MENU HELPERS
# ============================================================

def _legacy_fallback_name(doc_id, used_names):
    if doc_id in LEGACY_MENU_NAME_MAP:
        return LEGACY_MENU_NAME_MAP[doc_id]

    # Never use the random Firestore ID as a visible menu name.
    base = "Food Item"
    if base not in used_names:
        return base

    number = 2
    while f"{base} {number}" in used_names:
        number += 1
    return f"{base} {number}"


def load_menu():
    if not db:
        return [dict(x) for x in DEFAULT_MENU]

    docs = list(db.collection("menu").stream())

    if not docs:
        for item in DEFAULT_MENU:
            db.collection("menu").document(item["name"]).set(item)
        return [dict(x) for x in DEFAULT_MENU]

    menu = []
    used_names = set()

    for doc in docs:
        data = doc.to_dict() or {}
        stored_name = str(data.get("name", "")).strip()
        name = stored_name or _legacy_fallback_name(doc.id, used_names)

        # If an old record has no name, persist the clean display name.
        if not stored_name:
            db.collection("menu").document(doc.id).set(
                {"name": name},
                merge=True,
            )

        used_names.add(name)
        item = dict(data)
        item["name"] = name
        item["_doc_id"] = doc.id
        item.setdefault("price", 0)
        item.setdefault("available", True)
        item.setdefault("discount", 0)
        item.setdefault("popular", False)
        menu.append(item)

    return sorted(menu, key=lambda x: str(x["name"]).lower())


def effective_price(item):
    price = float(item.get("price", 0))
    discount = float(item.get("discount", 0))
    return max(0, round(price * (1 - discount / 100), 2))


def save_menu_item(name, price, discount, available, popular, old_doc_id=None):
    name = name.strip()
    target_id = old_doc_id or name

    payload = {
        "name": name,
        "price": float(price),
        "discount": float(discount),
        "available": bool(available),
        "popular": bool(popular),
    }

    db.collection("menu").document(target_id).set(payload, merge=True)

    # If renaming a legacy document, keep only the renamed record.
    if old_doc_id and old_doc_id != name:
        db.collection("menu").document(old_doc_id).delete()


def delete_menu_item(item):
    doc_id = item.get("_doc_id", item.get("name"))
    db.collection("menu").document(doc_id).delete()


# ============================================================
# IMAGE HELPERS
# ============================================================

def image_to_base64(uploaded_file, max_bytes=500_000):
    if uploaded_file is None:
        return None
    raw = uploaded_file.getvalue()
    if len(raw) > max_bytes:
        raise ValueError("Image is too large. Please upload an image below 500 KB.")
    return base64.b64encode(raw).decode("utf-8")


def decode_menu_image(item):
    """Decode the existing stored menu photo without changing how images are stored."""
    encoded = item.get("photo_base64") if isinstance(item, dict) else None
    if not encoded:
        return None
    try:
        return base64.b64decode(encoded)
    except Exception:
        return None


# ============================================================
# ORDER HELPERS
# ============================================================

def normalize_items(raw_items):
    if isinstance(raw_items, dict):
        return [
            {"name": str(name), "quantity": int(qty), "unit_price": 0, "line_total": 0}
            for name, qty in raw_items.items()
        ]

    if isinstance(raw_items, list):
        result = []
        for item in raw_items:
            if isinstance(item, dict):
                result.append(
                    {
                        "name": str(item.get("name", "Item")),
                        "quantity": int(item.get("quantity", 1)),
                        "unit_price": float(item.get("unit_price", 0)),
                        "line_total": float(item.get("line_total", 0)),
                    }
                )
            else:
                result.append(
                    {"name": str(item), "quantity": 1, "unit_price": 0, "line_total": 0}
                )
        return result

    if raw_items in (None, ""):
        return []

    return [{"name": str(raw_items), "quantity": 1, "unit_price": 0, "line_total": 0}]


def items_text(raw_items):
    normalized = normalize_items(raw_items)
    return ", ".join(
        f"{item['name']} × {item['quantity']}" for item in normalized
    ) or "—"


def order_sort_key(order):
    try:
        return int(str(order.get("order_id", "0")))
    except Exception:
        return 0


def timestamp_sort_key(value):
    if value is None:
        return 0
    if hasattr(value, "timestamp"):
        try:
            return value.timestamp()
        except Exception:
            pass
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0


def find_order_document(order):
    order_id = str(order.get("order_id", ""))
    order_date = str(order.get("date", date.today().isoformat()))

    direct = db.collection("orders").document(f"{order_date}_{order_id}")
    if direct.get().exists:
        return direct

    for doc in (
        db.collection("orders")
        .where("order_id", "==", order_id)
        .where("date", "==", order_date)
        .limit(1)
        .stream()
    ):
        return doc.reference

    for doc in (
        db.collection("orders")
        .where("order_id", "==", order_id)
        .limit(1)
        .stream()
    ):
        return doc.reference

    return None


def update_order_status(order, new_status):
    ref = find_order_document(order)
    if not ref:
        return False, "Order document not found."
    ref.update(
        {"status": new_status, "updated_at": firestore.SERVER_TIMESTAMP}
    )
    return True, None


def mark_counter_payment_received(order):
    ref = find_order_document(order)
    if not ref:
        return False, "Order document not found."
    ref.update(
        {
            "payment_status": "Paid",
            "payment_method": "Pay at Counter",
            "payment_received_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }
    )
    return True, None


def get_today_orders():
    if not db:
        return []

    today = date.today().isoformat()
    docs = db.collection("orders").where("date", "==", today).stream()
    orders = [dict(doc.to_dict() or {}, _doc_id=doc.id) for doc in docs]
    return sorted(orders, key=order_sort_key)


def get_student_orders(uid):
    if not db:
        return []

    docs = db.collection("orders").where("uid", "==", uid).stream()
    orders = [dict(doc.to_dict() or {}, _doc_id=doc.id) for doc in docs]
    return sorted(
        orders,
        key=lambda x: timestamp_sort_key(x.get("created_at")),
        reverse=True,
    )


# ============================================================
# ORDER CREATION + WALLET
# ============================================================

def create_order(student, cart, order_type, break_time, payment_method):
    if not cart:
        return False, "Your cart is empty."

    uid = student["uid"]
    today = date.today().isoformat()
    user_ref = db.collection("users").document(uid)
    counter_ref = db.collection("counters").document(today)

    menu = {item["name"]: item for item in load_menu()}

    items = []
    total = 0.0

    for name, quantity in cart.items():
        quantity = int(quantity)
        if quantity <= 0:
            continue

        item = menu.get(name)
        if not item:
            return False, f"{name} is no longer available."

        if not item.get("available", True):
            return False, f"{name} is currently unavailable."

        price = effective_price(item)
        line_total = round(price * quantity, 2)
        items.append(
            {
                "name": name,
                "quantity": quantity,
                "unit_price": price,
                "line_total": line_total,
            }
        )
        total += line_total

    total = round(total, 2)
    if not items:
        return False, "Your cart is empty."

    transaction = db.transaction()

    @transactional
    def create_transaction(transaction, user_ref, counter_ref):
        user_snap = user_ref.get(transaction=transaction)
        if not user_snap.exists:
            raise ValueError("Student profile not found.")

        counter_snap = counter_ref.get(transaction=transaction)
        current_number = int(counter_snap.to_dict().get("value", 0)) if counter_snap.exists else 0
        next_number = current_number + 1
        order_id = f"{next_number:03d}"

        user_data = user_snap.to_dict() or {}
        payment_status = "Pending"

        if payment_method == "Wallet":
            balance = float(user_data.get("wallet_balance", 0))
            if balance < total:
                raise ValueError(
                    f"Insufficient wallet balance. Available ₹{balance:.2f}."
                )

            new_balance = round(balance - total, 2)
            transaction.update(user_ref, {"wallet_balance": new_balance})

            wallet_tx_ref = db.collection("wallet_transactions").document()
            transaction.set(
                wallet_tx_ref,
                {
                    "uid": uid,
                    "type": "Debit",
                    "amount": total,
                    "balance_after": new_balance,
                    "reason": f"Order #{order_id}",
                    "order_id": order_id,
                    "created_at": firestore.SERVER_TIMESTAMP,
                    "date": today,
                },
            )
            payment_status = "Paid"

        transaction.set(
            counter_ref,
            {"value": next_number, "date": today},
            merge=True,
        )

        order_ref = db.collection("orders").document(f"{today}_{order_id}")
        order_data = {
            "order_id": order_id,
            "uid": uid,
            "student_name": user_data.get("name", ""),
            "student_id": user_data.get("student_id", ""),
            "email": user_data.get("email", ""),
            "items": items,
            "total": total,
            "order_type": order_type,
            "break_time": break_time,
            "payment_method": payment_method,
            "payment_status": payment_status,
            "status": "Confirmed",
            "date": today,
            "created_at": firestore.SERVER_TIMESTAMP,
        }
        transaction.set(order_ref, order_data)
        return order_data

    try:
        return True, create_transaction(transaction, user_ref, counter_ref)
    except Exception as exc:
        return False, str(exc)


def request_wallet_topup(student, amount, reason):
    """Create a pending request. This does NOT change wallet balance."""
    try:
        amount = float(amount)
    except Exception:
        return False, "Please enter a valid amount."

    if amount <= 0:
        return False, "Amount must be greater than zero."

    if amount > 10000:
        return False, "Maximum top-up request is ₹10,000."

    uid = student["uid"]

    existing = (
        db.collection("wallet_topup_requests")
        .where("uid", "==", uid)
        .where("status", "==", "Pending")
        .stream()
    )

    for doc in existing:
        data = doc.to_dict() or {}
        if round(float(data.get("amount", 0)), 2) == round(amount, 2):
            return False, "You already have a pending request for this amount."

    request_ref = db.collection("wallet_topup_requests").document()

    request_ref.set(
        {
            "uid": uid,
            "student_name": student.get("name", ""),
            "student_id": student.get("student_id", ""),
            "email": student.get("email", ""),
            "amount": round(amount, 2),
            "reason": reason.strip() or "Cash deposited at cafeteria desk",
            "status": "Pending",
            "date": date.today().isoformat(),
            "created_at": firestore.SERVER_TIMESTAMP,
        }
    )

    return True, request_ref.id


def get_wallet_topup_requests(status=None, uid=None):
    query = db.collection("wallet_topup_requests")

    if status is not None:
        query = query.where("status", "==", status)

    if uid is not None:
        query = query.where("uid", "==", uid)

    requests_list = []

    for doc in query.stream():
        item = doc.to_dict() or {}
        item["_doc_id"] = doc.id
        requests_list.append(item)

    return sorted(
        requests_list,
        key=lambda x: str(x.get("date", "")),
        reverse=True,
    )


def approve_wallet_topup(request):
    """Approve a pending request and credit the wallet atomically."""
    request_id = request.get("_doc_id")
    if not request_id:
        return False, "Top-up request ID is missing."

    amount = float(request.get("amount", 0))
    if amount <= 0:
        return False, "Invalid top-up amount."

    request_ref = db.collection("wallet_topup_requests").document(request_id)
    user_ref = db.collection("users").document(request.get("uid"))
    wallet_ref = db.collection("wallet_transactions").document()

    transaction = db.transaction()

    @transactional
    def approve_transaction(transaction, request_ref, user_ref, wallet_ref):
        request_snap = request_ref.get(transaction=transaction)
        if not request_snap.exists:
            raise ValueError("Top-up request not found.")

        request_data = request_snap.to_dict() or {}
        if request_data.get("status") != "Pending":
            raise ValueError("This top-up request has already been processed.")

        user_snap = user_ref.get(transaction=transaction)
        if not user_snap.exists:
            raise ValueError("Student profile not found.")

        user_data = user_snap.to_dict() or {}
        current_balance = float(user_data.get("wallet_balance", 0))
        new_balance = round(current_balance + amount, 2)

        transaction.update(
            user_ref,
            {"wallet_balance": new_balance},
        )

        transaction.set(
            wallet_ref,
            {
                "uid": request_data.get("uid"),
                "type": "Credit",
                "amount": amount,
                "balance_after": new_balance,
                "reason": request_data.get("reason", "Cash deposited at cafeteria desk"),
                "source": "Cafeteria Approved Top-up",
                "topup_request_id": request_id,
                "approved_by": DESK_NAME,
                "date": date.today().isoformat(),
                "created_at": firestore.SERVER_TIMESTAMP,
            },
        )

        transaction.update(
            request_ref,
            {
                "status": "Approved",
                "approved_amount": amount,
                "balance_after": new_balance,
                "approved_at": firestore.SERVER_TIMESTAMP,
                "approved_by": DESK_NAME,
            },
        )

        return new_balance

    try:
        new_balance = approve_transaction(
            transaction,
            request_ref,
            user_ref,
            wallet_ref,
        )
        return True, new_balance
    except Exception as exc:
        return False, str(exc)


def reject_wallet_topup(request, rejection_reason="Payment not verified at cafeteria desk."):
    request_id = request.get("_doc_id")
    if not request_id:
        return False, "Top-up request ID is missing."

    request_ref = db.collection("wallet_topup_requests").document(request_id)

    try:
        snap = request_ref.get()
        if not snap.exists:
            return False, "Top-up request not found."

        data = snap.to_dict() or {}
        if data.get("status") != "Pending":
            return False, "This top-up request has already been processed."

        request_ref.update(
            {
                "status": "Rejected",
                "rejection_reason": rejection_reason,
                "rejected_at": firestore.SERVER_TIMESTAMP,
                "rejected_by": DESK_NAME,
            }
        )
        return True, None
    except Exception as exc:
        return False, str(exc)


def add_wallet_money(uid, amount, reason="Cash deposited at cafeteria desk"):
    amount = float(amount)
    if amount <= 0:
        return False, "Amount must be greater than zero."

    transaction = db.transaction()
    user_ref = db.collection("users").document(uid)
    wallet_tx_ref = db.collection("wallet_transactions").document()

    @transactional
    def credit_transaction(transaction, user_ref, wallet_tx_ref):
        snap = user_ref.get(transaction=transaction)
        if not snap.exists:
            raise ValueError("Student profile not found.")

        current = float((snap.to_dict() or {}).get("wallet_balance", 0))
        new_balance = round(current + amount, 2)

        transaction.update(user_ref, {"wallet_balance": new_balance})
        transaction.set(
            wallet_tx_ref,
            {
                "uid": uid,
                "type": "Credit",
                "amount": amount,
                "balance_after": new_balance,
                "reason": reason,
                "created_at": firestore.SERVER_TIMESTAMP,
                "date": date.today().isoformat(),
            },
        )
        return new_balance

    try:
        return True, credit_transaction(transaction, user_ref, wallet_tx_ref)
    except Exception as exc:
        return False, str(exc)


# ============================================================
# SESSION / NAVIGATION
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
    st.session_state.pop("auth_session", None)
    st.session_state.pop("student_user", None)
    st.session_state["cart"] = {}
    st.session_state["last_order"] = None
    st.session_state["page"] = "Home"
    st.rerun()


def cafeteria_logout():
    st.session_state["cafeteria_logged_in"] = False
    st.session_state["page"] = "Home"
    st.rerun()


init_state()


# ============================================================
# HOME
# ============================================================

def home_page():
    student = current_student()

    st.markdown(
        """
<div class="hero">
<div class="hero-title">Pre-order. Skip the queue. Enjoy your break. 🍽️</div>
<div class="hero-sub">Order from Campus Cafeteria before the rush and collect your food quickly.</div>
</div>
""",
        unsafe_allow_html=True,
    )

    if student:
        st.success(
            f"Welcome back, {student.get('name', 'Student')}! "
            f"Wallet balance: ₹{float(student.get('wallet_balance', 0)):.2f}"
        )
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🍔 Order Food", use_container_width=True, type="primary"):
                go_to("Order Food")
        with c2:
            if st.button("📦 My Orders", use_container_width=True):
                go_to("My Orders")
        with c3:
            if st.button("💰 Wallet", use_container_width=True):
                go_to("Wallet")
    else:
        c1, c2, c3 = st.columns(3)
        cards = [
            ("🍔 Order Food", "Pre-order your meal and avoid the queue."),
            ("⏱️ Save Break Time", "Place your order before the cafeteria rush."),
            ("💳 Easy Payment", "Use your prepaid wallet or pay at the counter."),
        ]
        for index, (col, (title, text_value)) in enumerate(zip([c1, c2, c3], cards)):
            with col:
                st.markdown(
                    f"""
<div class="card">
<div class="card-title">{title}</div>
<div class="card-text">{text_value}</div>
</div>
""",
                    unsafe_allow_html=True,
                )
                if st.button("Get Started", key=f"home_start_{index}", use_container_width=True):
                    go_to("Student Login")

    st.markdown("### How it works")
    cols = st.columns(4)
    steps = [
        ("1", "Login", "Create your student account."),
        ("2", "Order", "Choose food and payment."),
        ("3", "Prepare", "Cafeteria confirms and prepares."),
        ("4", "Collect", "Show your Order ID at the desk."),
    ]
    for col, (num, title, text_value) in zip(cols, steps):
        with col:
            st.markdown(
                f"""
<div class="card">
<div class="card-title">{num}. {title}</div>
<div class="card-text">{text_value}</div>
</div>
""",
                unsafe_allow_html=True,
            )

    st.markdown("### Order modes")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown(
            """
<div class="card">
<div class="card-title">🕐 Break Order</div>
<div class="card-text">Choose a scheduled break period and collect during that break. Once confirmed, the order is ready for collection workflow.</div>
</div>
""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            """
<div class="card">
<div class="card-title">🏠 Regular Order</div>
<div class="card-text">Room / Hostel pre-order only. Available anytime, including during breaks. Estimated preparation: 10–15 minutes.</div>
</div>
""",
            unsafe_allow_html=True,
        )

    st.info(
        f"Need help at the desk? {DESK_NAME} · {DESK_PHONE} · {DESK_EMAIL}"
    )


# ============================================================
# NAVIGATION
# ============================================================

def render_nav():
    student = current_student()
    cafeteria = st.session_state.get("cafeteria_logged_in", False)

    st.markdown(
        """
<div class="app-brand">
    <div class="app-brand-icon">🍽️</div>
    <div class="app-brand-name">Campus Cafeteria</div>
</div>
""",
        unsafe_allow_html=True,
    )

    if student:
        labels = [
            ("🏠 Home", "Home"),
            ("🍔 Order Food", "Order Food"),
            ("📦 My Orders", "My Orders"),
            ("💰 Wallet", "Wallet"),
            ("💬 Feedback", "Feedback"),
            ("🚪 Logout", "Logout"),
        ]
        cols = st.columns(len(labels))
        for col, (label, page) in zip(cols, labels):
            with col:
                if st.button(label, key=f"nav_{page}", use_container_width=True):
                    logout_student() if page == "Logout" else go_to(page)

    elif cafeteria:
        labels = [
            ("📊 Dashboard", "Cafeteria Dashboard"),
            ("🍔 Menu", "Menu Management"),
            ("💬 Feedback", "Feedback Management"),
            ("🚪 Logout", "Cafeteria Logout"),
        ]
        cols = st.columns(len(labels))
        for col, (label, page) in zip(cols, labels):
            with col:
                if st.button(label, key=f"cnav_{page}", use_container_width=True):
                    cafeteria_logout() if page == "Cafeteria Logout" else go_to(page)

    else:
        labels = [
            ("🏠 Home", "Home"),
            ("🎓 Student Login", "Student Login"),
            ("🧑‍🍳 Cafeteria Portal", "Cafeteria Portal"),
        ]
        cols = st.columns(3)
        for col, (label, page) in zip(cols, labels):
            with col:
                if st.button(label, key=f"guest_{page}", use_container_width=True):
                    go_to(page)

    st.divider()


# ============================================================
# STUDENT LOGIN / SIGNUP
# ============================================================

def student_login_page():
    st.markdown("## 🎓 Student Login")

    if current_student():
        st.success("You are already logged in.")
        if st.button("Go to Home", type="primary"):
            go_to("Home")
        return

    login_tab, signup_tab, reset_tab = st.tabs(
        ["Login", "Create Account", "Forgot Password"]
    )

    with login_tab:
        email = st.text_input("Email", key="student_login_email")
        password = st.text_input("Password", type="password", key="student_login_password")

        if st.button("Login", type="primary", use_container_width=True):
            if not email.strip() or not password:
                st.error("Please enter both email and password.")
            else:
                data, error = login_student(email.strip(), password)
                if error:
                    st.error(f"Login failed: {error}")
                else:
                    st.session_state.auth_session = {
                        "id_token": data["idToken"],
                        "refresh_token": data["refreshToken"],
                        "login_time": datetime.now().timestamp(),
                    }
                    profile = get_user_profile(data["localId"])
                    if not profile:
                        st.error("Login succeeded but the student profile is missing.")
                        st.session_state.pop("auth_session", None)
                    else:
                        st.session_state.student_user = profile
                        st.session_state.page = "Home"
                        st.rerun()

    with signup_tab:
        name = st.text_input("Full Name", key="signup_name")
        student_id = st.text_input("Student ID / Roll Number", key="signup_student_id")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Create Password", type="password", key="signup_password")
        confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")

        if st.button("Create Account", type="primary", use_container_width=True):
            if not name.strip() or not student_id.strip() or not email.strip():
                st.error("Please fill all fields.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                data, error = signup_student(email.strip(), password)
                if error:
                    st.error(f"Could not create account: {error}")
                else:
                    save_user_profile(
                        data["localId"],
                        name,
                        student_id,
                        email,
                    )
                    st.session_state.auth_session = {
                        "id_token": data["idToken"],
                        "refresh_token": data["refreshToken"],
                        "login_time": datetime.now().timestamp(),
                    }
                    st.session_state.page = "Home"
                    st.success("Account created successfully.")
                    st.rerun()

    with reset_tab:
        email = st.text_input("Account email", key="reset_email")
        if st.button("Send Reset Email", use_container_width=True):
            if not email.strip():
                st.error("Enter your email.")
            else:
                _, error = send_password_reset(email.strip())
                if error:
                    st.error(f"Could not send reset email: {error}")
                else:
                    st.success("Password reset email sent. Check your inbox.")


# ============================================================
# ORDER FOOD
# ============================================================

def order_food_page():
    student = current_student()
    if not student:
        st.warning("Please log in first.")
        if st.button("Go to Student Login"):
            go_to("Student Login")
        return

    st.markdown("## 🍔 Order Food")

    menu = load_menu()
    available_items = [x for x in menu if x.get("available", True)]

    if not available_items:
        st.warning("No food items are currently available.")
        return

    popular = [x for x in available_items if x.get("popular", False)]
    if popular:
        st.markdown("### ⭐ Popular Picks")
        cols = st.columns(min(3, len(popular)))
        for col, item in zip(cols, popular[:3]):
            with col:
                with st.container(border=True):
                    image_bytes = decode_menu_image(item)
                    if image_bytes:
                        st.image(image_bytes, width=180)
                    else:
                        st.markdown("<div style='font-size:3rem;text-align:center;padding:.4rem 0;'>🍽️</div>", unsafe_allow_html=True)

                    st.markdown(
                        f"<div class=\"card-title\">{item['name']}</div>",
                        unsafe_allow_html=True,
                    )

                    discount = float(item.get("discount", 0))
                    if discount > 0:
                        st.markdown(
                            f"<div class=\"card-text\"><s>₹{float(item.get('price', 0)):.0f}</s> &nbsp; <b>₹{effective_price(item):.0f}</b></div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            f"<div class=\"card-text\"><b>₹{effective_price(item):.0f}</b></div>",
                            unsafe_allow_html=True,
                        )

    st.markdown("### Menu")

    for item in available_items:
        doc_id = str(item.get("_doc_id", item["name"]))
        name = item["name"]
        price = effective_price(item)

        c1, c2, c3 = st.columns([4, 1, 1])

        with c1:
            discount = float(item.get("discount", 0))
            if discount > 0:
                st.write(f"**{name}** — ~~₹{float(item.get('price', 0)):.0f}~~ ₹{price:.0f}")
            else:
                st.write(f"**{name}** — ₹{price:.0f}")

        with c2:
            current = int(st.session_state.cart.get(name, 0))
            quantity = st.number_input(
                "Qty",
                min_value=0,
                max_value=20,
                value=current,
                step=1,
                key=f"qty_{doc_id}",
            )
            if quantity <= 0:
                st.session_state.cart.pop(name, None)
            else:
                st.session_state.cart[name] = int(quantity)

        with c3:
            st.write("")

    cart = st.session_state.cart
    st.divider()

    if not cart:
        st.info("Your cart is empty. Select quantities above.")
        return

    menu_map = {x["name"]: x for x in menu}
    total = 0.0

    st.markdown("### 🛒 Your Cart")
    for name, quantity in cart.items():
        item = menu_map.get(name)
        if item:
            line = effective_price(item) * int(quantity)
            total += line
            st.write(f"**{name}** × {quantity} = ₹{line:.0f}")

    total = round(total, 2)
    st.markdown(f"### Total: ₹{total:.0f}")

    order_mode = st.radio(
        "Order Type",
        ["Break Order", "Regular Order"],
        horizontal=True,
        key="order_type_selector",
    )

    break_time = None
    if order_mode == "Break Order":
        st.caption("Choose the break period when you will collect your order.")
        break_time = st.selectbox(
            "Break Time",
            BREAK_OPTIONS,
            key="break_time_selector",
        )
    else:
        st.info(
            "Regular Order = Room / Hostel pre-order only. "
            "Available anytime, including during a break. "
            "Estimated preparation time: 10–15 minutes."
        )

    payment_method = st.radio(
        "Payment Method",
        ["Wallet", "Pay at Counter"],
        horizontal=True,
        key="payment_method_selector",
    )

    wallet_balance = float(student.get("wallet_balance", 0))
    if payment_method == "Wallet":
        st.caption(f"Wallet balance: ₹{wallet_balance:.2f}")
        if wallet_balance < total:
            st.warning(f"You need ₹{total - wallet_balance:.2f} more in your wallet.")
    else:
        st.caption("Pay at the cafeteria desk before collection.")

    if st.button("Place Order", type="primary", use_container_width=True):
        if payment_method == "Wallet" and wallet_balance < total:
            st.error("Insufficient wallet balance.")
            return

        ok, result = create_order(
            student,
            cart,
            order_mode,
            break_time,
            payment_method,
        )

        if not ok:
            st.error(f"Could not place order: {result}")
            return

        st.session_state.last_order = result
        st.session_state.cart = {}
        st.session_state.page = "Order Confirmation"
        st.rerun()


# ============================================================
# ORDER CONFIRMATION
# ============================================================

def confirmation_page():
    order = st.session_state.get("last_order")
    if not order:
        st.info("No recent order.")
        if st.button("Order Food"):
            go_to("Order Food")
        return

    st.markdown("## ✅ Order Confirmed")
    st.success(f"Your Order ID is #{order.get('order_id')}")

    st.markdown(
        f"""
<div class="success-box">
<div class="order-id">#{order.get('order_id')}</div>
<p style="text-align:center;margin:0;">Show this Order ID at the cafeteria desk.</p>
</div>
""",
        unsafe_allow_html=True,
    )

    st.write(f"**Order Type:** {order.get('order_type', '-')}")
    if order.get("break_time"):
        st.write(f"**Break:** {order.get('break_time')}")
    st.write(f"**Payment:** {order.get('payment_method', '-')}")
    st.write(f"**Payment Status:** {order.get('payment_status', '-')}")
    st.write(f"**Status:** {order.get('status', 'Confirmed')}")
    st.write(f"**Total:** ₹{float(order.get('total', 0)):.0f}")

    st.markdown("### Items")
    for item in normalize_items(order.get("items", [])):
        st.write(
            f"{item['name']} × {item['quantity']} — ₹{float(item.get('line_total', 0)):.0f}"
        )

    if order.get("payment_method") == "Pay at Counter":
        st.warning("Please pay at the cafeteria desk before collection.")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("📦 Track Order", use_container_width=True):
            go_to("My Orders")
    with c2:
        if st.button("🍔 Order More", use_container_width=True):
            go_to("Order Food")


# ============================================================
# MY ORDERS
# ============================================================

def my_orders_page():
    student = current_student()
    if not student:
        st.warning("Please log in first.")
        return

    st.markdown("## 📦 My Orders")
    orders = get_student_orders(student["uid"])

    if not orders:
        st.info("You have no orders yet.")
        if st.button("Order Food"):
            go_to("Order Food")
        return

    for order in orders[:30]:
        status = order.get("status", "Confirmed")
        payment_status = order.get("payment_status", "-")

        with st.container(border=True):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.markdown(f"### #{order.get('order_id')}")
            with c2:
                st.write(f"**Status**\n\n{status}")
            with c3:
                st.write(f"**Payment**\n\n{payment_status}")
            with c4:
                st.write(f"**Total**\n\n₹{float(order.get('total', 0)):.0f}")

            if order.get("break_time"):
                st.caption(f"Break: {order['break_time']}")

            st.write(items_text(order.get("items", [])))

            if status == "Collected":
                st.success("Collected")
            elif order.get("payment_method") == "Pay at Counter" and payment_status != "Paid":
                st.warning("Pay at the cafeteria desk before collection.")
            else:
                st.info("Bring your Order ID to the cafeteria desk for collection.")


# ============================================================
# WALLET
# ============================================================

def wallet_page():
    student = current_student()
    if not student:
        st.warning("Please log in first.")
        return

    student = get_user_profile(student["uid"]) or student
    balance = float(student.get("wallet_balance", 0))

    st.markdown("## 💰 Wallet")
    st.metric("Available Balance", f"₹{balance:.2f}", border=True)

    st.info(
        "First pay the cafeteria desk. Then send a top-up request here. "
        "Your balance changes only after cafeteria staff approve the payment."
    )

    st.markdown("### ➕ Request Wallet Top-up")

    amount = st.number_input(
        "Amount to request",
        min_value=1.0,
        max_value=10000.0,
        value=100.0,
        step=50.0,
        key="wallet_request_amount",
    )

    reason = st.text_input(
        "Reason",
        value="Cash deposited at cafeteria desk",
        key="wallet_request_reason",
    )

    if st.button(
        "📨 Send Top-up Request",
        type="primary",
        use_container_width=True,
        key="wallet_request_button",
    ):
        ok, result = request_wallet_topup(
            student,
            amount,
            reason,
        )

        if ok:
            st.success(
                f"₹{amount:.2f} request sent to the cafeteria. "
                "Your wallet balance has NOT changed yet."
            )
            st.rerun()
        else:
            st.error(str(result))

    st.markdown("### 📋 My Top-up Requests")

    requests_list = get_wallet_topup_requests(uid=student["uid"])

    if not requests_list:
        st.caption("No wallet top-up requests yet.")
    else:
        for request in requests_list[:20]:
            with st.container(border=True):
                c1, c2, c3 = st.columns([2, 2, 1.4])

                with c1:
                    st.write(
                        f"**₹{float(request.get('amount', 0)):.2f}**"
                    )
                    st.caption(
                        request.get(
                            "reason",
                            "Cash deposited at cafeteria desk",
                        )
                    )

                with c2:
                    st.caption(
                        f"Date: {request.get('date', '-') }"
                    )
                    if request.get("status") == "Approved":
                        st.caption(
                            f"Approved by: {request.get('approved_by', DESK_NAME)}"
                        )
                    elif request.get("status") == "Rejected":
                        st.caption(
                            request.get(
                                "rejection_reason",
                                "Request rejected.",
                            )
                        )

                with c3:
                    status = request.get("status", "Pending")
                    if status == "Approved":
                        st.success("Approved")
                    elif status == "Rejected":
                        st.error("Rejected")
                    else:
                        st.warning("Pending")

    st.caption(
        "Only cafeteria staff can approve and credit wallet money."
    )


# ============================================================
# STUDENT FEEDBACK
# ============================================================

def feedback_page():
    student = current_student()
    if not student:
        st.warning("Please log in first.")
        return

    st.markdown("## 💬 Feedback")

    rating = st.slider("Rating", 1, 5, 5, key="feedback_rating")
    category = st.selectbox(
        "Category",
        ["Food Quality", "Taste", "Service", "Waiting Time", "Other"],
        key="feedback_category",
    )
    message = st.text_area("Your feedback", key="feedback_message")
    photo = st.file_uploader(
        "Optional photo",
        type=["png", "jpg", "jpeg", "webp"],
        key="feedback_photo",
    )

    if st.button("Submit Feedback", type="primary", use_container_width=True):
        if not message.strip():
            st.error("Please enter your feedback.")
            return

        try:
            photo_b64 = image_to_base64(photo)
        except ValueError as exc:
            st.error(str(exc))
            return

        db.collection("feedback").add(
            {
                "uid": student["uid"],
                "student_name": student.get("name", ""),
                "student_id": student.get("student_id", ""),
                "rating": int(rating),
                "category": category,
                "message": message.strip(),
                "photo_base64": photo_b64,
                "created_at": firestore.SERVER_TIMESTAMP,
                "date": date.today().isoformat(),
            }
        )
        st.success("Thank you for your feedback!")
        st.rerun()


# ============================================================
# CAFETERIA LOGIN
# ============================================================

def cafeteria_login_page():
    st.markdown("## 🧑‍🍳 Cafeteria Portal")
    st.info("This portal is for cafeteria desk staff.")

    login_id = st.text_input("Login ID", key="caf_login_id")
    password = st.text_input("Password", type="password", key="caf_password")

    if st.button("Login to Cafeteria Portal", type="primary", use_container_width=True):
        if (
            login_id.strip().lower() == CAFETERIA_LOGIN_ID.lower()
            and password == CAFETERIA_PASSWORD
        ):
            st.session_state.cafeteria_logged_in = True
            st.session_state.page = "Cafeteria Dashboard"
            st.rerun()
        else:
            st.error("Incorrect Login ID or Password.")


# ============================================================
# CAFETERIA DASHBOARD
# ============================================================

def cafeteria_dashboard_page():
    if not st.session_state.get("cafeteria_logged_in"):
        go_to("Cafeteria Portal")
        return

    st.markdown(
        """
<div class="dashboard-title">
    <h2>📊 Cafeteria Dashboard</h2>
    <p>Manage today's orders, payments and wallet approvals from one place.</p>
    <span class="dashboard-chip">🟢 Cafeteria Desk Online</span>
</div>
""",
        unsafe_allow_html=True,
    )

    contact_cols = st.columns([1.2, 1, 1, 1])
    with contact_cols[0]:
        st.metric("👨‍🍳 Desk", DESK_NAME, border=True)
    with contact_cols[1]:
        st.metric("📞 Contact", DESK_PHONE, border=True)
    with contact_cols[2]:
        st.metric("📅 Date", date.today().strftime("%d %b"), border=True)
    with contact_cols[3]:
        st.metric("💳 Wallet", "Approval Required", border=True)

    # ========================================================
    # WALLET TOP-UP REQUESTS
    # ========================================================
    st.markdown(
        '<div class="section-title">💰 Wallet Top-up Requests</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="dashboard-subtitle">Students can request a top-up, but their balance changes only after the cafeteria verifies the payment.</div>',
        unsafe_allow_html=True,
    )

    pending_topups = get_wallet_topup_requests(status="Pending")

    if not pending_topups:
        st.markdown(
            '<div class="topup-empty">✅ No pending wallet top-up requests. Everything is up to date.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.warning(
            f"🔔 {len(pending_topups)} wallet top-up request(s) are waiting for approval."
        )

        for request_index, request in enumerate(pending_topups):
            request_key = str(request.get("_doc_id", request_index))

            with st.container(border=True):
                c1, c2, c3 = st.columns([2.5, 1.5, 2])

                with c1:
                    st.markdown(
                        f"### 👤 {request.get('student_name', '-')}"
                    )
                    st.caption(
                        f"Student ID: {request.get('student_id', '-')}"
                    )
                    st.caption(
                        f"📧 {request.get('email', '-')}"
                    )

                with c2:
                    st.markdown(
                        f"### ₹{float(request.get('amount', 0)):.2f}"
                    )
                    st.caption(
                        f"Requested: {request.get('date', '-')}"
                    )

                with c3:
                    st.info(
                        request.get(
                            "reason",
                            "Cash deposited at cafeteria desk",
                        )
                    )

                    a1, a2 = st.columns(2)
                    with a1:
                        if st.button(
                            "✅ Approve",
                            type="primary",
                            use_container_width=True,
                            key=f"approve_topup_{request_key}",
                        ):
                            ok, result = approve_wallet_topup(request)
                            if ok:
                                st.success(
                                    f"₹{float(request.get('amount', 0)):.2f} credited. "
                                    f"New balance: ₹{result:.2f}"
                                )
                                st.rerun()
                            else:
                                st.error(str(result))

                    with a2:
                        if st.button(
                            "❌ Reject",
                            use_container_width=True,
                            key=f"reject_topup_{request_key}",
                        ):
                            ok, error = reject_wallet_topup(request)
                            if ok:
                                st.success("Top-up request rejected.")
                                st.rerun()
                            else:
                                st.error(str(error))

    st.divider()

    # ========================================================
    # TODAY'S ORDER OVERVIEW
    # ========================================================
    orders = get_today_orders()

    counts = {
        "Total": len(orders),
        "Confirmed": sum(x.get("status") == "Confirmed" for x in orders),
        "Preparing": sum(x.get("status") == "Preparing" for x in orders),
        "Ready": sum(x.get("status") == "Ready" for x in orders),
        "Collected": sum(x.get("status") == "Collected" for x in orders),
    }

    st.markdown(
        '<div class="section-title">📈 Today\'s Overview</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="dashboard-subtitle">A quick view of the current order pipeline.</div>',
        unsafe_allow_html=True,
    )

    cols = st.columns(5)
    cols[0].metric("📦 Total Orders", counts["Total"], border=True)
    cols[1].metric("🔵 Confirmed", counts["Confirmed"], border=True)
    cols[2].metric("🟠 Preparing", counts["Preparing"], border=True)
    cols[3].metric("🟢 Ready", counts["Ready"], border=True)
    cols[4].metric("✅ Collected", counts["Collected"], border=True)

    st.markdown(
        '<div class="section-title">🧾 Today\'s Orders</div>',
        unsafe_allow_html=True,
    )

    if not orders:
        st.info("No orders today.")
    else:
        f1, f2 = st.columns([2.5, 1])
        with f1:
            search = st.text_input(
                "🔎 Search by Order ID, Student Name or Student ID",
                key="dashboard_order_search",
            )
        with f2:
            status_filter = st.selectbox(
                "Filter by Status",
                ["All", "Confirmed", "Preparing", "Ready", "Collected"],
                key="dashboard_status_filter",
            )

        filtered = []
        for order in orders:
            searchable = (
                f"{order.get('order_id','')} "
                f"{order.get('student_name','')} "
                f"{order.get('student_id','')}"
            ).lower()

            if search.strip().lower() not in searchable:
                continue
            if status_filter != "All" and order.get("status") != status_filter:
                continue
            filtered.append(order)

        st.caption(f"Showing {len(filtered)} of {len(orders)} order(s)")

        if not filtered:
            st.info("No orders match your search/filter.")
        else:
            for order_index, order in enumerate(filtered):
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([1.1, 2.4, 2.2, 2])

                    with c1:
                        st.markdown(
                            '<div class="order-card-label">Order ID</div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<div class="order-card-id">#{order.get("order_id", "-")}</div>',
                            unsafe_allow_html=True,
                        )

                    with c2:
                        st.markdown(
                            '<div class="order-card-label">Student</div>',
                            unsafe_allow_html=True,
                        )
                        st.write(f"**{order.get('student_name','-')}**")
                        st.caption(f"Student ID: {order.get('student_id','-')}")
                        st.caption(order.get("order_type", "-"))
                        if order.get("break_time"):
                            st.caption(f"Break: {order.get('break_time')}")

                    with c3:
                        st.markdown(
                            '<div class="order-card-label">Items</div>',
                            unsafe_allow_html=True,
                        )
                        st.write(items_text(order.get("items", [])))
                        st.caption(f"Total: ₹{float(order.get('total', 0)):.0f}")

                    with c4:
                        status = order.get("status", "Confirmed")
                        payment_status = order.get("payment_status", "Pending")

                        status_icon = {
                            "Confirmed": "🔵",
                            "Preparing": "🟠",
                            "Ready": "🟢",
                            "Collected": "✅",
                        }.get(status, "⚪")

                        st.markdown(
                            '<div class="order-card-label">Status</div>',
                            unsafe_allow_html=True,
                        )
                        st.write(f"**{status_icon} {status}**")

                        if payment_status == "Paid":
                            st.markdown(
                                '<div class="payment-paid">🟢 Payment: Paid</div>',
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                '<div class="payment-pending">🟠 Payment: Pending</div>',
                                unsafe_allow_html=True,
                            )

                        order_key = str(
                            order.get(
                                "_doc_id",
                                order.get("order_id", order_index),
                            )
                        )

                        if (
                            order.get("payment_method") == "Pay at Counter"
                            and payment_status != "Paid"
                        ):
                            if st.button(
                                "💵 Payment Received",
                                key=f"pay_{order_key}",
                                use_container_width=True,
                            ):
                                ok, error = mark_counter_payment_received(order)
                                if ok:
                                    st.rerun()
                                else:
                                    st.error(error)

                        if status == "Confirmed":
                            if st.button(
                                "▶ Start Preparing",
                                key=f"prep_{order_key}",
                                use_container_width=True,
                            ):
                                ok, error = update_order_status(order, "Preparing")
                                if ok:
                                    st.rerun()
                                else:
                                    st.error(error)

                        elif status == "Preparing":
                            if st.button(
                                "✓ Mark Ready",
                                key=f"ready_{order_key}",
                                use_container_width=True,
                            ):
                                ok, error = update_order_status(order, "Ready")
                                if ok:
                                    st.rerun()
                                else:
                                    st.error(error)

                        elif status == "Ready":
                            if (
                                order.get("payment_method") == "Pay at Counter"
                                and payment_status != "Paid"
                            ):
                                st.warning("Collect payment before handover.")
                            else:
                                if st.button(
                                    "📦 Mark Collected",
                                    key=f"collect_{order_key}",
                                    use_container_width=True,
                                ):
                                    ok, error = update_order_status(order, "Collected")
                                    if ok:
                                        st.rerun()
                                    else:
                                        st.error(error)

    st.divider()
    st.markdown("### 🧹 Manual Cleanup")
    st.caption(
        "Deletes orders older than 14 days. Use only when you are sure old records are no longer needed."
    )

    if st.button("Delete Orders Older Than 14 Days", key="cleanup_orders"):
        cutoff = date.today() - timedelta(days=14)
        old_docs = list(
            db.collection("orders")
            .where("date", "<", cutoff.isoformat())
            .limit(200)
            .stream()
        )

        if not old_docs:
            st.info("No orders older than 14 days were found.")
        else:
            batch = db.batch()
            for doc in old_docs:
                batch.delete(doc.reference)
            batch.commit()
            st.success(f"Deleted {len(old_docs)} old order(s).")


# ============================================================
# MENU MANAGEMENT
# ============================================================

def menu_management_page():
    if not st.session_state.get("cafeteria_logged_in"):
        go_to("Cafeteria Portal")
        return

    st.markdown("## 🍔 Menu Management")

    menu = load_menu()

    st.markdown("### Add New Item")
    with st.form("add_menu_form"):
        name = st.text_input("Item Name")
        price = st.number_input("Price", min_value=0.0, step=5.0)
        discount = st.number_input(
            "Discount (%)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=1.0,
        )
        available = st.checkbox("Available", value=True)
        popular = st.checkbox("Popular Pick", value=False)
        photo = st.file_uploader(
            "Food Photo (optional)",
            type=["png", "jpg", "jpeg", "webp"],
            key="new_food_photo",
        )
        save_new = st.form_submit_button("Save Item", type="primary")

    if save_new:
        if not name.strip():
            st.error("Enter an item name.")
        elif price <= 0:
            st.error("Price must be greater than zero.")
        else:
            try:
                photo_b64 = image_to_base64(photo)
                save_menu_item(
                    name.strip(),
                    price,
                    discount,
                    available,
                    popular,
                )
                if photo_b64:
                    db.collection("menu").document(name.strip()).set(
                        {"photo_base64": photo_b64},
                        merge=True,
                    )
                st.success("Menu item saved.")
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    st.markdown("### Current Menu")

    for index, item in enumerate(menu):
        doc_id = item.get("_doc_id", item.get("name", index))
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([3, 1.2, 1.2, 1.2])

            with c1:
                discount = float(item.get("discount", 0))
                price_text = f"₹{effective_price(item):.0f}"
                if discount:
                    price_text += f" · {discount:.0f}% off"
                st.write(f"**{item['name']}** — {price_text}")

            with c2:
                st.write("Available" if item.get("available", True) else "Unavailable")

            with c3:
                st.write("⭐ Popular" if item.get("popular", False) else "")

            with c4:
                if st.button("Delete", key=f"menu_delete_{doc_id}", use_container_width=True):
                    delete_menu_item(item)
                    st.rerun()

            with st.expander("Edit item"):
                with st.form(f"edit_menu_{doc_id}"):
                    edit_name = st.text_input(
                        "Name",
                        value=str(item.get("name", "")),
                    )
                    edit_price = st.number_input(
                        "Price",
                        min_value=0.0,
                        value=float(item.get("price", 0)),
                        step=5.0,
                    )
                    edit_discount = st.number_input(
                        "Discount (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(item.get("discount", 0)),
                        step=1.0,
                    )
                    edit_available = st.checkbox(
                        "Available",
                        value=bool(item.get("available", True)),
                    )
                    edit_popular = st.checkbox(
                        "Popular Pick",
                        value=bool(item.get("popular", False)),
                    )
                    edit_photo = st.file_uploader(
                        "Replace photo (optional)",
                        type=["png", "jpg", "jpeg", "webp"],
                        key=f"edit_photo_{doc_id}",
                    )
                    save_edit = st.form_submit_button("Save Changes")

                if save_edit:
                    if not edit_name.strip():
                        st.error("Name cannot be empty.")
                    elif edit_price <= 0:
                        st.error("Price must be greater than zero.")
                    else:
                        try:
                            photo_b64 = image_to_base64(edit_photo)
                            save_menu_item(
                                edit_name.strip(),
                                edit_price,
                                edit_discount,
                                edit_available,
                                edit_popular,
                                old_doc_id=doc_id,
                            )
                            if photo_b64:
                                db.collection("menu").document(edit_name.strip()).set(
                                    {"photo_base64": photo_b64},
                                    merge=True,
                                )
                            st.success("Item updated.")
                            st.rerun()
                        except ValueError as exc:
                            st.error(str(exc))


# ============================================================
# FEEDBACK MANAGEMENT
# ============================================================

def feedback_management_page():
    if not st.session_state.get("cafeteria_logged_in"):
        go_to("Cafeteria Portal")
        return

    st.markdown("## 💬 Feedback Management")

    docs = list(db.collection("feedback").stream())
    feedback = [dict(doc.to_dict() or {}, _doc_id=doc.id) for doc in docs]

    if not feedback:
        st.info("No feedback yet.")
        return

    feedback.sort(
        key=lambda x: timestamp_sort_key(x.get("created_at")),
        reverse=True,
    )

    for item in feedback[:100]:
        with st.container(border=True):
            c1, c2 = st.columns([1, 4])
            with c1:
                st.metric("Rating", f"{item.get('rating','-')}/5")
            with c2:
                st.write(
                    f"**{item.get('student_name','-')}** · "
                    f"{item.get('category','')}"
                )
                st.write(item.get("message", ""))
                if item.get("photo_base64"):
                    try:
                        st.image(
                            base64.b64decode(item["photo_base64"]),
                            width=260,
                        )
                    except Exception:
                        st.caption("Attached photo could not be displayed.")


# ============================================================
# MAIN ROUTER
# ============================================================

if not firebase_connected:
    st.error("🔴 Firebase connection failed.")
    st.code(firebase_error)
    st.stop()

render_nav()

page = st.session_state.get("page", "Home")

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
