from pathlib import Path
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session

from csv_service import read_csv, append_csv, write_csv
from auth_service import AuthService
from email_service import EmailService


app = Flask(__name__)
app.secret_key = "health-booking-ultra-secret"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

USERS_FILE = DATA_DIR / "users.csv"
CLINICS_FILE = DATA_DIR / "clinics.csv"
DOCTORS_FILE = DATA_DIR / "doctors.csv"
PATIENTS_FILE = DATA_DIR / "patients.csv"
APPOINTMENTS_FILE = DATA_DIR / "appointments.csv"

TIME_FORMAT = "%Y-%m-%d %H:%M"

PATIENT_FIELDS = ["patient_id", "patient_name", "patient_email", "phone", "home_address", "user_id"]

APPOINTMENT_FIELDS = [
    "appointment_id",
    "patient_id",
    "user_id",
    "patient_name",
    "patient_email",
    "phone",
    "home_address",
    "doctor_id",
    "clinic_id",
    "appointment_time",
    "symptom",
    "status"
]

auth_service = AuthService(USERS_FILE)


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Vui lòng đăng nhập trước.", "warning")
            return redirect(url_for("login"))
        return func(*args, **kwargs)
    return wrapper


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Vui lòng đăng nhập trước.", "warning")
            return redirect(url_for("login"))

        if session.get("role") != "Admin":
            flash("Bạn không có quyền truy cập trang Admin.", "danger")
            return redirect(url_for("index"))

        return func(*args, **kwargs)
    return wrapper


def get_next_id(rows, id_field):
    ids = []

    for row in rows:
        value = row.get(id_field, "").strip()
        if value.isdigit():
            ids.append(int(value))

    return max(ids) + 1 if ids else 1


def find_nearest_clinic():
    clinics = read_csv(CLINICS_FILE)

    if not clinics:
        return None

    # Khoảng cách giả lập: chọn phòng khám có distance_km nhỏ nhất.
    return min(clinics, key=lambda c: float(c["distance_km"]))


def find_clinic_by_id(clinic_id):
    for clinic in read_csv(CLINICS_FILE):
        if clinic["clinic_id"] == str(clinic_id):
            return clinic
    return None


def find_doctor_by_id(doctor_id):
    for doctor in read_csv(DOCTORS_FILE):
        if doctor["doctor_id"] == str(doctor_id):
            return doctor
    return None


def find_doctor_by_symptom(symptom, preferred_clinic_id):
    doctors = read_csv(DOCTORS_FILE)
    symptom = symptom.lower().strip()

    matched_preferred = []
    matched_other = []

    for doctor in doctors:
        keyword = doctor["symptom_keyword"].lower().strip()
        specialty = doctor["specialty"].lower().strip()

        if keyword in symptom or symptom in keyword or specialty in symptom or symptom in specialty:
            if doctor["clinic_id"] == str(preferred_clinic_id):
                matched_preferred.append(doctor)
            else:
                matched_other.append(doctor)

    if matched_preferred:
        return matched_preferred[0]

    if matched_other:
        return matched_other[0]

    return None


def is_conflict(doctor_id, appointment_time):
    appointments = read_csv(APPOINTMENTS_FILE)

    for item in appointments:
        if (
            item["doctor_id"] == str(doctor_id)
            and item["appointment_time"] == appointment_time
            and item["status"] != "Canceled"
        ):
            return True

    return False


def suggest_available_time(doctor_id, appointment_time):
    new_time = datetime.strptime(appointment_time, TIME_FORMAT)

    while True:
        new_time += timedelta(minutes=30)
        new_time_text = new_time.strftime(TIME_FORMAT)

        if not is_conflict(doctor_id, new_time_text):
            return new_time_text


def create_patient(patient_name, patient_email, phone, home_address, user_id):
    patients = read_csv(PATIENTS_FILE)

    new_patient = {
        "patient_id": get_next_id(patients, "patient_id"),
        "patient_name": patient_name,
        "patient_email": patient_email,
        "phone": phone,
        "home_address": home_address,
        "user_id": user_id
    }

    append_csv(PATIENTS_FILE, PATIENT_FIELDS, new_patient)
    return new_patient


def get_appointment_view_rows():
    result = []

    for item in read_csv(APPOINTMENTS_FILE):
        doctor = find_doctor_by_id(item["doctor_id"])
        clinic = find_clinic_by_id(item["clinic_id"])

        result.append({
            **item,
            "doctor_name": doctor["doctor_name"] if doctor else "Không rõ",
            "specialty": doctor["specialty"] if doctor else "Không rõ",
            "doctor_image": doctor.get("image", "") if doctor else "",
            "clinic_name": clinic["clinic_name"] if clinic else "Không rõ",
            "clinic_address": clinic["address"] if clinic else "Không rõ",
            "clinic_image": clinic.get("image", "") if clinic else "",
            "distance_km": clinic["distance_km"] if clinic else "0"
        })

    return result


def get_my_appointments():
    if session.get("role") == "Admin":
        return get_appointment_view_rows()

    user_id = str(session.get("user_id"))

    return [
        item for item in get_appointment_view_rows()
        if item.get("user_id") == user_id or item.get("patient_email") == session.get("email")
    ]


@app.context_processor
def inject_user():
    return {
        "current_user": {
            "user_id": session.get("user_id"),
            "username": session.get("username"),
            "role": session.get("role"),
            "email": session.get("email"),
            "full_name": session.get("full_name")
        }
    }


@app.route("/")
def index():
    clinics = read_csv(CLINICS_FILE)
    doctors = read_csv(DOCTORS_FILE)
    patients = read_csv(PATIENTS_FILE)
    appointments = read_csv(APPOINTMENTS_FILE)

    booked = [a for a in appointments if a.get("status") == "Booked"]
    canceled = [a for a in appointments if a.get("status") == "Canceled"]

    if session.get("role") == "Admin":
        recent = get_appointment_view_rows()[-6:]
    elif session.get("user_id"):
        recent = get_my_appointments()[-6:]
    else:
        recent = []

    recent.reverse()

    return render_template(
        "index.html",
        clinic_count=len(clinics),
        doctor_count=len(doctors),
        patient_count=len(patients),
        appointment_count=len(booked),
        canceled_count=len(canceled),
        recent=recent
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    user = auth_service.login(username, password)

    if not user:
        flash("Sai tên đăng nhập hoặc mật khẩu.", "danger")
        return redirect(url_for("login"))

    session["user_id"] = int(user["user_id"])
    session["username"] = user["username"]
    session["role"] = user["role"]
    session["email"] = user["email"]
    session["full_name"] = user["full_name"]
    session["phone"] = user.get("phone", "")
    session["address"] = user.get("address", "")

    flash(f"Đăng nhập thành công. Xin chào {user['full_name']}!", "success")
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()
    email = request.form.get("email", "").strip()
    full_name = request.form.get("full_name", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()

    if not all([username, password, email, full_name, phone, address]):
        flash("Vui lòng nhập đầy đủ thông tin.", "danger")
        return redirect(url_for("register"))

    if "@" not in email or "." not in email:
        flash("Email không hợp lệ.", "danger")
        return redirect(url_for("register"))

    ok, message = auth_service.register_patient(username, password, email, full_name, phone, address)

    if ok:
        flash(message + " Bạn có thể đăng nhập.", "success")
        return redirect(url_for("login"))

    flash(message, "danger")
    return redirect(url_for("register"))


@app.route("/logout")
def logout():
    session.clear()
    flash("Đã đăng xuất.", "success")
    return redirect(url_for("index"))


@app.route("/clinics")
def clinics():
    keyword = request.args.get("q", "").lower().strip()
    rows = read_csv(CLINICS_FILE)

    if keyword:
        rows = [
            c for c in rows
            if keyword in c["clinic_name"].lower()
            or keyword in c["address"].lower()
            or keyword in c["district"].lower()
        ]

    rows = sorted(rows, key=lambda c: float(c["distance_km"]))
    return render_template("clinics.html", clinics=rows, q=keyword)


@app.route("/doctors")
def doctors():
    keyword = request.args.get("q", "").lower().strip()
    rows = read_csv(DOCTORS_FILE)
    clinics_data = read_csv(CLINICS_FILE)
    clinic_map = {c["clinic_id"]: c for c in clinics_data}

    if keyword:
        rows = [
            d for d in rows
            if keyword in d["doctor_name"].lower()
            or keyword in d["specialty"].lower()
            or keyword in d["symptom_keyword"].lower()
        ]

    return render_template("doctors.html", doctors=rows, clinic_map=clinic_map, q=keyword)


@app.route("/book", methods=["GET", "POST"])
@login_required
def book():
    if request.method == "GET":
        return render_template(
            "book.html",
            default_name=session.get("full_name", ""),
            default_email=session.get("email", ""),
            default_phone=session.get("phone", ""),
            default_address=session.get("address", "")
        )

    patient_name = request.form.get("patient_name", "").strip()
    patient_email = request.form.get("patient_email", "").strip()
    phone = request.form.get("phone", "").strip()
    home_address = request.form.get("home_address", "").strip()
    symptom = request.form.get("symptom", "").strip()
    appointment_time_raw = request.form.get("appointment_time", "").strip()

    if not all([patient_name, patient_email, phone, home_address, symptom, appointment_time_raw]):
        flash("Vui lòng nhập đầy đủ thông tin.", "danger")
        return redirect(url_for("book"))

    if "@" not in patient_email or "." not in patient_email:
        flash("Email không hợp lệ.", "danger")
        return redirect(url_for("book"))

    try:
        appointment_time = datetime.strptime(appointment_time_raw, "%Y-%m-%dT%H:%M").strftime(TIME_FORMAT)
    except ValueError:
        flash("Thời gian không hợp lệ.", "danger")
        return redirect(url_for("book"))

    nearest_clinic = find_nearest_clinic()

    if not nearest_clinic:
        flash("Không tìm thấy phòng khám.", "danger")
        return redirect(url_for("book"))

    doctor = find_doctor_by_symptom(symptom, nearest_clinic["clinic_id"])

    if not doctor:
        flash("Không tìm thấy bác sĩ phù hợp. Hãy thử: sốt, đau họng, đau lưng, đau bụng, đau đầu, đau răng...", "warning")
        return redirect(url_for("book"))

    doctor_clinic = find_clinic_by_id(doctor["clinic_id"])

    final_time = appointment_time
    suggested = None

    if is_conflict(doctor["doctor_id"], appointment_time):
        final_time = suggest_available_time(doctor["doctor_id"], appointment_time)
        suggested = final_time
        flash(f"Lịch {appointment_time} bị trùng. Hệ thống đã tự động đề xuất và đặt sang {final_time}.", "warning")

    user_id = str(session.get("user_id"))
    patient = create_patient(patient_name, patient_email, phone, home_address, user_id)

    appointments = read_csv(APPOINTMENTS_FILE)

    new_appointment = {
        "appointment_id": get_next_id(appointments, "appointment_id"),
        "patient_id": patient["patient_id"],
        "user_id": user_id,
        "patient_name": patient_name,
        "patient_email": patient_email,
        "phone": phone,
        "home_address": home_address,
        "doctor_id": doctor["doctor_id"],
        "clinic_id": doctor["clinic_id"],
        "appointment_time": final_time,
        "symptom": symptom,
        "status": "Booked"
    }

    append_csv(APPOINTMENTS_FILE, APPOINTMENT_FIELDS, new_appointment)

    email_success, email_message = EmailService().send_reminder(
        patient_email=patient_email,
        patient_name=patient_name,
        doctor_name=doctor["doctor_name"],
        clinic_name=doctor_clinic["clinic_name"] if doctor_clinic else "Không rõ",
        appointment_time=final_time
    )

    flash("Đặt lịch thành công.", "success")
    flash(email_message, "success" if email_success else "warning")

    return render_template(
        "success.html",
        appointment=new_appointment,
        doctor=doctor,
        clinic=doctor_clinic,
        nearest_clinic=nearest_clinic,
        email_message=email_message,
        suggested=suggested
    )


@app.route("/appointments")
@login_required
def appointments():
    keyword = request.args.get("q", "").lower().strip()
    status = request.args.get("status", "").strip()

    rows = get_my_appointments()

    if keyword:
        rows = [
            a for a in rows
            if keyword in a["patient_name"].lower()
            or keyword in a["patient_email"].lower()
            or keyword in a["doctor_name"].lower()
            or keyword in a["clinic_name"].lower()
            or keyword in a["symptom"].lower()
        ]

    if status:
        rows = [a for a in rows if a["status"] == status]

    rows.reverse()
    return render_template("appointments.html", appointments=rows, q=keyword, status=status)


@app.route("/appointment/<appointment_id>")
@login_required
def appointment_detail(appointment_id):
    rows = get_my_appointments()

    appointment = None
    for row in rows:
        if row["appointment_id"] == str(appointment_id):
            appointment = row
            break

    if not appointment:
        flash("Không tìm thấy lịch hẹn hoặc bạn không có quyền xem.", "danger")
        return redirect(url_for("appointments"))

    return render_template("appointment_detail.html", appointment=appointment)


@app.route("/cancel/<appointment_id>", methods=["POST"])
@login_required
def cancel(appointment_id):
    allowed = get_my_appointments()
    allowed_ids = [str(a["appointment_id"]) for a in allowed]

    if str(appointment_id) not in allowed_ids:
        flash("Bạn không có quyền hủy lịch này.", "danger")
        return redirect(url_for("appointments"))

    rows = read_csv(APPOINTMENTS_FILE)
    found = False

    for row in rows:
        if row["appointment_id"] == str(appointment_id):
            row["status"] = "Canceled"
            found = True

    if found:
        write_csv(APPOINTMENTS_FILE, APPOINTMENT_FIELDS, rows)
        flash("Hủy lịch thành công.", "success")
    else:
        flash("Không tìm thấy lịch hẹn.", "danger")

    return redirect(url_for("appointments"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    users = auth_service.get_all_users()
    clinics_data = read_csv(CLINICS_FILE)
    doctors_data = read_csv(DOCTORS_FILE)
    patients_data = read_csv(PATIENTS_FILE)
    appointments_data = get_appointment_view_rows()

    booked = [a for a in appointments_data if a["status"] == "Booked"]
    canceled = [a for a in appointments_data if a["status"] == "Canceled"]

    recent = appointments_data[-10:]
    recent.reverse()

    return render_template(
        "admin_dashboard.html",
        user_count=len(users),
        clinic_count=len(clinics_data),
        doctor_count=len(doctors_data),
        patient_count=len(patients_data),
        booked_count=len(booked),
        canceled_count=len(canceled),
        recent=recent
    )


@app.route("/admin/users")
@admin_required
def admin_users():
    return render_template("admin_users.html", users=auth_service.get_all_users())


@app.route("/admin/patients")
@admin_required
def admin_patients():
    patients = read_csv(PATIENTS_FILE)
    patients.reverse()
    return render_template("admin_patients.html", patients=patients)


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
