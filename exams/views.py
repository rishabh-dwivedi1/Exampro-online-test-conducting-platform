import json
from collections import defaultdict
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .models import Question, Result, UserResponse

EXAM_DURATION = 30 * 60
EXAM_SUBJECTS = ["Physics", "Chemistry", "Mathematics", "Computer Science"]
SUBJECT_OPTIONS = ["All Subjects", *EXAM_SUBJECTS]


def normalized_subject(subject):
    cleaned = subject.replace("-", " ").title()
    return cleaned if cleaned in SUBJECT_OPTIONS else "All Subjects"


def exam_title(subject):
    return "Complete Mock Test" if subject == "All Subjects" else f"{subject} Practice Test"


def get_exam_questions(subject):
    query = Question.objects.filter(subject__in=EXAM_SUBJECTS)
    if subject != "All Subjects":
        query = query.filter(subject=subject)
    return sorted(query, key=lambda q: (EXAM_SUBJECTS.index(q.subject), q.id))


def ensure_questions():
    rows = [
        ("Physics", "The SI unit of force is", "Joule", "Newton", "Watt", "Pascal", "B", "Mechanics"),
        ("Physics", "The dimensional formula of Planck's constant is", "ML2T-1", "MLT-2", "M2LT-1", "ML2T-2", "A", "Units and Dimensions"),
        ("Physics", "A body moving with uniform circular motion has", "Constant velocity", "Zero acceleration", "Changing speed", "Centripetal acceleration", "D", "Mechanics"),
        ("Physics", "Which law explains action and reaction forces?", "Newton's first law", "Newton's second law", "Newton's third law", "Hooke's law", "C", "Laws of Motion"),
        ("Physics", "The unit of electric current is", "Volt", "Ohm", "Ampere", "Coulomb", "C", "Electricity"),
        ("Physics", "In a convex lens, parallel rays after refraction meet at", "Pole", "Focus", "Centre of curvature", "Optical centre", "B", "Optics"),
        ("Physics", "The work done is zero when force and displacement are", "Parallel", "Opposite", "Perpendicular", "Equal", "C", "Work and Energy"),
        ("Physics", "Frequency is measured in", "Hertz", "Tesla", "Weber", "Farad", "A", "Waves"),
        ("Physics", "Ohm's law is represented by", "V = IR", "P = VI", "F = ma", "E = mc2", "A", "Electricity"),
        ("Physics", "The escape velocity from Earth depends on", "Mass of object only", "Radius and mass of Earth", "Temperature", "Air pressure", "B", "Gravitation"),
        ("Chemistry", "Atomic number is equal to the number of", "Neutrons", "Electrons only", "Protons", "Nucleons", "C", "Atomic Structure"),
        ("Chemistry", "The pH of a neutral solution at 25 C is", "0", "7", "10", "14", "B", "Acids and Bases"),
        ("Chemistry", "Which bond is formed by sharing electrons?", "Ionic bond", "Covalent bond", "Metallic bond", "Hydrogen bond", "B", "Chemical Bonding"),
        ("Chemistry", "Avogadro's number is approximately", "6.022 x 10^23", "9.8", "3.14", "1.6 x 10^-19", "A", "Mole Concept"),
        ("Chemistry", "The chemical formula of washing soda is", "NaHCO3", "Na2CO3.10H2O", "CaCO3", "NaCl", "B", "Salts"),
        ("Chemistry", "An exothermic reaction", "Absorbs heat", "Releases heat", "Stops instantly", "Needs no reactants", "B", "Thermochemistry"),
        ("Chemistry", "Which gas turns lime water milky?", "Oxygen", "Nitrogen", "Carbon dioxide", "Hydrogen", "C", "Chemical Reactions"),
        ("Chemistry", "The functional group in alcohols is", "-COOH", "-CHO", "-OH", "-NH2", "C", "Organic Chemistry"),
        ("Chemistry", "A catalyst changes the rate of reaction by changing", "Equilibrium constant", "Activation energy", "Molecular formula", "Atomic number", "B", "Chemical Kinetics"),
        ("Chemistry", "The most electronegative element is", "Fluorine", "Oxygen", "Chlorine", "Nitrogen", "A", "Periodic Table"),
        ("Mathematics", "Derivative of x squared is", "x", "2x", "x squared", "2", "B", "Calculus"),
        ("Mathematics", "The value of sin 90 degrees is", "0", "1", "1/2", "sqrt(3)/2", "B", "Trigonometry"),
        ("Mathematics", "If a matrix has order 2 x 3, it has how many elements?", "5", "6", "8", "9", "B", "Matrices"),
        ("Mathematics", "The sum of first n natural numbers is", "n2", "n(n+1)/2", "2n", "n(n-1)/2", "B", "Sequences"),
        ("Mathematics", "The distance between (0,0) and (3,4) is", "3", "4", "5", "7", "C", "Coordinate Geometry"),
        ("Mathematics", "The roots of x squared - 5x + 6 = 0 are", "1 and 6", "2 and 3", "-2 and -3", "0 and 5", "B", "Algebra"),
        ("Mathematics", "The probability of getting a head in one fair coin toss is", "0", "1/4", "1/2", "1", "C", "Probability"),
        ("Mathematics", "Integral of 1 with respect to x is", "0", "1", "x + C", "x squared", "C", "Calculus"),
        ("Mathematics", "The area of a circle is", "2 pi r", "pi r squared", "pi d", "r squared", "B", "Mensuration"),
        ("Mathematics", "The mean of 2, 4, 6, 8 is", "4", "5", "6", "8", "B", "Statistics"),
        ("Computer Science", "Which data structure follows FIFO order?", "Stack", "Queue", "Tree", "Graph", "B", "Data Structures"),
        ("Computer Science", "Time complexity of binary search is", "O(n)", "O(log n)", "O(n log n)", "O(1)", "B", "Algorithms"),
        ("Computer Science", "Which SQL clause filters grouped records?", "WHERE", "ORDER BY", "HAVING", "LIMIT", "C", "Databases"),
        ("Computer Science", "HTML stands for", "Hyper Text Markup Language", "High Text Machine Language", "Hyperlinks Text Mark Language", "Home Tool Markup Language", "A", "Web Basics"),
        ("Computer Science", "Which protocol is used for secure web browsing?", "FTP", "HTTP", "HTTPS", "SMTP", "C", "Networks"),
        ("Computer Science", "In Python, lists are", "Immutable", "Mutable", "Static only", "Compiled", "B", "Programming"),
        ("Computer Science", "Which normal form removes transitive dependency?", "1NF", "2NF", "3NF", "BCNF only", "C", "Databases"),
        ("Computer Science", "CSS Grid is mainly used for", "Two-dimensional layouts", "Database joins", "Server routing", "Password hashing", "A", "Web Basics"),
        ("Computer Science", "A primary key must be", "Null", "Duplicated", "Unique and not null", "Encrypted", "C", "Databases"),
        ("Computer Science", "Which sorting algorithm uses divide and conquer?", "Bubble sort", "Selection sort", "Merge sort", "Linear sort", "C", "Algorithms"),
    ]
    existing = set(Question.objects.filter(text__in=[row[1] for row in rows]).values_list("text", flat=True))
    Question.objects.bulk_create([
        Question(subject=subject, text=text, option_a=a, option_b=b, option_c=c, option_d=d, correct_answer=ans, topic=topic)
        for subject, text, a, b, c, d, ans, topic in rows
        if text not in existing
    ])


def auth_page(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    mode = request.GET.get("mode", "signup")
    if request.method == "POST":
        action = request.POST.get("action")
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        if action == "signup":
            name = request.POST.get("name", "").strip()
            try:
                user = User.objects.create_user(username=email, email=email, password=password, first_name=name)
                login(request, user)
                return redirect("dashboard")
            except IntegrityError:
                user = authenticate(request, username=email, password=password)
                if user:
                    login(request, user)
                    return redirect("dashboard")
                messages.error(request, "Account already exists. Please sign in with your password.")
                mode = "login"
        else:
            username = email
            try:
                username = User.objects.get(email=email).username
            except User.DoesNotExist:
                pass
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                return redirect("dashboard")
            messages.error(request, "Invalid email or password.")
            mode = "login"
    return render(request, "exams/login.html", {"mode": mode})


def logout_view(request):
    logout(request)
    return redirect("login")


@login_required
def dashboard_page(request):
    ensure_questions()
    attempts = Result.objects.filter(user=request.user).order_by("-submitted_at")
    total_attempts = attempts.count()
    best_score = max([r.score for r in attempts], default=0)
    best_accuracy = max([r.accuracy for r in attempts], default=0)
    avg_accuracy = round(sum(r.accuracy for r in attempts) / total_attempts, 2) if total_attempts else 0
    exam_cards = []
    for subject in SUBJECT_OPTIONS:
        count = Question.objects.filter(subject__in=EXAM_SUBJECTS).count() if subject == "All Subjects" else Question.objects.filter(subject=subject).count()
        exam_cards.append({
            "subject": subject,
            "slug": subject.lower().replace(" ", "-"),
            "title": exam_title(subject),
            "count": count,
        })
    return render(request, "exams/dashboard.html", {
        "attempts": attempts,
        "avg_accuracy": avg_accuracy,
        "best_accuracy": best_accuracy,
        "best_score": best_score,
        "duration": EXAM_DURATION // 60,
        "exam_cards": exam_cards,
        "total_attempts": total_attempts,
    })


@login_required
def start_exam(request, subject):
    ensure_questions()
    selected = normalized_subject(subject)
    request.session["exam_subject"] = selected
    request.session["exam_started_at"] = int(timezone.now().timestamp())
    return redirect("exam")


@login_required
def exam_page(request):
    ensure_questions()
    selected_subject = request.session.get("exam_subject")
    if not selected_subject:
        return redirect("dashboard")
    started = request.session.get("exam_started_at")
    now = int(timezone.now().timestamp())
    if not started:
        request.session["exam_started_at"] = now
        started = now
    remaining = max(0, EXAM_DURATION - (now - int(started)))
    questions = get_exam_questions(selected_subject)
    payload = [
        {
            "id": q.id,
            "subject": q.subject,
            "text": q.text,
            "topic": q.topic,
            "options": {"A": q.option_a, "B": q.option_b, "C": q.option_c, "D": q.option_d},
        }
        for q in questions
    ]
    return render(request, "exams/exam.html", {
        "questions": questions,
        "questions_json": payload,
        "remaining": remaining,
        "subject": exam_title(selected_subject),
        "subjects": EXAM_SUBJECTS,
    })


@login_required
def download_paper(request):
    ensure_questions()
    selected_subject = request.session.get("exam_subject", "All Subjects")
    questions = get_exam_questions(selected_subject)
    lines = [
        "ExamPro Online - Computer Based Test Paper",
        f"Exam: {exam_title(selected_subject)}",
        f"Total Questions: {len(questions)}",
        f"Duration: {EXAM_DURATION // 60} minutes",
        "",
    ]
    for index, q in enumerate(questions, start=1):
        lines.extend([
            f"Q{index}. [{q.subject} - {q.topic}] {q.text}",
            f"  A. {q.option_a}",
            f"  B. {q.option_b}",
            f"  C. {q.option_c}",
            f"  D. {q.option_d}",
            "",
        ])
    response = HttpResponse("\n".join(lines), content_type="text/plain")
    filename = exam_title(selected_subject).lower().replace(" ", "_")
    response["Content-Disposition"] = f'attachment; filename="{filename}_question_paper.txt"'
    return response


@login_required
@transaction.atomic
def submit_exam(request):
    ensure_questions()
    selected_subject = request.session.get("exam_subject")
    if not selected_subject:
        return redirect("dashboard")
    started = int(request.session.get("exam_started_at", int(timezone.now().timestamp())))
    elapsed = min(EXAM_DURATION, max(0, int(timezone.now().timestamp()) - started))
    try:
        data = json.loads(request.POST.get("responses", "{}"))
    except json.JSONDecodeError:
        data = {}
    questions = get_exam_questions(selected_subject)
    attempted = correct = incorrect = 0
    result = Result.objects.create(
        user=request.user,
        subject=selected_subject,
        title=exam_title(selected_subject),
        total_questions=len(questions),
        attempted=0,
        correct=0,
        incorrect=0,
        score=0,
        time_taken=elapsed,
    )
    for q in questions:
        item = data.get(str(q.id), {})
        selected_answer = item.get("answer", "")
        marked = bool(item.get("marked", False))
        is_correct = selected_answer == q.correct_answer
        if selected_answer:
            attempted += 1
            correct += int(is_correct)
            incorrect += int(not is_correct)
        UserResponse.objects.create(
            user=request.user,
            question=q,
            selected_answer=selected_answer,
            is_correct=is_correct,
            marked_for_review=marked,
            result=result,
        )
    result.attempted = attempted
    result.correct = correct
    result.incorrect = incorrect
    result.score = correct
    result.accuracy = round((correct / attempted) * 100, 2) if attempted else 0
    result.save()
    request.session.pop("exam_started_at", None)
    request.session.pop("exam_subject", None)
    return redirect("result_detail", result_id=result.id)


@login_required
def result_page(request, result_id=None):
    if result_id:
        result = get_object_or_404(Result, id=result_id, user=request.user)
    else:
        result = Result.objects.filter(user=request.user).order_by("-submitted_at").first()
        if not result:
            return redirect("dashboard")
    responses = UserResponse.objects.filter(result=result).select_related("question").order_by("question_id")
    topic_stats = defaultdict(lambda: {"total": 0, "correct": 0, "percent": 0})
    for r in responses:
        s = topic_stats[f"{r.question.subject} - {r.question.topic}"]
        s["total"] += 1
        s["correct"] += int(r.is_correct)
    topics = []
    for name, s in topic_stats.items():
        s["percent"] = round((s["correct"] / s["total"]) * 100) if s["total"] else 0
        topics.append({"name": name, **s})
    time_text = f"{result.time_taken // 60:02d}:{result.time_taken % 60:02d}"
    unattempted = result.total_questions - result.attempted
    return render(request, "exams/result.html", {
        "result": result,
        "responses": responses,
        "topics": topics,
        "time_text": time_text,
        "unattempted": unattempted,
        "attempts": Result.objects.filter(user=request.user).order_by("-submitted_at")[:5],
    })
