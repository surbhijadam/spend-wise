from flask import Flask, jsonify, request, render_template, redirect, url_for, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import io
import csv
import math
import os
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask import jsonify
from flask_login import login_required, current_user
from collections import defaultdict
import os
from flask import Flask, request, jsonify
from google import genai # The new SDK
from dotenv import load_dotenv

# Load the key from the .env file
load_dotenv()

app = Flask(__name__)

# Initialize the Gemini Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

@app.route('/ai', methods=['POST']) # Or wherever your AI logic sits
def ai_feature():
    try:
        user_msg = request.json.get('message')
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=user_msg
        )
        return jsonify({"reply": response.text})
    except Exception as e:
        print(f"AI Error: {e}")
        return jsonify({"error": str(e)}), 400

# ... rest of your routes ...

# ---------------- FLASK APP SETUP ---------------- 
app = Flask(__name__)
CORS(app)
app.secret_key = os.environ.get("FLASK_SECRET", "dev-secret-please-change")

# serializer for token-based auth (optional)
serializer = URLSafeTimedSerializer(app.secret_key)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'


class User(UserMixin):
    def __init__(self, username, name=None):
        self.id = username
        self.name = name or username


@login_manager.user_loader
def load_user(username):
    user_doc = users_collection.find_one({'username': username})
    if user_doc:
        return User(username, user_doc.get('name'))
    return None

# ---------------- FRONTEND ROUTES ---------------- #

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/add-expense-page")
@login_required
def add_expense_page():
    return render_template("add_expense.html")

@app.route('/add-income')
@login_required
def add_income_page():
    return render_template('income.html')

@app.route('/view-income')
@login_required
def view_income_page():
    return render_template('view_income.html')


@app.route("/view-expense-page")
@login_required
def view_expense_page():
    return render_template("view_expenses.html")


@app.route('/analytics-page')
@login_required
def analytics_page():
    # Page is public — JS will call APIs and redirect to /login on 401 if needed
    return render_template('analytics.html')


@app.route('/ai')
@login_required
def ai_page():
    return render_template('ai.html')


@app.route('/gamification')
@login_required
def gamification_page():
    return render_template('gamification.html')

# ---------------- MONGODB CONNECTION ---------------- #

client = MongoClient("mongodb://localhost:27017/")
db = client["SpendWiseDB"]
expenses_collection = db["expenses"]
users_collection = db["users"]
income_col = db["income"]


# ---------------- API ROUTES ---------------- #

@app.route('/add-expense', methods=['POST'])
@login_required
def add_expense():
    # Accept either session-based login (Flask-Login) or Bearer token
    def get_req_user():
        # check Authorization header for Bearer token
        auth = request.headers.get('Authorization', '')
        if auth.startswith('Bearer '):
            tok = auth.split(' ', 1)[1]
            try:
                data = serializer.loads(tok, max_age=60 * 60 * 24 * 30)
                return data.get('username')
            except (SignatureExpired, BadSignature):
                return None
        if current_user and current_user.is_authenticated:
            return current_user.id
        return None

    user = get_req_user()
    if not user:
        return jsonify({'error': 'not authenticated'}), 401

    data = request.json or {}
    try:
        amount = float(data.get('amount') or 0)
    except ValueError:
        return jsonify({'error': 'invalid amount'}), 400

    expense = {
        'amount': amount,
        'category': data.get('category'),
        'note': data.get('note'),
        'date': data.get('date') or datetime.utcnow().strftime('%Y-%m-%d'),
        'user': user
    }

    res = expenses_collection.insert_one(expense)
    return jsonify({'message': 'Expense added successfully', 'id': str(res.inserted_id)}), 201


@app.route('/get-expenses', methods=['GET'])
@login_required
def get_expenses():
    # allow token or session
    auth = request.headers.get('Authorization', '')
    username = None
    if auth.startswith('Bearer '):
        tok = auth.split(' ', 1)[1]
        try:
            data = serializer.loads(tok, max_age=60 * 60 * 24 * 30)
            username = data.get('username')
        except (SignatureExpired, BadSignature):
            username = None
    if not username and current_user and current_user.is_authenticated:
        username = current_user.id
    if not username:
        return jsonify({'error': 'not authenticated'}), 401

    expenses = list(expenses_collection.find({'user': username}, { }))
    # convert _id to string and keep fields
    out = []
    for e in expenses:
        out.append({
            'id': str(e.get('_id')),
            'amount': e.get('amount'),
            'category': e.get('category'),
            'note': e.get('note'),
            'date': e.get('date')
        })
    return jsonify(out), 200


# ---------------- ADD INCOME ----------------
@app.route("/add-income", methods=["GET", "POST"])
def add_income():
    if request.method == "POST":
        amount = request.form.get("amount")
        source = request.form.get("source")
        note = request.form.get("note")
        date = request.form.get("date")

        if not amount or not source or not date:
            return "Missing fields", 400

        income_col.insert_one({
            "amount": float(amount),
            "source": source,
            "note": note,
            "date": datetime.strptime(date, "%Y-%m-%d")
        })

        return redirect(url_for("add_income"))

    # total income
    total = 0
    result = income_col.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$amount"}}}
    ])
    for r in result:
        total = r["total"]

    return render_template("income.html", total_income=total)


# ---------------- VIEW ALL INCOME ----------------
@app.route("/view-income")
def view_income():
    data = []
    for inc in income_col.find().sort("date", -1):
        data.append({
            "amount": inc["amount"],
            "source": inc["source"],
            "note": inc.get("note", ""),
            "date": inc["date"].strftime("%Y-%m-%d")
        })
    return jsonify(data)


@app.route('/api/analytics', methods=['GET'])
@login_required
def analytics_api():
    # Accept either session-based login or Bearer token
    username = get_request_username()
    if not username:
        return jsonify({'error': 'not authenticated'}), 401

    # Expenses are stored with key 'user' (username); support legacy 'user_id' as well
    expenses = list(expenses_collection.find({'$or': [{'user': username}, {'user_id': username}]}))

    if not expenses:
        return jsonify({
            "total_spent": 0,
            "prediction_next_month": 0,
            "top_merchant": "N/A",
            "spending_by_category": [],
            "monthly_trend": []
        })

    # ---- Total Spent ----
    total_spent = sum(float(e['amount']) for e in expenses)

    # ---- Spending by Category ----
    category_map = defaultdict(float)
    for e in expenses:
        category_map[e.get('category', 'Other')] += float(e['amount'])

    spending_by_category = [
        {"category": k, "total_spent": v}
        for k, v in category_map.items()
    ]

    # ---- Monthly Trend ----
    monthly_map = defaultdict(float)
    for e in expenses:
        date = e.get('date')
        if isinstance(date, str):
            month = date[:7]  # YYYY-MM
        else:
            month = datetime.now().strftime('%Y-%m')
        monthly_map[month] += float(e['amount'])

    monthly_trend = [
        {"month": k, "total_spent": v}
        for k, v in sorted(monthly_map.items())
    ]

    # ---- Top Merchant ----
    merchant_map = defaultdict(float)
    for e in expenses:
        merchant_map[e.get('note', 'Unknown')] += float(e['amount'])

    top_merchant = max(merchant_map, key=merchant_map.get)

    # ---- Simple Prediction (avg) ----
    prediction = total_spent / max(len(monthly_trend), 1)

    return jsonify({
        "total_spent": total_spent,
        "prediction_next_month": round(prediction, 2),
        "top_merchant": top_merchant,
        "spending_by_category": spending_by_category,
        "monthly_trend": monthly_trend
    })


@app.route('/api/summary', methods=['GET'])
def api_summary():
    # Resolve username from Bearer token or session
    username = get_request_username()
    if not username:
        return jsonify({'error':'unauthorized'}), 401

    user_filter = {'user': username}
    # Total sum
    pipeline_total = [
        {'$match': user_filter},
        {'$group': {'_id': None, 'total': {'$sum': '$amount'}}}
    ]
    total_res = list(expenses_collection.aggregate(pipeline_total))
    total = total_res[0]['total'] if total_res else 0.0

    # Totals by category
    pipeline_cat = [
        {'$match': user_filter},
        {'$group': {'_id': '$category', 'total': {'$sum': '$amount'}}},
        {'$sort': {'total': -1}}
    ]
    cat_res = list(expenses_collection.aggregate(pipeline_cat))
    by_category = [{'category': r['_id'], 'total': r['total']} for r in cat_res]

    # Monthly totals (YYYY-MM)
    pipeline_month = [
        {'$match': user_filter},
        {'$project': {'amount': '$amount', 'year_month': {'$substr': ['$date', 0, 7]}}},
        {'$group': {'_id': '$year_month', 'total': {'$sum': '$amount'}}},
        {'$sort': {'_id': 1}}
    ]
    month_res = list(expenses_collection.aggregate(pipeline_month))
    monthly = [{'month': r['_id'], 'total': r['total']} for r in month_res]

    # top merchants by note/merchant field (if note used to store merchant)
    pipeline_merch = [
        {'$match': user_filter},
        {'$match': {'note': {'$ne': None}}},
        {'$group': {'_id': '$note', 'total': {'$sum': '$amount'}}},
        {'$sort': {'total': -1}},
        {'$limit': 10}
    ]
    merch_res = list(expenses_collection.aggregate(pipeline_merch))
    top_merchants = [{'merchant': r['_id'], 'total': r['total']} for r in merch_res]

    return jsonify({'total': total, 'by_category': by_category, 'monthly': monthly, 'top_merchants': top_merchants}), 200


def get_request_username():
    """Helper: return username from Bearer token or current_user session."""
    username = None
    auth = request.headers.get('Authorization', '')
    if auth and auth.startswith('Bearer '):
        token = auth.split(' ', 1)[1]
        try:
            data = serializer.loads(token, max_age=60 * 60 * 24 * 30)
            # tokens in this app are created as {'username': ...}
            username = data.get('username') or data.get('user') or data.get('id')
        except (SignatureExpired, BadSignature, Exception):
            username = None
    if not username:
        if current_user and getattr(current_user, 'is_authenticated', False):
            # User ID is stored on .id in UserMixin
            username = getattr(current_user, 'id', None)
    return username


# ---------------- EXPENSE EDIT / DELETE ---------------- #

@app.route('/api/expense/<expense_id>', methods=['PUT'])
def update_expense(expense_id):
    data = request.json or {}
    # auth
    auth = request.headers.get('Authorization', '')
    username = None
    if auth.startswith('Bearer '):
        tok = auth.split(' ', 1)[1]
        try:
            data_tok = serializer.loads(tok, max_age=60 * 60 * 24 * 30)
            username = data_tok.get('username')
        except (SignatureExpired, BadSignature):
            username = None
    if not username and current_user and current_user.is_authenticated:
        username = current_user.id
    if not username:
        return jsonify({'error': 'not authenticated'}), 401
    try:
        oid = ObjectId(expense_id)
    except Exception:
        return jsonify({'error': 'invalid id'}), 400

    existing = expenses_collection.find_one({'_id': oid, 'user': username})
    if not existing:
        return jsonify({'error': 'not found'}), 404

    update = {}
    if 'amount' in data:
        try:
            update['amount'] = float(data['amount'])
        except Exception:
            return jsonify({'error': 'invalid amount'}), 400
    if 'category' in data:
        update['category'] = data['category']
    if 'note' in data:
        update['note'] = data['note']
    if 'date' in data:
        update['date'] = data['date']

    if update:
        expenses_collection.update_one({'_id': oid}, {'$set': update})
    return jsonify({'message': 'updated'}), 200


@app.route('/api/expense/<expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    try:
        oid = ObjectId(expense_id)
    except Exception:
        return jsonify({'error': 'invalid id'}), 400
    # auth
    auth = request.headers.get('Authorization', '')
    username = None
    if auth.startswith('Bearer '):
        tok = auth.split(' ', 1)[1]
        try:
            data_tok = serializer.loads(tok, max_age=60 * 60 * 24 * 30)
            username = data_tok.get('username')
        except (SignatureExpired, BadSignature):
            username = None
    if not username and current_user and current_user.is_authenticated:
        username = current_user.id
    if not username:
        return jsonify({'error': 'not authenticated'}), 401

    res = expenses_collection.delete_one({'_id': oid, 'user': username})
    if res.deleted_count == 0:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'message': 'deleted'}), 200


# ---------------- BUDGETS ---------------- #

budgets_collection = db['budgets']

@app.route('/api/budget', methods=['GET'])
@login_required
def get_budget():
    # auth
    auth = request.headers.get('Authorization', '')
    username = None
    if auth.startswith('Bearer '):
        tok = auth.split(' ', 1)[1]
        try:
            data_tok = serializer.loads(tok, max_age=60 * 60 * 24 * 30)
            username = data_tok.get('username')
        except (SignatureExpired, BadSignature):
            username = None
    if not username and current_user and current_user.is_authenticated:
        username = current_user.id
    if not username:
        return jsonify({'error': 'not authenticated'}), 401

    # default month = current month
    month = request.args.get('month') or datetime.utcnow().strftime('%Y-%m')
    doc = budgets_collection.find_one({'user': username, 'month': month})
    if not doc:
        return jsonify({'month': month, 'amount': 0.0}), 200
    return jsonify({'month': doc['month'], 'amount': doc['amount']}), 200


@app.route('/api/budget', methods=['POST'])
def set_budget():
    # auth
    auth = request.headers.get('Authorization', '')
    username = None
    if auth.startswith('Bearer '):
        tok = auth.split(' ', 1)[1]
        try:
            data_tok = serializer.loads(tok, max_age=60 * 60 * 24 * 30)
            username = data_tok.get('username')
        except (SignatureExpired, BadSignature):
            username = None
    if not username and current_user and current_user.is_authenticated:
        username = current_user.id
    if not username:
        return jsonify({'error': 'not authenticated'}), 401

    data = request.json or {}
    month = data.get('month') or datetime.utcnow().strftime('%Y-%m')
    try:
        amount = float(data.get('amount') or 0)
    except Exception:
        return jsonify({'error': 'invalid amount'}), 400

    budgets_collection.update_one({'user': username, 'month': month}, {'$set': {'amount': amount}}, upsert=True)
    return jsonify({'month': month, 'amount': amount}), 200


@app.route('/api/reports')
def api_reports():
    """Return CSV or (stub) PDF reports. Query params: type=expenses|summary, format=csv|pdf"""
    username = get_request_username()
    if not username:
        return jsonify({'error':'unauthorized'}), 401

    rtype = request.args.get('type', 'expenses')
    fmt = request.args.get('format', 'csv')

    if rtype == 'expenses':
        docs = list(expenses_collection.find({'user': username}).sort('date', -1))
        if fmt == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['id','date','amount','category','note'])
            for d in docs:
                writer.writerow([str(d.get('_id')), d.get('date'), d.get('amount'), d.get('category',''), d.get('note','')])
            csvdata = output.getvalue()
            output.close()
            resp = make_response(csvdata)
            resp.headers['Content-Type'] = 'text/csv'
            resp.headers['Content-Disposition'] = 'attachment; filename=expenses.csv'
            return resp
        else:
            return jsonify({'error':'pdf not implemented yet'}), 501

    elif rtype == 'summary':
        pipeline = [
            {'$match': {'user': username}},
            {'$project': {'amount': '$amount', 'year_month': {'$substr': ['$date', 0, 7]}}},
            {'$group': {'_id': '$year_month', 'total': {'$sum': '$amount'}}},
            {'$sort': {'_id': 1}}
        ]
        monthly = list(expenses_collection.aggregate(pipeline))
        if fmt == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['year_month','total'])
            for m in monthly:
                writer.writerow([m['_id'], m['total']])
            csvdata = output.getvalue()
            output.close()
            resp = make_response(csvdata)
            resp.headers['Content-Type'] = 'text/csv'
            resp.headers['Content-Disposition'] = 'attachment; filename=summary.csv'
            return resp
        else:
            return jsonify({'error':'pdf not implemented yet'}), 501
    else:
        return jsonify({'error':'unknown report type'}), 400


@app.route('/api/predict')
def api_predict():
    """Return a naive forecast for next month's total using simple linear regression on monthly totals."""
    username = get_request_username()
    if not username:
        return jsonify({'error':'unauthorized'}), 401

    pipeline = [
        {'$match': {'user': username}},
        {'$project': {'amount': '$amount', 'year_month': {'$substr': ['$date', 0, 7]}}},
        {'$group': {'_id': '$year_month', 'total': {'$sum': '$amount'}}},
        {'$sort': {'_id': 1}}
    ]
    monthly = list(expenses_collection.aggregate(pipeline))
    vals = [m['total'] for m in monthly]
    if len(vals) < 2:
        pred = vals[-1] if vals else 0.0
        return jsonify({'prediction': pred, 'method': 'fallback'}), 200

    n = len(vals)
    xs = list(range(n))
    ys = vals
    x_mean = sum(xs)/n
    y_mean = sum(ys)/n
    num = sum((xs[i]-x_mean)*(ys[i]-y_mean) for i in range(n))
    den = sum((xs[i]-x_mean)**2 for i in range(n))
    b = num/den if den != 0 else 0.0
    a = y_mean - b * x_mean
    next_x = n
    pred = a + b * next_x
    return jsonify({'prediction': float(pred), 'method': 'linear_regression', 'n_points': n}), 200




# ---------------- AUTH ROUTES ---------------- #

@app.route('/signup')
def signup_page():
    return render_template('signup.html')


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.json or {}

    username = data.get('username')   # can be email OR separate username
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'username, email and password required'}), 400

    # check duplicate username OR email
    if users_collection.find_one({
        '$or': [{'username': username}, {'email': email}]
    }):
        return jsonify({'error': 'user already exists'}), 409

    hashed = generate_password_hash(password)

    users_collection.insert_one({
        'username': username,
        'email': email,
        'password': hashed,
        'created_at': datetime.utcnow()
    })

    return jsonify({'message': 'signup successful'}), 201



@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or {}
    identifier = data.get('username')  # can be username OR email
    password = data.get('password')

    if not identifier or not password:
        return jsonify({'error': 'credentials required'}), 400

    # 🔍 search by username OR email
    user = users_collection.find_one({
        '$or': [
            {'username': identifier},
            {'email': identifier}
        ]
    })

    if not user:
        return jsonify({'error': 'invalid credentials'}), 401

    if not check_password_hash(user['password'], password):
        return jsonify({'error': 'invalid credentials'}), 401

    login_user(User(user['username'], user.get('email')))
    token = serializer.dumps({'username': user['username']})

    return jsonify({'message': 'login successful', 'token': token}), 200



@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


# ---------------- BUDGET GROUPS ---------------- #

groups_collection = db['groups']

@app.route('/budgeting')
def budgeting_page():
    return render_template('budgeting.html')

@app.route('/api/group', methods=['POST'])
def api_create_group():
    username = get_request_username()
    if not username:
        return jsonify({'error': 'not authenticated'}), 401
    data = request.json or {}
    name = data.get('name') or 'Untitled Group'
    try:
        budget = float(data.get('budget') or 0)
    except Exception:
        return jsonify({'error': 'invalid budget amount'}), 400
    doc = {
        'name': name,
        'budget': budget,
        'created_by': username,
        'members': [username],
        'created_at': datetime.utcnow().isoformat()
    }
    res = groups_collection.insert_one(doc)
    group_id = str(res.inserted_id)
    token = serializer.dumps({'group_id': group_id, 'inviter': username})
    invite_link = f"{request.host_url.rstrip('/')}/join-group/{token}"
    return jsonify({'group_id': group_id, 'invite_token': token, 'invite_link': invite_link}), 201

@app.route('/api/groups', methods=['GET'])
def api_list_groups():
    username = get_request_username()
    if not username:
        return jsonify({'error': 'not authenticated'}), 401
    docs = list(groups_collection.find({'members': username}))
    out = []
    for d in docs:
        out.append({
            'id': str(d.get('_id')),
            'name': d.get('name'),
            'budget': d.get('budget', 0),
            'members': d.get('members', [])
        })
    return jsonify(out), 200


@app.route('/api/group', methods=['GET'])
def api_list_groups_alias():
    """Alias kept for older frontend code that requests /api/group (singular)."""
    return api_list_groups()

@app.route('/api/group/<group_id>', methods=['GET'])
def api_get_group(group_id):
    username = get_request_username()
    if not username:
        return jsonify({'error': 'not authenticated'}), 401
    try:
        oid = ObjectId(group_id)
    except Exception:
        return jsonify({'error': 'invalid group id'}), 400
    group = groups_collection.find_one({'_id': oid})
    if not group:
        return jsonify({'error': 'group not found'}), 404
    if username not in group.get('members', []):
        return jsonify({'error': 'forbidden'}), 403
    # group expenses
    ex_docs = list(expenses_collection.find({'group_id': group_id}))
    expenses = []
    total = 0.0
    by_category = {}
    for e in ex_docs:
        amt = float(e.get('amount') or 0)
        total += amt
        cat = e.get('category') or 'Uncategorized'
        by_category[cat] = by_category.get(cat, 0) + amt
        expenses.append({
            'id': str(e.get('_id')),
            'amount': amt,
            'category': cat,
            'note': e.get('note'),
            'date': e.get('date'),
            'added_by': e.get('user')
        })
    by_category_list = [{'category': k, 'total': v} for k, v in by_category.items()]
    return jsonify({
        'id': group_id,
        'name': group.get('name'),
        'budget': group.get('budget', 0),
        'members': group.get('members', []),
        'total_spent': total,
        'by_category': by_category_list,
        'expenses': expenses
    }), 200


@app.route('/api/group/<group_id>/invite', methods=['GET'])
def api_group_invite(group_id):
    """Return a short-lived invite link (token) for a group. Caller must be a member."""
    username = get_request_username()
    if not username:
        return jsonify({'error': 'not authenticated'}), 401
    try:
        oid = ObjectId(group_id)
    except Exception:
        return jsonify({'error': 'invalid group id'}), 400
    group = groups_collection.find_one({'_id': oid})
    if not group:
        return jsonify({'error': 'group not found'}), 404
    if username not in group.get('members', []):
        return jsonify({'error': 'forbidden'}), 403
    token = serializer.dumps({'group_id': group_id, 'inviter': username})
    invite_link = f"{request.host_url.rstrip('/')}/join-group/{token}"
    return jsonify({'invite_link': invite_link, 'invite_token': token}), 200

@app.route('/api/group/<group_id>/expense', methods=['POST'])
def api_add_group_expense(group_id):
    username = get_request_username()
    if not username:
        return jsonify({'error': 'not authenticated'}), 401
    try:
        oid = ObjectId(group_id)
    except Exception:
        return jsonify({'error': 'invalid group id'}), 400
    group = groups_collection.find_one({'_id': oid})
    if not group:
        return jsonify({'error': 'group not found'}), 404
    if username not in group.get('members', []):
        return jsonify({'error': 'forbidden'}), 403
    data = request.json or {}
    try:
        amount = float(data.get('amount') or 0)
    except Exception:
        return jsonify({'error': 'invalid amount'}), 400
    expense = {
        'amount': amount,
        'category': data.get('category'),
        'note': data.get('note'),
        'date': data.get('date') or datetime.utcnow().strftime('%Y-%m-%d'),
        'user': username,
        'group_id': group_id
    }
    res = expenses_collection.insert_one(expense)
    return jsonify({'message': 'Expense added to group', 'id': str(res.inserted_id)}), 201

@app.route('/join-group/<token>')
def join_group(token):
    try:
        data = serializer.loads(token, max_age=60 * 60 * 24 * 30)
    except (SignatureExpired, BadSignature, Exception):
        return jsonify({'error': 'invalid or expired token'}), 400
    group_id = data.get('group_id')
    if not group_id:
        return jsonify({'error': 'invalid token payload'}), 400
    if not (current_user and current_user.is_authenticated):
        return redirect(url_for('login_page'))
    username = current_user.id
    try:
        oid = ObjectId(group_id)
    except Exception:
        return jsonify({'error': 'invalid group id'}), 400
    groups_collection.update_one({'_id': oid}, {'$addToSet': {'members': username}})
    return redirect(url_for('budgeting_page'))


if __name__ == "__main__":
    # Print diagnostic info at startup to help diagnose route registration issues
    import os
    print('Starting SpendWise app')
    print('cwd:', os.getcwd())
    try:
        print('Registered routes:')
        for r in app.url_map.iter_rules():
            print(' ', r.endpoint, r.rule)
    except Exception as _:
        print('Could not list url_map')
    # Disable the reloader on Windows to avoid transient socket errors when restarting
    app.run(debug=True, use_reloader=False)

